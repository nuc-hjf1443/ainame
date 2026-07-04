from decimal import Decimal

import pytest

from models.finance import PackageConfig
from models.user import User
from repository.admin_repo import AdminRepository
from repository.asset_repo import AssetRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.membership_repo import MembershipRepository


@pytest.mark.asyncio
async def test_admin_unified_packages_and_membership_visibility(session):
    repo = AdminRepository(session)

    vip = await repo.create_package({
        "package_scope": "VIP",
        "name": "Monthly VIP",
        "price": Decimal("19.90"),
        "duration_days": 30,
        "naming_daily_quota": 100,
        "visual_daily_quota": 20,
        "expert_discount": Decimal("0.90"),
        "description": "VIP package",
        "status": "ACTIVE",
    })
    quota = await repo.create_package({
        "package_scope": "NAMING_QUOTA",
        "name": "30 Naming Credits",
        "price": Decimal("9.90"),
        "api_quota": 30,
        "description": "Credit package",
        "status": "ACTIVE",
    })
    inactive = PackageConfig(
        name="Inactive Credits",
        package_type="NAMING_QUOTA",
        price=Decimal("1.00"),
        api_quota=1,
        status="INACTIVE",
    )
    session.add(inactive)
    await session.commit()

    packages = await repo.list_packages()
    visible = await MembershipRepository(session).list_packages()

    assert {vip["package_scope"], quota["package_scope"]} == {"VIP", "NAMING_QUOTA"}
    assert any(item["name"] == "Monthly VIP" for item in packages)
    assert {item.name for item in visible} == {"Monthly VIP", "30 Naming Credits"}


@pytest.mark.asyncio
async def test_expert_level_filters_packages_and_order_creation(session):
    customer = User(email="level-customer@test.local", username="customer", _password="test")
    expert_user = User(email="level-expert@test.local", username="expert", _password="test")
    session.add_all([customer, expert_user])
    await session.commit()

    asset = await AssetRepository(session).create_name(customer.id, {
        "thread_id": "level-thread",
        "name": "Qiming",
        "category": "企业名",
        "moral": "Open brightness",
        "reference": None,
        "domain": None,
        "domain_status": None,
    })
    repo = MarketplaceRepository(session)
    expert = await repo.apply_expert(expert_user.id, {
        "display_name": "Senior Expert",
        "expert_type": "BRAND_CONSULTANT",
        "bio": "Long brand consulting and naming project experience.",
        "credentials": "Complete brand consulting credentials.",
        "years_experience": 8,
    })
    await repo.review_expert(expert.id, expert_user.id, "APPROVED", None, "SENIOR")
    standard_package = await repo.create_package({
        "name": "Standard Review",
        "expert_type": "BRAND_CONSULTANT",
        "expert_level": "STANDARD",
        "price": 99,
        "delivery_days": 2,
        "description": "Standard service",
        "status": "ACTIVE",
    })
    senior_package = await repo.create_package({
        "name": "Senior Review",
        "expert_type": "BRAND_CONSULTANT",
        "expert_level": "SENIOR",
        "price": 199,
        "delivery_days": 3,
        "description": "Senior service",
        "status": "ACTIVE",
    })

    senior_packages = await repo.list_packages("BRAND_CONSULTANT", expert_level="SENIOR")
    assert [item.id for item in senior_packages] == [senior_package.id]
    assert not await repo.create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": standard_package.id,
        "naming_asset_id": asset.id,
        "requirements": "Analyze brand communication advantages",
    })
    service = await repo.create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": senior_package.id,
        "naming_asset_id": asset.id,
        "requirements": "Analyze brand communication advantages",
    })
    assert service is not None
    assert await repo.delete_package(senior_package.id) is False


@pytest.mark.asyncio
async def test_admin_package_delete_blocks_referenced_packages(session):
    repo = AdminRepository(session)
    package = await repo.create_package({
        "package_scope": "NAMING_QUOTA",
        "name": "One Credit",
        "price": Decimal("1.00"),
        "api_quota": 1,
        "status": "ACTIVE",
    })
    user = User(email="package-delete@test.local", username="buyer", _password="test")
    session.add(user)
    await session.commit()
    order = await MembershipRepository(session).create_order(user.id, package["id"])

    assert order is not None
    assert await repo.delete_package("NAMING_QUOTA", package["id"]) is False

    unused = await repo.create_package({
        "package_scope": "NAMING_QUOTA",
        "name": "Unused Credit",
        "price": Decimal("2.00"),
        "api_quota": 2,
        "status": "ACTIVE",
    })
    assert await repo.delete_package("NAMING_QUOTA", unused["id"]) is True
