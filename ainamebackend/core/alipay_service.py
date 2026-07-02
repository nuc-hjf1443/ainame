import base64
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

import settings
from models.finance import Order


class AlipayError(Exception):
    pass


@dataclass
class AlipayTradeResult:
    out_trade_no: str
    trade_no: str | None
    total_amount: Decimal
    trade_status: str

    @property
    def paid(self) -> bool:
        return self.trade_status in {"TRADE_SUCCESS", "TRADE_FINISHED"}


def _decimal_amount(value: Decimal | str) -> str:
    return format(Decimal(value).quantize(Decimal("0.01")), "f")


class AlipayClient:
    def __init__(self):
        self.gateway_url = settings.ALIPAY_GATEWAY_URL
        self.app_id = settings.ALIPAY_APP_ID
        self.sign_type = settings.ALIPAY_SIGN_TYPE or "RSA2"

    def ensure_enabled(self) -> None:
        if not settings.ALIPAY_ENABLED:
            raise AlipayError("支付宝沙箱支付未启用")
        if not self.app_id:
            raise AlipayError("缺少 ALIPAY_APP_ID")
        if not settings.ALIPAY_APP_PRIVATE_KEY_PATH or not Path(settings.ALIPAY_APP_PRIVATE_KEY_PATH).is_file():
            raise AlipayError("缺少支付宝应用私钥文件")
        if not settings.ALIPAY_PUBLIC_KEY_PATH or not Path(settings.ALIPAY_PUBLIC_KEY_PATH).is_file():
            raise AlipayError("缺少支付宝公钥文件")

    def build_pay_url(self, order: Order) -> str:
        self.ensure_enabled()
        if not order.out_trade_no:
            raise AlipayError("订单缺少 out_trade_no")
        if not order.payment_subject:
            raise AlipayError("订单缺少支付标题")
        method, product_code = self._pay_method_and_product()
        biz_content = {
            "out_trade_no": order.out_trade_no,
            "total_amount": _decimal_amount(order.amount),
            "subject": order.payment_subject,
            "product_code": product_code,
        }
        params = self._base_params(method)
        params.update(
            notify_url=settings.ALIPAY_NOTIFY_URL,
            return_url=settings.ALIPAY_RETURN_URL,
            biz_content=json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
        )
        params["sign"] = self.sign(params)
        return f"{self.gateway_url}?{urlencode(params)}"

    def build_wap_pay_url(self, order: Order) -> str:
        return self.build_pay_url(order)

    async def query_trade(self, out_trade_no: str) -> AlipayTradeResult:
        response = await self._request(
            "alipay.trade.query",
            {"out_trade_no": out_trade_no},
        )
        return AlipayTradeResult(
            out_trade_no=response.get("out_trade_no") or out_trade_no,
            trade_no=response.get("trade_no"),
            total_amount=Decimal(str(response.get("total_amount") or "0")),
            trade_status=response.get("trade_status") or "",
        )

    async def refund_trade(self, order: Order) -> dict[str, Any]:
        self.ensure_enabled()
        if not order.out_trade_no:
            raise AlipayError("订单缺少 out_trade_no")
        if not order.refund_request_no:
            raise AlipayError("订单缺少退款请求号")
        response = await self._request(
            "alipay.trade.refund",
            {
                "out_trade_no": order.out_trade_no,
                "refund_amount": _decimal_amount(order.amount),
                "out_request_no": order.refund_request_no,
            },
        )
        return response

    async def _request(self, method: str, biz_content: dict[str, Any]) -> dict[str, Any]:
        self.ensure_enabled()
        params = self._base_params(method)
        params["biz_content"] = json.dumps(biz_content, ensure_ascii=False, separators=(",", ":"))
        params["sign"] = self.sign(params)
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.gateway_url, data=params)
            response.raise_for_status()
        data = response.json()
        response_key = f"{method.replace('.', '_')}_response"
        payload = data.get(response_key) or {}
        if payload.get("code") != "10000":
            message = payload.get("sub_msg") or payload.get("msg") or "支付宝接口调用失败"
            raise AlipayError(message)
        return payload

    def sign(self, params: dict[str, Any]) -> str:
        unsigned = self._unsigned_string(params)
        private_key = self._load_private_key()
        signature = private_key.sign(
            unsigned.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify(self, params: dict[str, Any]) -> bool:
        signature = params.get("sign")
        if not signature:
            return False
        try:
            public_key = self._load_public_key()
            public_key.verify(
                base64.b64decode(signature),
                self._unsigned_string(params).encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    def _base_params(self, method: str) -> dict[str, str]:
        return {
            "app_id": self.app_id,
            "method": method,
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": self.sign_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
        }

    def _pay_method_and_product(self) -> tuple[str, str]:
        pay_method = (settings.ALIPAY_PAY_METHOD or "page").strip().lower()
        if pay_method == "wap":
            return "alipay.trade.wap.pay", "QUICK_WAP_WAY"
        if pay_method == "page":
            return "alipay.trade.page.pay", "FAST_INSTANT_TRADE_PAY"
        raise AlipayError("ALIPAY_PAY_METHOD 仅支持 page 或 wap")

    def _unsigned_string(self, params: dict[str, Any]) -> str:
        items = []
        for key in sorted(params):
            if key == "sign":
                continue
            value = params[key]
            if value is None or value == "":
                continue
            items.append(f"{key}={value}")
        return "&".join(items)

    def _load_private_key(self):
        raw = Path(settings.ALIPAY_APP_PRIVATE_KEY_PATH).read_text(encoding="utf-8").strip()
        candidates = [raw] if raw.startswith("-----BEGIN") else [
            self._wrap_key(raw, "PRIVATE KEY"),
            self._wrap_key(raw, "RSA PRIVATE KEY"),
        ]
        last_error: Exception | None = None
        for content in candidates:
            try:
                return serialization.load_pem_private_key(content.encode("utf-8"), password=None)
            except ValueError as exc:
                last_error = exc
        raise ValueError("支付宝应用私钥格式不正确，请确认使用的是应用私钥而不是应用公钥或支付宝公钥") from last_error

    def _load_public_key(self):
        content = self._read_key(settings.ALIPAY_PUBLIC_KEY_PATH, "PUBLIC KEY")
        return serialization.load_pem_public_key(content.encode("utf-8"))

    def _read_key(self, file_path: str, label: str) -> str:
        raw = Path(file_path).read_text(encoding="utf-8").strip()
        if raw.startswith("-----BEGIN"):
            return raw
        return self._wrap_key(raw, label)

    def _wrap_key(self, raw: str, label: str) -> str:
        chunks = "\n".join(raw[i:i + 64] for i in range(0, len(raw), 64))
        return f"-----BEGIN {label}-----\n{chunks}\n-----END {label}-----\n"
