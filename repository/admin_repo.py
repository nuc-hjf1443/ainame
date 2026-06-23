from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.ai_asset import AgentConfig, KnowledgeBase
from models.audit import SensitiveWordInterception
from models.finance import Order, RefundAudit
from models.user import User
from models.finance import UserMembership
from models.marketplace import ExpertProfile


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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

    async def list_orders(self, page: int, page_size: int):
        stmt = select(Order).order_by(Order.created_time.desc(), Order.id.desc())
        return await self._paginate(stmt, page, page_size)

    async def review_refund(self, refund_id: int, status: str, review_note: str | None):
        refund = await self.session.get(RefundAudit, refund_id)
        if not refund:
            return None
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
