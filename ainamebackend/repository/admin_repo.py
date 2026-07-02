import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.alipay_service import AlipayClient
from core.order_expiry import expire_pending_orders
from models.ai_asset import AgentConfig, KnowledgeBase
from models.audit import SensitiveWordInterception
from models.finance import Order, PackageConfig, RefundAudit
from models.user import User
from models.finance import UserMembership
from models.marketplace import ExpertProfile, ExpertServiceOrder, ExpertServicePackage


class AdminRepository:
    def __init__(self, session: AsyncSession, alipay_client: AlipayClient | None = None):
        self.session = session
        self.alipay_client = alipay_client or AlipayClient()

    async def _paginate(self, stmt: Select[Any], page: int, page_size: int):
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total or 0

    async def list_users(self, page: int, page_size: int, keyword: str | None = None):
        stmt = select(User)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            stmt = stmt.where(or_(User.username.like(pattern), User.email.like(pattern)))
        users, total = await self._paginate(stmt.order_by(User.id.desc()), page, page_size)
        now = datetime.now()
        for user in users:
            membership = await self.session.scalar(select(UserMembership).where(UserMembership.user_id == user.id, UserMembership.status == "ACTIVE", UserMembership.end_time > now))
            expert = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
            user.is_vip = bool(membership)
            user.vip_expires_at = membership.end_time if membership else None
            user.expert_status = expert.status if expert else None
        return users, total

    async def toggle_user_ban(self, user_id: int):
        user = await self.session.get(User, user_id)
        if not user or user.is_deleted:
            return None
        user.is_banned = not user.is_banned
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def reset_user_password(self, user_id: int, password: str):
        user = await self.session.get(User, user_id)
        if not user or user.is_deleted:
            return None
        user.password = password
        await self.session.commit()
        return user

    async def soft_delete_user(self, user_id: int):
        user = await self.session.get(User, user_id)
        if not user:
            return None
        user.is_deleted = True
        user.is_banned = True
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def _latest_refund(self, order_id: int):
        return await self.session.scalar(
            select(RefundAudit)
            .where(RefundAudit.order_id == order_id)
            .order_by(RefundAudit.id.desc())
            .limit(1)
        )

    async def _order_payload(self, order: Order) -> dict[str, Any]:
        package = await self.session.get(PackageConfig, order.package_id) if order.package_id else None
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id)
        )
        expert = await self.session.get(ExpertProfile, service.expert_id) if service else None
        service_package = await self.session.get(ExpertServicePackage, service.package_id) if service else None
        refund = await self._latest_refund(order.id)
        return {
            "id": order.id,
            "user_id": order.user_id,
            "package_id": order.package_id,
            "package_name": package.name if package else None,
            "amount": order.amount,
            "status": order.status,
            "order_type": order.order_type,
            "payment_provider": order.payment_provider,
            "payment_subject": order.payment_subject,
            "out_trade_no": order.out_trade_no,
            "provider_trade_no": order.provider_trade_no,
            "refund_request_no": order.refund_request_no,
            "refunded_time": order.refunded_time,
            "paid_time": order.paid_time,
            "created_time": order.created_time,
            "updated_time": order.updated_time,
            "service_order_id": service.id if service else None,
            "service_status": service.status if service else None,
            "expert_id": service.expert_id if service else None,
            "expert_name": expert.display_name if expert else None,
            "service_package_id": service.package_id if service else None,
            "service_package_name": service_package.name if service_package else None,
            "refund_id": refund.id if refund else None,
            "refund_status": refund.status if refund else None,
        }

    async def list_orders(
            self,
            page: int,
            page_size: int,
            status: str | None = None,
            order_type: str | None = None,
            payment_provider: str | None = None,
            keyword: str | None = None,
    ):
        await expire_pending_orders(self.session)
        conditions = []
        if status:
            conditions.append(Order.status == status)
        if order_type:
            conditions.append(Order.order_type == order_type)
        if payment_provider:
            conditions.append(Order.payment_provider == payment_provider)
        if keyword:
            stripped = keyword.strip()
            pattern = f"%{stripped}%"
            keyword_conditions = [
                Order.out_trade_no.like(pattern),
                Order.provider_trade_no.like(pattern),
                Order.payment_subject.like(pattern),
                User.username.like(pattern),
                User.email.like(pattern),
            ]
            if stripped.isdigit():
                keyword_id = int(stripped)
                keyword_conditions.extend([Order.id == keyword_id, Order.user_id == keyword_id])
            conditions.append(or_(*keyword_conditions))
        stmt = select(Order).join(User, User.id == Order.user_id).where(*conditions).order_by(
            Order.created_time.desc(),
            Order.id.desc(),
        )
        orders, total = await self._paginate(stmt, page, page_size)
        return [await self._order_payload(order) for order in orders], total

    async def _refund_payload(self, refund: RefundAudit) -> dict[str, Any]:
        order = await self.session.get(Order, refund.order_id)
        payload = {
            "id": refund.id,
            "order_id": refund.order_id,
            "reason": refund.reason,
            "status": refund.status,
            "review_note": refund.review_note,
            "reviewed_time": refund.reviewed_time,
            "created_time": refund.created_time,
            "updated_time": refund.updated_time,
        }
        if order:
            payload.update(
                order_amount=order.amount,
                order_status=order.status,
                order_type=order.order_type,
                payment_provider=order.payment_provider,
                out_trade_no=order.out_trade_no,
                user_id=order.user_id,
            )
            service = await self.session.scalar(
                select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id)
            )
            payload.update(
                service_order_id=service.id if service else None,
                service_status=service.status if service else None,
            )
        return payload

    async def list_refunds(self, page: int, page_size: int, status: str | None = None):
        conditions = []
        if status:
            conditions.append(RefundAudit.status == status)
        stmt = select(RefundAudit).where(*conditions).order_by(RefundAudit.created_time.desc(), RefundAudit.id.desc())
        refunds, total = await self._paginate(stmt, page, page_size)
        return [await self._refund_payload(refund) for refund in refunds], total

    async def review_refund(self, refund_id: int, status: str, review_note: str | None):
        refund = await self.session.scalar(
            select(RefundAudit).where(RefundAudit.id == refund_id).with_for_update()
        )
        if not refund:
            return None
        if refund.status != "PENDING":
            return refund
        order = await self.session.scalar(
            select(Order).where(Order.id == refund.order_id).with_for_update()
        )
        if not order:
            return None
        service = await self.session.scalar(
            select(ExpertServiceOrder).where(ExpertServiceOrder.finance_order_id == order.id).with_for_update()
        )
        if status == "APPROVED":
            if order.status != "PAID":
                return None
            order.refund_request_no = order.refund_request_no or (
                f"RF{order.id}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
            )
            if order.payment_provider == "ALIPAY_SANDBOX":
                await self.session.commit()
                await self.alipay_client.refund_trade(order)
            order.status = "REFUNDED"
            order.refunded_time = datetime.now()
            if service:
                service.status = "CANCELLED"
        elif service and service.status == "REFUND_PENDING":
            service.status = "WAITING_ACCEPT"
        refund.status = status
        refund.review_note = review_note
        refund.reviewed_time = datetime.now()
        await self.session.commit()
        await self.session.refresh(refund)
        return refund

    async def list_agents(self):
        result = await self.session.execute(select(AgentConfig).order_by(AgentConfig.id.desc()))
        return result.scalars().all()

    async def update_agent(self, agent_id: int, values: dict[str, Any]):
        agent = await self.session.get(AgentConfig, agent_id)
        if not agent:
            return None
        for key, value in values.items():
            if value is not None:
                setattr(agent, key, value)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def upsert_knowledge(self, values: dict[str, Any]):
        knowledge_id = values.pop("knowledge_id", None)
        if knowledge_id:
            knowledge = await self.session.get(KnowledgeBase, knowledge_id)
            if not knowledge:
                return None
            for key, value in values.items():
                setattr(knowledge, key, value)
        else:
            knowledge = KnowledgeBase(**values)
            self.session.add(knowledge)
        await self.session.commit()
        await self.session.refresh(knowledge)
        return knowledge

    async def list_sensitive_logs(self, page: int, page_size: int):
        stmt = select(SensitiveWordInterception).order_by(
            SensitiveWordInterception.created_time.desc(),
            SensitiveWordInterception.id.desc(),
        )
        return await self._paginate(stmt, page, page_size)
