from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.finance import DailyQuotaUsage, PackageConfig, UserQuotaBalance
from models.user import User
from models.visual import BrandKit, BrandVisual
from repository.membership_repo import MembershipRepository


FREE_NAMING_TOTAL_QUOTA = 5
FREE_VISUAL_TOTAL_QUOTA = 0
SHANGHAI = ZoneInfo("Asia/Shanghai")


def current_usage_date():
    return datetime.now(SHANGHAI).date()


def current_month_range():
    today = current_usage_date()
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    return date(today.year, today.month, 1), next_month


async def _usage_sum(session: AsyncSession, user_id: int, field, start: date | None = None, end: date | None = None) -> int:
    conditions = [DailyQuotaUsage.user_id == user_id]
    if start:
        conditions.append(DailyQuotaUsage.usage_date >= start)
    if end:
        conditions.append(DailyQuotaUsage.usage_date < end)
    value = await session.scalar(select(func.coalesce(func.sum(field), 0)).where(*conditions))
    return int(value or 0)


async def quota_snapshot(session: AsyncSession, user_id: int):
    repository = MembershipRepository(session)
    membership = await repository.get_active_membership(user_id)
    package = await session.get(PackageConfig, membership.package_id) if membership else None
    balance = await repository.get_quota_balance(user_id)
    if package:
        month_start, next_month = current_month_range()
        naming_used = await _usage_sum(session, user_id, DailyQuotaUsage.naming_used, month_start, next_month)
        visual_used = await _usage_sum(session, user_id, DailyQuotaUsage.visual_used, month_start, next_month)
        naming_limit = package.naming_daily_quota
        visual_limit = package.visual_daily_quota
        quota_period = "MONTHLY"
    else:
        naming_used = await _usage_sum(session, user_id, DailyQuotaUsage.naming_used)
        visual_used = await _usage_sum(session, user_id, DailyQuotaUsage.visual_used)
        naming_limit = FREE_NAMING_TOTAL_QUOTA
        visual_limit = FREE_VISUAL_TOTAL_QUOTA
        quota_period = "TOTAL"
    return {
        "is_vip": bool(membership),
        "membership": membership,
        "package": package,
        "quota_period": quota_period,
        "naming_balance": balance.naming_balance if balance else 0,
        "naming_used": naming_used,
        "naming_limit": naming_limit,
        "visual_used": visual_used,
        "visual_limit": visual_limit,
    }


async def reserve_quota(session: AsyncSession, user_id: int, feature: str):
    await session.scalar(select(User).where(User.id == user_id).with_for_update())
    snapshot = await quota_snapshot(session, user_id)
    usage_date = current_usage_date()
    usage = await session.scalar(
        select(DailyQuotaUsage).where(
            DailyQuotaUsage.user_id == user_id,
            DailyQuotaUsage.usage_date == usage_date,
        ).with_for_update()
    )
    if not usage:
        usage = DailyQuotaUsage(user_id=user_id, usage_date=usage_date)
        session.add(usage)
        await session.flush()
    used_field = "naming_used" if feature == "NAMING" else "visual_used"
    limit = snapshot["naming_limit"] if feature == "NAMING" else snapshot["visual_limit"]
    used = snapshot["naming_used"] if feature == "NAMING" else snapshot["visual_used"]
    if used >= limit:
        if feature == "NAMING":
            balance = await session.scalar(
                select(UserQuotaBalance).where(UserQuotaBalance.user_id == user_id).with_for_update()
            )
            if balance and balance.naming_balance > 0:
                balance.naming_balance -= 1
                await session.commit()
                return {"source": "BALANCE"}
        await session.rollback()
        label = "智能起名" if feature == "NAMING" else "品牌生成"
        period = "本月" if snapshot["quota_period"] == "MONTHLY" else "账号"
        action = "请购买起名次数包或升级 VIP" if feature == "NAMING" else "请升级或续费 VIP"
        raise HTTPException(429, detail=f"{period}{label}额度已用完（{used}/{limit}），{action}")
    setattr(usage, used_field, getattr(usage, used_field) + 1)
    await session.commit()
    return usage_date


async def refund_quota(
        session: AsyncSession,
        user_id: int,
        feature: str,
        usage_date: date | dict | None = None,
):
    if isinstance(usage_date, dict) and usage_date.get("source") == "BALANCE":
        balance = await session.scalar(
            select(UserQuotaBalance).where(UserQuotaBalance.user_id == user_id).with_for_update()
        )
        if balance:
            balance.naming_balance += 1
            await session.commit()
        return
    usage = await session.scalar(
        select(DailyQuotaUsage).where(
            DailyQuotaUsage.user_id == user_id,
            DailyQuotaUsage.usage_date == (usage_date or current_usage_date()),
        ).with_for_update()
    )
    if usage:
        field = "naming_used" if feature == "NAMING" else "visual_used"
        setattr(usage, field, max(0, getattr(usage, field) - 1))
        await session.commit()


async def refund_visual_quota_once(session: AsyncSession, visual_id: int, user_id: int):
    visual = await session.scalar(
        select(BrandVisual).where(
            BrandVisual.id == visual_id,
            BrandVisual.user_id == user_id,
        ).with_for_update()
    )
    if not visual or visual.brand_kit_id is not None or visual.quota_refunded:
        return False
    await _refund_locked(session, user_id, visual)
    return True


async def refund_brand_kit_quota_once(session: AsyncSession, kit_id: int, user_id: int):
    kit = await session.scalar(
        select(BrandKit).where(
            BrandKit.id == kit_id,
            BrandKit.user_id == user_id,
        ).with_for_update()
    )
    if not kit or kit.quota_refunded:
        return False
    await _refund_locked(session, user_id, kit)
    return True


async def _refund_locked(session: AsyncSession, user_id: int, record):
    usage_date = record.quota_usage_date or current_usage_date()
    usage = await session.scalar(
        select(DailyQuotaUsage).where(
            DailyQuotaUsage.user_id == user_id,
            DailyQuotaUsage.usage_date == usage_date,
        ).with_for_update()
    )
    if usage:
        usage.visual_used = max(0, usage.visual_used - 1)
    record.quota_refunded = True
    await session.commit()
