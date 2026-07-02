from datetime import datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from core.alipay_service import AlipayClient, AlipayError, AlipayTradeResult
from models.asset import NamingAsset
from models.finance import Order, PackageConfig, UserQuotaBalance
from models.marketplace import ExpertProfile, ExpertServicePackage
from models.user import User
from repository.admin_repo import AdminRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.membership_repo import MembershipRepository
from repository.payment_repo import PaymentRepository


def configure_alipay(monkeypatch, tmp_path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_path = tmp_path / "app_private.pem"
    public_path = tmp_path / "alipay_public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    import settings

    monkeypatch.setattr(settings, "ALIPAY_ENABLED", True)
    monkeypatch.setattr(settings, "ALIPAY_APP_ID", "2021000118650000")
    monkeypatch.setattr(settings, "ALIPAY_GATEWAY_URL", "https://openapi-sandbox.dl.alipaydev.com/gateway.do")
    monkeypatch.setattr(settings, "ALIPAY_APP_PRIVATE_KEY_PATH", str(private_path))
    monkeypatch.setattr(settings, "ALIPAY_PUBLIC_KEY_PATH", str(public_path))
    monkeypatch.setattr(settings, "ALIPAY_NOTIFY_URL", "https://api.test/payments/alipay/notify")
    monkeypatch.setattr(settings, "ALIPAY_RETURN_URL", "https://api.test/payments/alipay/return")
    monkeypatch.setattr(settings, "ALIPAY_PAY_METHOD", "page")
    return AlipayClient()


async def create_user(session, suffix: str):
    user = User(email=f"{suffix}@test.local", username=suffix, password="test")
    session.add(user)
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_alipay_wap_payment_url_is_signed(session, monkeypatch, tmp_path):
    client = configure_alipay(monkeypatch, tmp_path)
    user = await create_user(session, "alipay-url")
    package = PackageConfig(
        package_code="QUOTA_NAMING_30",
        name="30 次起名包",
        price=Decimal("9.90"),
        api_quota=30,
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()
    order = await MembershipRepository(session).create_order(user.id, package.id)
    order = await PaymentRepository(session, client).prepare_membership_alipay_order(order.id, user.id)

    payment_url = client.build_wap_pay_url(order)
    params = {key: values[0] for key, values in parse_qs(urlparse(payment_url).query).items()}

    assert params["app_id"] == "2021000118650000"
    assert params["method"] == "alipay.trade.page.pay"
    assert params["notify_url"] == "https://api.test/payments/alipay/notify"
    assert order.out_trade_no in params["biz_content"]
    assert "9.90" in params["biz_content"]
    assert "FAST_INSTANT_TRADE_PAY" in params["biz_content"]
    assert client.verify(params)
    params["biz_content"] = params["biz_content"].replace("9.90", "0.01")
    assert not client.verify(params)


@pytest.mark.asyncio
async def test_alipay_wap_mode_uses_wap_method(session, monkeypatch, tmp_path):
    client = configure_alipay(monkeypatch, tmp_path)
    import settings

    monkeypatch.setattr(settings, "ALIPAY_PAY_METHOD", "wap")
    user = await create_user(session, "alipay-wap")
    order = Order(
        user_id=user.id,
        amount=Decimal("1.00"),
        status="PENDING",
        order_type="MEMBERSHIP",
        payment_provider="ALIPAY_SANDBOX",
        out_trade_no="AN_TEST_WAP",
        payment_subject="测试支付",
    )
    session.add(order)
    await session.commit()

    params = {key: values[0] for key, values in parse_qs(urlparse(client.build_pay_url(order)).query).items()}

    assert params["method"] == "alipay.trade.wap.pay"
    assert "QUICK_WAP_WAY" in params["biz_content"]
    assert client.verify(params)


@pytest.mark.asyncio
async def test_alipay_membership_completion_is_idempotent(session):
    user = await create_user(session, "alipay-balance")
    package = PackageConfig(
        package_code="QUOTA_NAMING_30",
        name="30 次起名包",
        price=Decimal("9.90"),
        api_quota=30,
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()
    order = Order(
        user_id=user.id,
        package_id=package.id,
        amount=Decimal("9.90"),
        status="PENDING",
        order_type="MEMBERSHIP",
        payment_provider="ALIPAY_SANDBOX",
        out_trade_no="AN_TEST_BALANCE",
    )
    session.add(order)
    await session.commit()
    result = AlipayTradeResult("AN_TEST_BALANCE", "TRADE_NO_1", Decimal("9.90"), "TRADE_SUCCESS")

    await PaymentRepository(session).complete_alipay_payment(result)
    await PaymentRepository(session).complete_alipay_payment(result)

    balance = await MembershipRepository(session).get_quota_balance(user.id)
    await session.refresh(order)
    assert balance.naming_balance == 30
    assert order.status == "PAID"
    assert order.provider_trade_no == "TRADE_NO_1"


@pytest.mark.asyncio
async def test_alipay_completion_rejects_amount_mismatch(session):
    user = await create_user(session, "alipay-mismatch")
    order = Order(
        user_id=user.id,
        amount=Decimal("19.90"),
        status="PENDING",
        order_type="MEMBERSHIP",
        payment_provider="ALIPAY_SANDBOX",
        out_trade_no="AN_TEST_MISMATCH",
    )
    session.add(order)
    await session.commit()

    with pytest.raises(AlipayError):
        await PaymentRepository(session).complete_alipay_payment(
            AlipayTradeResult("AN_TEST_MISMATCH", "TRADE_NO_2", Decimal("0.01"), "TRADE_SUCCESS")
        )


@pytest.mark.asyncio
async def test_alipay_expert_payment_and_refund(session):
    customer = await create_user(session, "alipay-customer")
    expert_user = await create_user(session, "alipay-expert")
    asset = NamingAsset(user_id=customer.id, thread_id="thread", name="启明", category="企业名")
    expert = ExpertProfile(
        user_id=expert_user.id,
        display_name="品牌专家",
        expert_type="BRAND_CONSULTANT",
        bio="具备长期品牌咨询和企业命名项目服务经验。",
        credentials="品牌咨询与企业命名相关完整项目资历。",
        years_experience=8,
        status="APPROVED",
    )
    package = ExpertServicePackage(
        name="品牌精批",
        expert_type="BRAND_CONSULTANT",
        price=Decimal("200.00"),
        delivery_days=3,
        description="结构化品牌分析",
        status="ACTIVE",
    )
    session.add_all([asset, expert, package])
    await session.commit()
    service = await MarketplaceRepository(session).create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "naming_asset_id": asset.id,
        "requirements": "重点评估品牌传播优势",
    })
    finance = await session.get(Order, service.finance_order_id)
    finance.payment_provider = "ALIPAY_SANDBOX"
    finance.out_trade_no = "AN_TEST_EXPERT"
    await session.commit()

    await PaymentRepository(session).complete_alipay_payment(
        AlipayTradeResult("AN_TEST_EXPERT", "TRADE_NO_3", Decimal("200.00"), "TRADE_SUCCESS")
    )
    payload = await MarketplaceRepository(session).order_payload(service)
    assert payload["status"] == "WAITING_ACCEPT"
    assert payload["payment_status"] == "PAID"

    class FakeAlipay:
        async def refund_trade(self, order):
            return {"code": "10000", "gmt_refund_pay": datetime.now().isoformat()}

    assert await PaymentRepository(session, FakeAlipay()).refund_expert_alipay_order(service.id, customer.id, "CUSTOMER")
    payload = await MarketplaceRepository(session).order_payload(service)
    assert payload["status"] == "CANCELLED"
    assert payload["payment_status"] == "REFUNDED"


@pytest.mark.asyncio
async def test_alipay_expert_refund_request_waits_for_admin_approval(session):
    customer = await create_user(session, "approval-customer")
    expert_user = await create_user(session, "approval-expert")
    asset = NamingAsset(user_id=customer.id, thread_id="thread", name="启明", category="企业名")
    expert = ExpertProfile(
        user_id=expert_user.id,
        display_name="品牌专家",
        expert_type="BRAND_CONSULTANT",
        bio="具备长期品牌咨询和企业命名项目服务经验。",
        credentials="品牌咨询与企业命名相关完整项目资历。",
        years_experience=8,
        status="APPROVED",
    )
    package = ExpertServicePackage(
        name="品牌精批",
        expert_type="BRAND_CONSULTANT",
        price=Decimal("200.00"),
        delivery_days=3,
        description="结构化品牌分析",
        status="ACTIVE",
    )
    session.add_all([asset, expert, package])
    await session.commit()
    service = await MarketplaceRepository(session).create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "naming_asset_id": asset.id,
        "requirements": "重点评估品牌传播优势",
    })
    finance = await session.get(Order, service.finance_order_id)
    finance.payment_provider = "ALIPAY_SANDBOX"
    finance.out_trade_no = "AN_TEST_APPROVAL_REFUND"
    finance.provider_trade_no = "TRADE_NO_APPROVAL"
    finance.status = "PAID"
    service.status = "WAITING_ACCEPT"
    await session.commit()

    refund = await PaymentRepository(session).request_expert_alipay_refund(
        service.id,
        customer.id,
        "CUSTOMER",
        "用户取消",
    )
    await session.refresh(service)
    await session.refresh(finance)
    assert refund is not None
    assert refund.status == "PENDING"
    assert service.status == "REFUND_PENDING"
    assert finance.status == "PAID"

    class FakeAlipay:
        async def refund_trade(self, order):
            assert order.refund_request_no
            return {"code": "10000", "gmt_refund_pay": datetime.now().isoformat()}

    reviewed = await AdminRepository(session, FakeAlipay()).review_refund(refund.id, "APPROVED", "同意退款")
    await session.refresh(service)
    await session.refresh(finance)
    assert reviewed.status == "APPROVED"
    assert finance.status == "REFUNDED"
    assert service.status == "CANCELLED"


@pytest.mark.asyncio
async def test_alipay_refund_failure_keeps_order_state(session):
    customer = await create_user(session, "refund-fail-customer")
    expert_user = await create_user(session, "refund-fail-expert")
    asset = NamingAsset(user_id=customer.id, thread_id="thread", name="远航", category="企业名")
    expert = ExpertProfile(
        user_id=expert_user.id,
        display_name="品牌专家",
        expert_type="BRAND_CONSULTANT",
        bio="具备长期品牌咨询和企业命名项目服务经验。",
        credentials="品牌咨询与企业命名相关完整项目资历。",
        years_experience=8,
        status="APPROVED",
    )
    package = ExpertServicePackage(
        name="品牌精批",
        expert_type="BRAND_CONSULTANT",
        price=Decimal("100.00"),
        delivery_days=3,
        description="结构化品牌分析",
        status="ACTIVE",
    )
    session.add_all([asset, expert, package])
    await session.commit()
    service = await MarketplaceRepository(session).create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "naming_asset_id": asset.id,
        "requirements": "重点评估品牌传播优势",
    })
    finance = await session.get(Order, service.finance_order_id)
    finance.payment_provider = "ALIPAY_SANDBOX"
    finance.out_trade_no = "AN_TEST_REFUND_FAIL"
    finance.status = "PAID"
    service.status = "WAITING_ACCEPT"
    await session.commit()

    class FailingAlipay:
        async def refund_trade(self, order):
            raise AlipayError("refund failed")

    with pytest.raises(AlipayError):
        await PaymentRepository(session, FailingAlipay()).refund_expert_alipay_order(service.id, customer.id, "CUSTOMER")

    await session.refresh(finance)
    await session.refresh(service)
    assert finance.status == "PAID"
    assert service.status == "WAITING_ACCEPT"
