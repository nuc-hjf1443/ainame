import uuid
from datetime import datetime
from decimal import Decimal

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.alipay_service import AlipayClient, AlipayError, AlipayTradeResult
from services.order_expiry import expire_order_if_unpaid, expire_pending_orders, order_payment_deadline
from models.finance import Order, PackageConfig, RefundAudit
from models.marketplace import ExpertServiceOrder, ExpertServicePackage
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

    async def list_user_orders(self, user_id: int, page: int, page_size: int):
        await expire_pending_orders(self.session)
        total = await self.session.scalar(
            select(func.count()).select_from(Order).where(Order.user_id == user_id)
        ) or 0
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_time.desc(), Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        orders = result.scalars().all()
        return [await self._user_order_payload(order) for order in orders], total

    async def prepare_user_alipay_order(self, order_id: int, user_id: int) -> Order | None:
        order = await self.session.scalar(
            select(Order).where(Order.id == order_id, Order.user_id == user_id).with_for_update()
        )
        if order and await expire_order_if_unpaid(self.session, order):
            return None
        if not order or order.status != "PENDING":
            return None

        service = await self.session.scalar(
            select(ExpertServiceOrder).where(
                ExpertServiceOrder.finance_order_id == order.id,
                ExpertServiceOrder.customer_id == user_id,
            ).with_for_update()
        )
        if service:
            if service.status != "PENDING_PAYMENT":
                return None
            order.order_type = "EXPERT_SERVICE"
            order.payment_subject = order.payment_subject or "启名星专家服务"
        elif order.package_id:
            order.order_type = "MEMBERSHIP"
            order.payment_subject = order.payment_subject or "启名星会员充值"
        else:
            return None

        order.payment_provider = "ALIPAY_SANDBOX"
        order.out_trade_no = order.out_trade_no or self._new_out_trade_no(order.id)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def _user_order_payload(self, order: Order) -> dict[str, Any]:
        package = await self.session.get(PackageConfig, order.package_id) if order.package_id else None
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id)
        )
        service_package = await self.session.get(ExpertServicePackage, service.package_id) if service else None
        return {
            "id": order.id,
            "amount": order.amount,
            "status": order.status,
            "order_type": order.order_type,
            "payment_provider": order.payment_provider,
            "payment_subject": order.payment_subject,
            "package_name": package.name if package else None,
            "out_trade_no": order.out_trade_no,
            "provider_trade_no": order.provider_trade_no,
            "paid_time": order.paid_time,
            "created_time": order.created_time,
            "updated_time": order.updated_time,
            "payment_deadline": order_payment_deadline(order) if order.status == "PENDING" else None,
            "service_order_id": service.id if service else None,
            "service_status": service.status if service else None,
            "service_package_name": service_package.name if service_package else None,
        }

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
        if order.status not in {"PENDING", "CANCELLED"}:
            return None
        if order.order_type == "MEMBERSHIP" or order.package_id:
            paid_order, _ = await MembershipRepository(self.session).complete_order_payment(
                order,
                payment_provider="ALIPAY_SANDBOX",
                provider_trade_no=result.trade_no,
                allow_cancelled=True,
            )
            return paid_order
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id).with_for_update()
        )
        if not service or service.status not in {"PENDING_PAYMENT", "CANCELLED"}:
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
