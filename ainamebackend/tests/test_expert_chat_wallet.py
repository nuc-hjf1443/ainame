from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import mysql

from models.marketplace import ExpertChatThread
from models.user import User
from repository.asset_repo import AssetRepository
from repository.marketplace_repo import MarketplaceRepository


async def create_approved_expert_fixture(session):
    customer = User(email="chat-customer@test.local", username="customer", _password="test")
    expert_user = User(email="chat-expert@test.local", username="expert", _password="test")
    admin = User(email="chat-admin@test.local", username="admin", _password="test", role="ADMIN")
    session.add_all([customer, expert_user, admin])
    await session.commit()

    asset = await AssetRepository(session).create_name(customer.id, {
        "thread_id": "thread-chat-wallet",
        "name": "BrightWay",
        "category": "brand",
        "moral": "clear direction",
        "reference": None,
        "domain": None,
        "domain_status": None,
    })

    repo = MarketplaceRepository(session)
    expert = await repo.apply_expert(expert_user.id, {
        "display_name": "Brand Expert",
        "expert_type": "BRAND_CONSULTANT",
        "bio": "Experienced naming and brand strategy consultant.",
        "credentials": "Delivered multiple brand naming projects.",
        "years_experience": 8,
    })
    await repo.review_expert(expert.id, admin.id, "APPROVED", None)
    package = await repo.create_package({
        "name": "Brand naming review",
        "expert_type": "BRAND_CONSULTANT",
        "price": Decimal("199.00"),
        "delivery_days": 3,
        "description": "Review brand naming strategy and risks.",
        "status": "ACTIVE",
    })
    return repo, customer, expert_user, admin, expert, package, asset


@pytest.mark.asyncio
async def test_expert_chat_binds_to_order_and_settles_wallet(session):
    repo, customer, expert_user, _, expert, package, asset = await create_approved_expert_fixture(session)

    thread = await repo.create_or_get_chat_thread(customer.id, expert.id, package.id)
    assert thread
    customer_message = await repo.send_chat_message(thread.id, customer.id, "Can you review this brand name?")
    expert_message = await repo.send_chat_message(thread.id, expert_user.id, "Yes, please share the target audience.")
    assert customer_message.content.startswith("Can you")
    assert expert_message.content.startswith("Yes")

    messages, total = await repo.list_chat_messages(thread.id, customer.id, 1, 50)
    assert total == 2
    assert [item.content for item in messages] == [
        "Can you review this brand name?",
        "Yes, please share the target audience.",
    ]

    service = await repo.create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "chat_thread_id": thread.id,
        "naming_asset_id": asset.id,
        "requirements": "Please analyze positioning, meaning and risks.",
    })
    assert service
    payload = await repo.order_payload(service)
    assert payload["chat_thread_id"] == thread.id

    assert await repo.customer_transition(service, customer.id, "PAY")
    assert await repo.expert_transition(service, expert.id, "ACCEPT")
    report_values = {key: "approved content" for key in (
        "overview",
        "professional_analysis",
        "phonetic_semantic_analysis",
        "communication_advantages",
        "risk_notes",
        "recommendations",
        "conclusion",
    )}
    await repo.save_report(service, expert.id, report_values, submit=True)
    assert await repo.customer_transition(service, customer.id, "COMPLETE")

    wallet = await repo.get_wallet(expert.id)
    assert wallet["available_balance"] == Decimal("199.00")
    assert wallet["total_income"] == Decimal("199.00")

    transactions, total = await repo.list_wallet_transactions(expert.id, 1, 20)
    assert total == 1
    assert transactions[0].transaction_type == "ORDER_SETTLEMENT"
    assert transactions[0].service_order_id == service.id

    await repo._settle_completed_order(service)
    _, total_after_retry = await repo.list_wallet_transactions(expert.id, 1, 20)
    assert total_after_retry == 1


@pytest.mark.asyncio
async def test_expert_chat_thread_detail_and_attachments(session):
    repo, customer, expert_user, _, expert, package, _ = await create_approved_expert_fixture(session)
    stranger = User(email="chat-stranger@test.local", username="stranger", _password="test")
    session.add(stranger)
    await session.commit()

    thread = await repo.create_or_get_chat_thread(customer.id, expert.id, package.id)
    attachment = await repo.add_chat_attachment(thread.id, customer.id, {
        "file_name": "brand-brief.pdf",
        "file_url": "/uploads/chat/brand-brief.pdf",
        "file_path": "/tmp/brand-brief.pdf",
        "file_type": "application/pdf",
        "file_size": 128,
    })
    assert attachment
    assert attachment.uploader_user_id == customer.id

    detail = await repo.get_chat_thread_detail(thread.id, customer.id)
    assert detail["id"] == thread.id
    assert detail["package_price"] == package.price
    assert detail["expert_type"] == expert.expert_type

    expert_detail = await repo.get_chat_thread_detail(thread.id, expert_user.id)
    assert expert_detail["id"] == thread.id
    assert await repo.get_chat_thread_detail(thread.id, stranger.id) is None

    payload, total = await repo.list_chat_messages_payload(thread.id, customer.id, 1, 50)
    assert total == 1
    assert payload[0]["content"] == "上传资料：brand-brief.pdf"
    assert payload[0]["attachments"][0]["file_name"] == "brand-brief.pdf"


def test_chat_thread_ordering_is_mysql_compatible():
    statement = (
        select(ExpertChatThread)
        .order_by(
            ExpertChatThread.last_message_at.is_(None),
            ExpertChatThread.last_message_at.desc(),
            ExpertChatThread.id.desc(),
        )
        .limit(50)
    )

    sql = str(statement.compile(dialect=mysql.dialect()))
    assert "NULLS LAST" not in sql
    assert "last_message_at IS NULL" in sql


@pytest.mark.asyncio
async def test_expert_withdrawal_review_updates_wallet_balances(session):
    repo, customer, _, admin, expert, package, asset = await create_approved_expert_fixture(session)
    service = await repo.create_order(customer.id, {
        "expert_id": expert.id,
        "package_id": package.id,
        "naming_asset_id": asset.id,
        "requirements": "Please analyze positioning, meaning and risks.",
    })
    assert await repo.customer_transition(service, customer.id, "PAY")
    assert await repo.expert_transition(service, expert.id, "ACCEPT")
    report_values = {key: "approved content" for key in (
        "overview",
        "professional_analysis",
        "phonetic_semantic_analysis",
        "communication_advantages",
        "risk_notes",
        "recommendations",
        "conclusion",
    )}
    await repo.save_report(service, expert.id, report_values, submit=True)
    assert await repo.customer_transition(service, customer.id, "COMPLETE")

    withdrawal = await repo.create_withdrawal(expert.id, {
        "amount": Decimal("80.00"),
        "alipay_account": "expert@example.com",
        "real_name": "Expert User",
    })
    assert withdrawal.status == "PENDING"
    wallet = await repo.get_wallet(expert.id)
    assert wallet["available_balance"] == Decimal("119.00")
    assert wallet["withdrawing_balance"] == Decimal("80.00")

    reviewed = await repo.review_withdrawal(withdrawal.id, admin.id, "APPROVED", "paid offline")
    assert reviewed.status == "APPROVED"
    wallet = await repo.get_wallet(expert.id)
    assert wallet["available_balance"] == Decimal("119.00")
    assert wallet["withdrawing_balance"] == Decimal("0.00")
    assert wallet["total_withdrawn"] == Decimal("80.00")

    rejected = await repo.create_withdrawal(expert.id, {
        "amount": Decimal("20.00"),
        "alipay_account": "expert@example.com",
        "real_name": "Expert User",
    })
    await repo.review_withdrawal(rejected.id, admin.id, "REJECTED", "invalid account")
    wallet = await repo.get_wallet(expert.id)
    assert wallet["available_balance"] == Decimal("119.00")
    assert wallet["withdrawing_balance"] == Decimal("0.00")
    assert wallet["total_withdrawn"] == Decimal("80.00")
