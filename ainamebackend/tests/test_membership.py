from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from services import quota_service
from services.quota_service import (
    current_usage_date,
    quota_snapshot,
    refund_brand_kit_quota_once,
    refund_quota,
    refund_visual_quota_once,
    reserve_quota,
)
from models.asset import NamingAsset
from models.finance import DailyQuotaUsage, PackageConfig, UserMembership, UserQuotaBalance
from models.marketplace import ExpertProfile, ExpertServicePackage
from models.user import User
from models.visual import BrandKit, BrandVisual
from repository.admin_repo import AdminRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.membership_repo import MembershipRepository
from routers import visual_router


async def create_user(session, suffix: str):
    user = User(email=f"{suffix}@test.local", username=suffix, password="old-password")
    session.add(user)
    await session.commit()
    return user


async def create_vip_package(session, code="VIP_MONTHLY", days=30):
    package = PackageConfig(
        package_code=code,
        name="月度 VIP" if days == 30 else "年度 VIP",
        price=Decimal("19.90") if days == 30 else Decimal("199.00"),
        duration_days=days,
        naming_daily_quota=100,
        visual_daily_quota=20,
        expert_discount=Decimal("0.90"),
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()
    return package


async def create_naming_quota_package(session, code="QUOTA_NAMING_30", quota=30):
    package = PackageConfig(
        package_code=code,
        name="30 次起名包",
        price=Decimal("9.90"),
        api_quota=quota,
        duration_days=0,
        naming_daily_quota=0,
        visual_daily_quota=0,
        expert_discount=Decimal("1.00"),
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()
    return package


@pytest.mark.asyncio
async def test_membership_payment_is_idempotent_and_renewal_extends(session):
    user = await create_user(session, "member")
    package = await create_vip_package(session)
    repo = MembershipRepository(session)

    first_order = await repo.create_order(user.id, package.id)
    _, first_membership = await repo.pay_order(first_order.id, user.id)
    first_expiry = first_membership.end_time

    _, repeated_membership = await repo.pay_order(first_order.id, user.id)
    assert repeated_membership.end_time == first_expiry

    renewal_order = await repo.create_order(user.id, package.id)
    _, renewed_membership = await repo.pay_order(renewal_order.id, user.id)
    assert renewed_membership.end_time == first_expiry + timedelta(days=30)


@pytest.mark.asyncio
async def test_free_and_vip_daily_quota_and_refund(session):
    free_user = await create_user(session, "free-quota")
    free_user_id = free_user.id
    for _ in range(5):
        await reserve_quota(session, free_user_id, "NAMING")
    with pytest.raises(HTTPException) as naming_error:
        await reserve_quota(session, free_user_id, "NAMING")
    assert naming_error.value.status_code == 429

    with pytest.raises(HTTPException) as visual_error:
        await reserve_quota(session, free_user_id, "VISUAL")
    assert visual_error.value.status_code == 429

    await refund_quota(session, free_user_id, "NAMING")
    await reserve_quota(session, free_user_id, "NAMING")

    vip_user = await create_user(session, "vip-quota")
    package = await create_vip_package(session, "VIP_YEARLY", 365)
    session.add(UserMembership(
        user_id=vip_user.id,
        package_id=package.id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(days=365),
        status="ACTIVE",
    ))
    await session.commit()
    await reserve_quota(session, vip_user.id, "VISUAL")
    snapshot = await quota_snapshot(session, vip_user.id)
    assert snapshot["visual_limit"] == 20
    assert snapshot["visual_used"] == 1


@pytest.mark.asyncio
async def test_free_quota_is_total_and_vip_quota_is_monthly(session, monkeypatch):
    free_user = await create_user(session, "free-total-quota")
    session.add(DailyQuotaUsage(user_id=free_user.id, usage_date=date(2026, 6, 30), naming_used=5))
    await session.commit()
    monkeypatch.setattr(quota_service, "current_usage_date", lambda: date(2026, 7, 1))

    with pytest.raises(HTTPException) as free_error:
        await reserve_quota(session, free_user.id, "NAMING")
    assert free_error.value.status_code == 429

    vip_user = await create_user(session, "vip-monthly-quota")
    package = PackageConfig(
        package_code="VIP_MONTHLY_LOW",
        package_type="VIP",
        name="月度 VIP 小额",
        price=Decimal("1.00"),
        duration_days=30,
        naming_daily_quota=2,
        visual_daily_quota=1,
        expert_discount=Decimal("1.00"),
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()
    session.add(UserMembership(
        user_id=vip_user.id,
        package_id=package.id,
        start_time=datetime(2026, 6, 1),
        end_time=datetime(2026, 8, 1),
        status="ACTIVE",
    ))
    session.add(DailyQuotaUsage(user_id=vip_user.id, usage_date=date(2026, 6, 30), naming_used=2))
    await session.commit()

    await reserve_quota(session, vip_user.id, "NAMING")
    await reserve_quota(session, vip_user.id, "NAMING")
    with pytest.raises(HTTPException) as vip_error:
        await reserve_quota(session, vip_user.id, "NAMING")
    assert vip_error.value.status_code == 429


@pytest.mark.asyncio
async def test_naming_quota_package_adds_balance_and_is_used_after_daily_quota(session):
    user = await create_user(session, "quota-balance")
    package = await create_naming_quota_package(session, quota=30)
    repo = MembershipRepository(session)

    order = await repo.create_order(user.id, package.id)
    _, membership = await repo.pay_order(order.id, user.id)
    assert membership is None

    balance = await repo.get_quota_balance(user.id)
    assert balance.naming_balance == 30

    for _ in range(5):
        await reserve_quota(session, user.id, "NAMING")

    token = await reserve_quota(session, user.id, "NAMING")
    assert token == {"source": "BALANCE"}
    await session.refresh(balance)
    assert balance.naming_balance == 29

    await refund_quota(session, user.id, "NAMING", token)
    await session.refresh(balance)
    assert balance.naming_balance == 30


@pytest.mark.asyncio
async def test_naming_quota_still_blocks_without_daily_or_balance(session):
    user = await create_user(session, "no-balance")
    session.add(UserQuotaBalance(user_id=user.id, naming_balance=0))
    await session.commit()

    for _ in range(5):
        await reserve_quota(session, user.id, "NAMING")

    with pytest.raises(HTTPException) as error:
        await reserve_quota(session, user.id, "NAMING")
    assert error.value.status_code == 429


@pytest.mark.asyncio
async def test_vip_expert_order_uses_discount_snapshot(session):
    customer = await create_user(session, "vip-customer")
    expert_user = await create_user(session, "discount-expert")
    vip_package = await create_vip_package(session)
    session.add(UserMembership(
        user_id=customer.id,
        package_id=vip_package.id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(days=30),
        status="ACTIVE",
    ))
    expert = ExpertProfile(
        user_id=expert_user.id,
        display_name="品牌专家",
        expert_type="BRAND_CONSULTANT",
        bio="具备长期品牌咨询和企业命名项目服务经验。",
        credentials="品牌咨询与企业命名相关完整项目资历。",
        years_experience=8,
        status="APPROVED",
    )
    service_package = ExpertServicePackage(
        name="品牌精批",
        expert_type="BRAND_CONSULTANT",
        price=Decimal("200.00"),
        delivery_days=3,
        description="结构化品牌分析",
        status="ACTIVE",
    )
    asset = NamingAsset(
        user_id=customer.id,
        thread_id="vip-order",
        name="启明",
        category="企业名",
        moral="开启光明",
    )
    session.add_all([expert, service_package, asset])
    await session.commit()

    order = await MarketplaceRepository(session).create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": service_package.id,
        "naming_asset_id": asset.id,
        "requirements": "重点评估品牌传播优势",
    })
    assert order.original_amount == Decimal("200.00")
    assert order.discount_rate == Decimal("0.90")
    assert order.amount == Decimal("180.00")


@pytest.mark.asyncio
async def test_admin_password_reset_hashes_and_soft_delete_blocks_account(session):
    user = await create_user(session, "admin-target")
    original_hash = user.password
    repo = AdminRepository(session)

    await repo.reset_user_password(user.id, "new-password")
    assert user.password != "new-password"
    assert user.password != original_hash
    assert user.check_password("new-password")

    deleted = await repo.soft_delete_user(user.id)
    assert deleted.is_deleted is True
    assert deleted.is_banned is True


@pytest.mark.asyncio
async def test_async_visual_failure_refunds_reserved_quota_once(session, monkeypatch):
    user = await create_user(session, "visual-refund")
    usage = DailyQuotaUsage(
        user_id=user.id,
        usage_date=current_usage_date(),
        visual_used=1,
    )
    visual = BrandVisual(
        user_id=user.id,
        thread_id="visual-refund-thread",
        name="启明",
        category="企业名",
        design_style="现代极简商业风",
        image_model="wan2.6-image",
        task_id="task-1",
        status="PROCESSING",
    )
    session.add_all([usage, visual])
    await session.commit()

    async def fail_task(item, repository):
        return await repository.update_visual_status(item, status="FAILED", error_message="mock failure")

    monkeypatch.setattr(visual_router, "refresh_brand_visual_status", fail_task)
    await visual_router.get_visual_status(visual.id, user, session)
    await session.refresh(usage)
    assert usage.visual_used == 0

    await visual_router.get_visual_status(visual.id, user, session)
    await session.refresh(usage)
    assert usage.visual_used == 0


@pytest.mark.asyncio
async def test_brand_kit_quota_refund_is_idempotent(session):
    user = await create_user(session, "brand-kit-refund")
    usage = DailyQuotaUsage(user_id=user.id, usage_date=current_usage_date(), visual_used=1)
    kit = BrandKit(
        user_id=user.id,
        thread_id="brand-kit-refund-thread",
        name="启明",
        moral="开启光明",
        industry="品牌咨询",
        audience="创业团队",
        design_style="现代简约",
        primary_color="蓝色",
        image_model="wan2.6-image",
        slogan="启明，让品牌被看见",
        status="FAILED",
    )
    session.add_all([usage, kit])
    await session.commit()

    assert await refund_brand_kit_quota_once(session, kit.id, user.id) is True
    assert await refund_brand_kit_quota_once(session, kit.id, user.id) is False
    await session.refresh(usage)
    await session.refresh(kit)
    assert usage.visual_used == 0
    assert kit.quota_refunded is True


@pytest.mark.asyncio
async def test_visual_refund_uses_original_reservation_date(session, monkeypatch):
    user = await create_user(session, "cross-day-refund")
    reservation_date = date(2026, 6, 22)
    current_date = date(2026, 6, 23)
    reserved_usage = DailyQuotaUsage(user_id=user.id, usage_date=reservation_date, visual_used=1)
    current_usage = DailyQuotaUsage(user_id=user.id, usage_date=current_date, visual_used=1)
    visual = BrandVisual(
        user_id=user.id,
        thread_id="cross-day-thread",
        name="启明",
        category="企业名",
        status="FAILED",
        quota_usage_date=reservation_date,
    )
    session.add_all([reserved_usage, current_usage, visual])
    await session.commit()
    monkeypatch.setattr(quota_service, "current_usage_date", lambda: current_date)

    assert await refund_visual_quota_once(session, visual.id, user.id) is True
    await session.refresh(reserved_usage)
    await session.refresh(current_usage)

    assert reserved_usage.visual_used == 0
    assert current_usage.visual_used == 1
