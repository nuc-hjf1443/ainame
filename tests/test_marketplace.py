import pytest

from models.user import User
from repository.asset_repo import AssetRepository
from repository.marketplace_repo import MarketplaceRepository


@pytest.mark.asyncio
async def test_expert_order_report_and_review_flow(session):
    customer = User(email="customer@test.local", username="customer", _password="test")
    expert_user = User(email="expert@test.local", username="expert", _password="test")
    admin = User(email="admin@test.local", username="admin", _password="test", role="ADMIN")
    session.add_all([customer, expert_user, admin])
    await session.commit()

    asset = await AssetRepository(session).create_name(customer.id, {
        "thread_id": "thread-1", "name": "启明", "category": "企业名", "moral": "开启光明",
        "reference": "测试", "domain": None, "domain_status": None,
    })
    repo = MarketplaceRepository(session)
    expert = await repo.apply_expert(expert_user.id, {
        "display_name": "测试专家", "expert_type": "BRAND_CONSULTANT",
        "bio": "具备长期品牌咨询和企业命名项目经验。", "credentials": "品牌咨询项目与命名服务资历说明。",
        "years_experience": 8,
    })
    await repo.review_expert(expert.id, admin.id, "APPROVED", None)
    package = await repo.create_package({
        "name": "品牌精批", "expert_type": "BRAND_CONSULTANT", "price": 199,
        "delivery_days": 3, "description": "结构化品牌命名报告", "status": "ACTIVE",
    })
    expert_asset = await AssetRepository(session).create_name(expert_user.id, {
        "thread_id": "expert-thread", "name": "自购测试", "category": "企业名", "moral": None,
        "reference": None, "domain": None, "domain_status": None,
    })
    assert not await repo.create_order(expert_user.id, {
        "expert_id": expert.id, "package_id": package.id, "naming_asset_id": expert_asset.id,
        "requirements": "不允许专家购买自己的服务",
    })
    service = await repo.create_order(customer.id, {
        "expert_id": expert.id, "package_id": package.id, "naming_asset_id": asset.id,
        "requirements": "重点分析传播和商标风险",
    })

    assert await repo.customer_transition(service, customer.id, "PAY")
    assert await repo.expert_transition(service, expert.id, "ACCEPT")
    report_values = {key: "测试内容" for key in (
        "overview", "professional_analysis", "phonetic_semantic_analysis", "communication_advantages",
        "risk_notes", "recommendations", "conclusion",
    )}
    report = await repo.save_report(service, expert.id, report_values, submit=True)
    assert report.status == "SUBMITTED"
    assert service.status == "DELIVERED"
    assert await repo.customer_transition(service, customer.id, "COMPLETE")
    assert await repo.add_review(service, customer.id, {"rating": 5, "content": "专业可靠"})
    assert not await repo.add_review(service, customer.id, {"rating": 4, "content": "重复评价"})


@pytest.mark.asyncio
async def test_order_reject_triggers_mock_refund(session):
    customer = User(email="c2@test.local", username="customer", _password="test")
    expert_user = User(email="e2@test.local", username="expert", _password="test")
    session.add_all([customer, expert_user])
    await session.commit()
    asset = await AssetRepository(session).create_name(customer.id, {
        "thread_id": "thread-2", "name": "知远", "category": "企业名", "moral": None,
        "reference": None, "domain": None, "domain_status": None,
    })
    repo = MarketplaceRepository(session)
    expert = await repo.apply_expert(expert_user.id, {
        "display_name": "品牌顾问", "expert_type": "BRAND_CONSULTANT",
        "bio": "具备丰富的品牌命名和传播咨询服务经验。", "credentials": "品牌咨询服务资历完整说明。",
        "years_experience": 5,
    })
    expert.status = "APPROVED"
    package = await repo.create_package({"name": "基础精批", "expert_type": "BRAND_CONSULTANT", "price": 99, "delivery_days": 2, "description": "基础服务", "status": "ACTIVE"})
    service = await repo.create_order(customer.id, {"expert_id": expert.id, "package_id": package.id, "naming_asset_id": asset.id, "requirements": "分析名字定位"})
    await repo.customer_transition(service, customer.id, "PAY")
    assert await repo.expert_transition(service, expert.id, "REJECT", "档期冲突")
    payload = await repo.order_payload(service)
    assert payload["status"] == "CANCELLED"
    assert payload["payment_status"] == "REFUNDED"


@pytest.mark.asyncio
async def test_rejected_expert_can_reapply(session):
    user = User(email="reapply@test.local", username="expert", _password="test")
    session.add(user)
    await session.commit()
    repo = MarketplaceRepository(session)
    profile = await repo.apply_expert(user.id, {
        "display_name": "旧资料", "expert_type": "CULTURE_MASTER",
        "bio": "这是一份等待审核的专家个人简介资料。", "credentials": "这是专家资历和项目经验说明。",
        "years_experience": 3,
    })
    profile.status = "REJECTED"
    await session.commit()

    reapplied = await repo.apply_expert(user.id, {
        "display_name": "新资料", "expert_type": "CULTURE_MASTER",
        "bio": "这是重新完善后的专家个人简介资料。", "credentials": "这是重新完善后的专家资历说明。",
        "years_experience": 5,
    })

    assert reapplied.status == "PENDING"
    assert reapplied.display_name == "新资料"
