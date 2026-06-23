from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.finance import DailyQuotaUsage, Order, PackageConfig, UserMembership
from models.user import User


class MembershipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_packages(self):
        result = await self.session.execute(
            select(PackageConfig).where(
                PackageConfig.package_code.in_(["VIP_MONTHLY", "VIP_YEARLY"]),
                PackageConfig.status == "ACTIVE",
            ).order_by(PackageConfig.duration_days)
        )
        return result.scalars().all()

    async def get_active_membership(self, user_id: int, now: datetime | None = None):
        now = now or datetime.now()
        return await self.session.scalar(
            select(UserMembership).where(
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE",
                UserMembership.end_time > now,
            )
        )

    async def get_active_package(self, user_id: int, now: datetime | None = None):
        membership = await self.get_active_membership(user_id, now)
        return await self.session.get(PackageConfig, membership.package_id) if membership else None

    async def get_usage(self, user_id: int, usage_date: date):
        return await self.session.scalar(
            select(DailyQuotaUsage).where(
                DailyQuotaUsage.user_id == user_id,
                DailyQuotaUsage.usage_date == usage_date,
            )
        )

    async def create_order(self, user_id: int, package_id: int):
        package = await self.session.scalar(
            select(PackageConfig).where(
                PackageConfig.id == package_id,
                PackageConfig.package_code.in_(["VIP_MONTHLY", "VIP_YEARLY"]),
                PackageConfig.status == "ACTIVE",
            )
        )
        if not package:
            return None
        order = Order(user_id=user_id, package_id=package.id, amount=package.price, status="PENDING")
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def pay_order(self, order_id: int, user_id: int):
        order = await self.session.scalar(
            select(Order).where(Order.id == order_id, Order.user_id == user_id).with_for_update()
        )
        if not order or not order.package_id:
            return None, None
        package = await self.session.get(PackageConfig, order.package_id)
        if not package or package.package_code not in {"VIP_MONTHLY", "VIP_YEARLY"}:
            return None, None
        membership = await self.session.scalar(
            select(UserMembership).where(UserMembership.user_id == user_id).with_for_update()
        )
        if order.status == "PAID":
            return order, membership
        if order.status != "PENDING":
            return None, None
        now = datetime.now()
        base = membership.end_time if membership and membership.status == "ACTIVE" and membership.end_time > now else now
        if membership:
            if membership.end_time <= now:
                membership.start_time = now
            membership.package_id = package.id
            membership.end_time = base + timedelta(days=package.duration_days)
            membership.status = "ACTIVE"
        else:
            membership = UserMembership(
                user_id=user_id, package_id=package.id, start_time=now,
                end_time=base + timedelta(days=package.duration_days), status="ACTIVE",
            )
            self.session.add(membership)
        order.status = "PAID"
        order.paid_time = now
        await self.session.commit()
        await self.session.refresh(membership)
        return order, membership

    async def gift_monthly_vip(self, user_id: int):
        user = await self.session.get(User, user_id)
        if not user or user.is_deleted:
            return None
        package = await self.session.scalar(select(PackageConfig).where(PackageConfig.package_code == "VIP_MONTHLY"))
        if not package:
            return None
        membership = await self.session.scalar(
            select(UserMembership).where(UserMembership.user_id == user_id).with_for_update()
        )
        now = datetime.now()
        base = membership.end_time if membership and membership.status == "ACTIVE" and membership.end_time > now else now
        if membership:
            membership.package_id = package.id
            membership.start_time = membership.start_time if membership.end_time > now else now
            membership.end_time = base + timedelta(days=30)
            membership.status = "ACTIVE"
        else:
            membership = UserMembership(user_id=user_id, package_id=package.id, start_time=now, end_time=base + timedelta(days=30))
            self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(membership)
        return membership

    async def expert_discount(self, user_id: int) -> Decimal:
        package = await self.get_active_package(user_id)
        return package.expert_discount if package else Decimal("1.00")
