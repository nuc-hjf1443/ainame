import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.alipay_service import AlipayClient, AlipayError, AlipayTradeResult
from core.order_expiry import expire_order_if_unpaid
from models.finance import Order, RefundAudit
from models.marketplace import ExpertServiceOrder
from repository.membership_repo import MembershipRepository


class PaymentRepository:
    def __init__(self, session: AsyncSession, alipay_client: AlipayClient | None = None):
        self.session = session
        self.alipay_client = alipay_client or AlipayClient()

    async def prepare_membership_alipay_order(self, order_id: int, user_id: int) -> Order | None:
        order = await self.session.scalar(
            select(Order).where(Order.id == order_id, Order.user_id == user_id).with_for_update()
        )
        if order and await expire_order_if_unpaid(self.session, order):
            return None
        if not order or not order.package_id or order.status != "PENDING":
            return None
        order.order_type = "MEMBERSHIP"
        order.payment_provider = "ALIPAY_SANDBOX"
        order.out_trade_no = order.out_trade_no or self._new_out_trade_no(order.id)
        order.payment_subject = order.payment_subject or "启名星会员充值"
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def prepare_expert_alipay_order(self, service_order_id: int, user_id: int) -> tuple[ExpertServiceOrder, Order] | None:
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(
                ExpertServiceOrder.id == service_order_id,
                ExpertServiceOrder.customer_id == user_id,
            ).with_for_update()
        )
        if not service or service.status != "PENDING_PAYMENT":
            return None
        order = await self.session.scalar(
            select(Order).where(Order.id == service.finance_order_id).with_for_update()
        )
        if order and await expire_order_if_unpaid(self.session, order):
            return None
        if not order or order.status != "PENDING":
            return None
        order.order_type = "EXPERT_SERVICE"
        order.payment_provider = "ALIPAY_SANDBOX"
        order.out_trade_no = order.out_trade_no or self._new_out_trade_no(order.id)
        order.payment_subject = order.payment_subject or "启名星专家服务"
        await self.session.commit()
        await self.session.refresh(service)
        await self.session.refresh(order)
        return service, order

    async def get_user_order_by_out_trade_no(self, out_trade_no: str, user_id: int) -> Order | None:
        return await self.session.scalar(
            select(Order).where(Order.out_trade_no == out_trade_no, Order.user_id == user_id)
        )

    async def complete_alipay_payment(
            self,
            result: AlipayTradeResult,
    ) -> Order | None:
        order = await self.session.scalar(
            select(Order).where(Order.out_trade_no == result.out_trade_no).with_for_update()
        )
        if not order or order.payment_provider != "ALIPAY_SANDBOX":
            return None
        if not result.paid:
            return order
        expected = Decimal(order.amount).quantize(Decimal("0.01"))
        actual = Decimal(result.total_amount).quantize(Decimal("0.01"))
        if expected != actual:
            raise AlipayError("支付宝支付金额与本地订单金额不一致")
        if order.status == "PAID":
            if result.trade_no and not order.provider_trade_no:
                order.provider_trade_no = result.trade_no
                await self.session.commit()
            return order
        if order.status != "PENDING":
            return None
        if order.order_type == "MEMBERSHIP" or order.package_id:
            paid_order, _ = await MembershipRepository(self.session).complete_order_payment(
                order,
                payment_provider="ALIPAY_SANDBOX",
                provider_trade_no=result.trade_no,
            )
            return paid_order
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id).with_for_update()
        )
        if not service or service.status != "PENDING_PAYMENT":
            return None
        order.order_type = "EXPERT_SERVICE"
        order.provider_trade_no = result.trade_no
        order.status = "PAID"
        order.paid_time = datetime.now()
        service.status = "WAITING_ACCEPT"
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def sync_alipay_order(self, out_trade_no: str) -> Order | None:
        result = await self.alipay_client.query_trade(out_trade_no)
        return await self.complete_alipay_payment(result)

    async def refund_expert_alipay_order(
            self,
            service_order_id: int,
            actor_id: int,
            actor_role: str,
            reason: str | None = None,
    ) -> bool:
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.id == service_order_id).with_for_update()
        )
        if not service or service.status != "WAITING_ACCEPT":
            return False
        if actor_role == "CUSTOMER" and service.customer_id != actor_id:
            return False
        if actor_role == "EXPERT" and service.expert_id != actor_id:
            return False
        order = await self.session.scalar(
            select(Order).where(Order.id == service.finance_order_id).with_for_update()
        )
        if not order or order.status != "PAID" or order.payment_provider != "ALIPAY_SANDBOX":
            return False
        order.refund_request_no = order.refund_request_no or f"RF{order.id}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
        await self.session.commit()
        await self.alipay_client.refund_trade(order)
        order.status = "REFUNDED"
        order.refunded_time = datetime.now()
        service.status = "CANCELLED"
        if reason:
            service.rejection_reason = reason
        await self.session.commit()
        return True

    async def request_expert_alipay_refund(
            self,
            service_order_id: int,
            actor_id: int,
            actor_role: str,
            reason: str | None = None,
    ) -> RefundAudit | None:
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.id == service_order_id).with_for_update()
        )
        if not service or service.status not in {"WAITING_ACCEPT", "REFUND_PENDING"}:
            return None
        if actor_role == "CUSTOMER" and service.customer_id != actor_id:
            return None
        if actor_role == "EXPERT" and service.expert_id != actor_id:
            return None
        order = await self.session.scalar(
            select(Order).where(Order.id == service.finance_order_id).with_for_update()
        )
        if not order or order.status != "PAID" or order.payment_provider != "ALIPAY_SANDBOX":
            return None
        existing = await self.session.scalar(
            select(RefundAudit)
            .where(RefundAudit.order_id == order.id, RefundAudit.status == "PENDING")
            .order_by(RefundAudit.id.desc())
            .limit(1)
        )
        service.status = "REFUND_PENDING"
        if reason:
            service.rejection_reason = reason
        if existing:
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        refund = RefundAudit(
            order_id=order.id,
            reason=reason or "专家服务订单取消退款",
            status="PENDING",
        )
        self.session.add(refund)
        await self.session.commit()
        await self.session.refresh(refund)
        return refund

    def _new_out_trade_no(self, order_id: int) -> str:
        return f"AN{order_id}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
