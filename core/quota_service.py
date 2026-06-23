from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.finance import DailyQuotaUsage, PackageConfig
from models.user import User
from models.visual import BrandKit, BrandVisual
from repository.membership_repo import MembershipRepository


FREE_NAMING_DAILY_QUOTA = 5
FREE_VISUAL_DAILY_QUOTA = 0
SHANGHAI = ZoneInfo("Asia/Shanghai")


def current_usage_date():
    return datetime.now(SHANGHAI).date()


async def quota_snapshot(session: AsyncSession, user_id: int):
    repository = MembershipRepository(session)
    membership = await repository.get_active_membership(user_id)
    package = await session.get(PackageConfig, membership.package_id) if membership else None
    usage = await repository.get_usage(user_id, current_usage_date())
    naming_limit = package.naming_daily_quota if package else FREE_NAMING_DAILY_QUOTA
    visual_limit = package.visual_daily_quota if package else FREE_VISUAL_DAILY_QUOTA
    return {
        "is_vip": bool(membership),
        "membership": membership,
        "package": package,
        "naming_used": usage.naming_used if usage else 0,
        "naming_limit": naming_limit,
        "visual_used": usage.visual_used if usage else 0,
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
    used = getattr(usage, used_field)
    if used >= limit:
        await session.rollback()
        label = "智能起名" if feature == "NAMING" else "视觉生成"
        raise HTTPException(429, detail=f"今日{label}额度已用完（{used}/{limit}），请升级或续费 VIP")
    setattr(usage, used_field, used + 1)
    await session.commit()
    return usage_date


async def refund_quota(
        session: AsyncSession,
        user_id: int,
        feature: str,
        usage_date: date | None = None,
):
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
