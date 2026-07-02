from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from models.asset import NamingAsset
from models.finance import Order, PackageConfig
from models.marketplace import ExpertProfile, ExpertServicePackage
from models.user import User
from repository.admin_repo import AdminRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.membership_repo import MembershipRepository


async def create_user(session, suffix: str):
    user = User(email=f"{suffix}@test.local", username=suffix, password="test")
    session.add(user)
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_admin_order_list_expires_stale_membership_order(session):
    user = await create_user(session, "expire-member")
    package = PackageConfig(
        package_code="QUOTA_NAMING_30",
        name="30 quota",
        price=Decimal("9.90"),
        api_quota=30,
        status="ACTIVE",
    )
    session.add(package)
    await session.commit()

    order = await MembershipRepository(session).create_order(user.id, package.id)
    order.created_time = datetime.now() - timedelta(minutes=16)
    await session.commit()

    orders, total = await AdminRepository(session).list_orders(1, 20)
    await session.refresh(order)

    assert total == 1
    assert order.status == "CANCELLED"
    assert orders[0]["status"] == "CANCELLED"

    paid_order, membership = await MembershipRepository(session).pay_order(order.id, user.id)
    assert paid_order is None
    assert membership is None


@pytest.mark.asyncio
async def test_stale_expert_order_expires_finance_and_service_order(session):
    customer = await create_user(session, "expire-customer")
    expert_user = await create_user(session, "expire-expert")
    asset = NamingAsset(user_id=customer.id, thread_id="expire-thread", name="Brand", category="企业名")
    expert = ExpertProfile(
        user_id=expert_user.id,
        display_name="Expert",
        expert_type="BRAND_CONSULTANT",
        bio="Long enough expert bio for testing brand consulting orders.",
        credentials="Long enough credentials for testing brand consulting orders.",
        years_experience=5,
        status="APPROVED",
    )
    package = ExpertServicePackage(
        name="Review",
        expert_type="BRAND_CONSULTANT",
        price=Decimal("99.00"),
        delivery_days=3,
        description="Review package",
        status="ACTIVE",
    )
    session.add_all([asset, expert, package])
    await session.commit()

    repo = MarketplaceRepository(session)
    service = await repo.create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "naming_asset_id": asset.id,
        "requirements": "Review the brand name",
    })
    finance = await session.get(Order, service.finance_order_id)
    finance.created_time = datetime.now() - timedelta(minutes=16)
    await session.commit()

    items, total = await repo.list_customer_orders(customer.id, 1, 20)
    await session.refresh(finance)
    await session.refresh(service)

    assert total == 1
    assert finance.status == "CANCELLED"
    assert service.status == "CANCELLED"
    assert items[0]["payment_status"] == "CANCELLED"
    assert items[0]["status"] == "CANCELLED"
    assert not await repo.customer_transition(service, customer.id, "PAY")
