from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND, HTTP_502_BAD_GATEWAY

import settings
from services.alipay_service import AlipayClient, AlipayError, AlipayTradeResult
from dependencies import get_current_user, get_session
from models.user import User
from repository.payment_repo import PaymentRepository
from schemas.payment_schemas import PaymentSyncOut


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/alipay/notify", response_class=PlainTextResponse)
async def alipay_notify(request: Request, session: AsyncSession = Depends(get_session)):
    data = {key: str(value) for key, value in (await request.form()).items()}
    client = AlipayClient()
    try:
        if data.get("app_id") != settings.ALIPAY_APP_ID or not client.verify(data):
            return "failure"
        result = AlipayTradeResult(
            out_trade_no=data.get("out_trade_no", ""),
            trade_no=data.get("trade_no"),
            total_amount=Decimal(data.get("total_amount") or "0"),
            trade_status=data.get("trade_status") or "",
        )
        if result.paid:
            await PaymentRepository(session, client).complete_alipay_payment(result)
        return "success"
    except Exception:
        return "failure"


@router.get("/alipay/return")
async def alipay_return(request: Request):
    data = {key: str(value) for key, value in request.query_params.items()}
    out_trade_no = data.get("out_trade_no") or ""
    status = "success" if data.get("app_id") == settings.ALIPAY_APP_ID and AlipayClient().verify(data) else "invalid"
    url = f"{settings.FRONTEND_BASE_URL}/#/pages/payment/result?out_trade_no={out_trade_no}&status={status}"
    return RedirectResponse(url)


@router.post("/alipay/orders/{out_trade_no}/sync", response_model=PaymentSyncOut)
async def sync_alipay_order(
        out_trade_no: str,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = PaymentRepository(session)
    order = await repository.get_user_order_by_out_trade_no(out_trade_no, user.id)
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="支付订单不存在")
    if order.status != "PAID":
        try:
            order = await repository.sync_alipay_order(out_trade_no)
        except AlipayError as exc:
            raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=409, detail="支付订单状态无法同步")
    return {
        "out_trade_no": out_trade_no,
        "status": order.status,
        "order_type": order.order_type,
        "order_id": order.id,
    }
