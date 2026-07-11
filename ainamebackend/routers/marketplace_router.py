import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_502_BAD_GATEWAY

import settings
from services.alipay_service import AlipayClient, AlipayError
from services.marketplace_service import generate_expert_report_draft
from core.payment_urls import alipay_notify_url, alipay_return_url
from dependencies import get_current_user, get_session, require_mock_payment_enabled
from models.user import User
from repository.asset_repo import AssetRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.payment_repo import PaymentRepository
from schemas.marketplace_schemas import (
    ChatAttachmentOut, ChatMessageIn, ChatMessageOut, ChatMessagePageOut, ChatThreadCreateIn,
    ChatThreadDetailOut, ChatThreadOut,
    ChatThreadPageOut, ExpertApplyIn, ExpertOut, ExpertPageOut, ExpertReviewOut,
    RejectOrderIn, ReportIn, ReportOut, ReviewIn, ServiceOrderCreateIn, ServiceOrderOut,
    ServiceOrderPageOut, ServicePackageOut, WalletOut, WalletTransactionPageOut,
    WithdrawalCreateIn, WithdrawalOut, WithdrawalPageOut,
)
from schemas.payment_schemas import AlipayPaymentOut


router = APIRouter(prefix="/marketplace", tags=["marketplace"])
CHAT_UPLOAD_DIR = settings.BASE_DIR / "uploads" / "chat"
MAX_CHAT_ATTACHMENT_SIZE = 10 * 1024 * 1024
ALLOWED_CHAT_ATTACHMENT_TYPES = {
    "application/pdf",
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_CHAT_ATTACHMENT_SUFFIXES = {".pdf", ".txt", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".webp"}


async def require_expert(user: User, repo: MarketplaceRepository):
    profile = await repo.get_expert_for_user(user.id, approved=True)
    if not profile:
        raise HTTPException(403, detail="仅已审核专家可访问")
    return profile


@router.get("/experts", response_model=ExpertPageOut)
async def list_experts(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), expert_type: str | None = None, session: AsyncSession = Depends(get_session)):
    items, total = await MarketplaceRepository(session).list_experts(page, page_size, expert_type)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/experts/{expert_id}", response_model=ExpertOut)
async def get_expert(expert_id: int, session: AsyncSession = Depends(get_session)):
    result = await MarketplaceRepository(session).get_expert(expert_id)
    if not result:
        raise HTTPException(404, detail="专家不存在")
    return result


@router.get("/packages", response_model=list[ServicePackageOut])
async def list_packages(
        expert_type: str | None = None,
        expert_id: int | None = None,
        session: AsyncSession = Depends(get_session),
):
    repo = MarketplaceRepository(session)
    expert_level = None
    if expert_id:
        expert = await repo.get_expert(expert_id)
        if not expert:
            raise HTTPException(404, detail="专家不存在")
        expert_type = expert["expert_type"]
        expert_level = expert.get("expert_level") or "STANDARD"
    return await repo.list_packages(expert_type, expert_level=expert_level)


@router.post("/expert-application", response_model=ExpertOut)
async def apply_expert(data: ExpertApplyIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    profile = await repo.apply_expert(user.id, data.model_dump())
    if not profile:
        raise HTTPException(409, detail="已有待审核或有效的专家档案")
    return await repo.expert_payload(profile)


@router.get("/expert-application/me", response_model=ExpertOut)
async def my_expert_profile(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    profile = await repo.get_expert_for_user(user.id)
    if not profile:
        raise HTTPException(404, detail="尚未申请专家")
    return await repo.expert_payload(profile)


@router.post("/chat/threads", response_model=ChatThreadOut)
async def create_chat_thread(data: ChatThreadCreateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    thread = await repo.create_or_get_chat_thread(user.id, data.expert_id, data.package_id)
    if not thread:
        raise HTTPException(400, detail="专家或套餐无效，无法发起咨询")
    return await repo._chat_thread_payload(thread)


@router.get("/chat/threads", response_model=ChatThreadPageOut)
async def list_my_chat_threads(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    items, total = await MarketplaceRepository(session).list_customer_chat_threads(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/chat/threads/{thread_id}", response_model=ChatThreadDetailOut)
async def get_chat_thread_detail(
        thread_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    detail = await MarketplaceRepository(session).get_chat_thread_detail(thread_id, user.id)
    if not detail:
        raise HTTPException(404, detail="会话不存在")
    return detail


@router.get("/expert/chat/threads", response_model=ChatThreadPageOut)
async def list_expert_chat_threads(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    items, total = await repo.list_expert_chat_threads(expert.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/chat/threads/{thread_id}/messages", response_model=ChatMessagePageOut)
async def list_chat_messages(
        thread_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    result = await MarketplaceRepository(session).list_chat_messages_payload(thread_id, user.id, page, page_size)
    if not result:
        raise HTTPException(404, detail="会话不存在")
    items, total = result
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/chat/threads/{thread_id}/messages", response_model=ChatMessageOut)
async def send_chat_message(thread_id: int, data: ChatMessageIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    message = await MarketplaceRepository(session).send_chat_message(thread_id, user.id, data.content)
    if not message:
        raise HTTPException(404, detail="会话不存在或已关闭")
    return message


@router.post("/chat/threads/{thread_id}/attachments", response_model=ChatAttachmentOut)
async def upload_chat_attachment(
        thread_id: int,
        file: UploadFile = File(...),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repo = MarketplaceRepository(session)
    if not await repo.get_chat_thread_for_user(thread_id, user.id):
        raise HTTPException(404, detail="会话不存在")
    content = await file.read()
    if len(content) > MAX_CHAT_ATTACHMENT_SIZE:
        raise HTTPException(413, detail="附件不能超过 10MB")
    content_type = file.content_type or "application/octet-stream"
    original_name = Path(file.filename or "attachment").name
    suffix = Path(original_name).suffix[:20]
    if content_type not in ALLOWED_CHAT_ATTACHMENT_TYPES and suffix.lower() not in ALLOWED_CHAT_ATTACHMENT_SUFFIXES:
        raise HTTPException(400, detail="仅支持 PDF、TXT、Word 和常见图片格式")
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CHAT_UPLOAD_DIR / stored_name
    file_path.write_bytes(content)
    attachment = await repo.add_chat_attachment(thread_id, user.id, {
        "file_name": original_name,
        "file_url": f"/uploads/chat/{stored_name}",
        "file_path": str(file_path),
        "file_type": content_type,
        "file_size": len(content),
    })
    if not attachment:
        raise HTTPException(404, detail="会话不存在或已关闭")
    return attachment


@router.put("/chat/threads/{thread_id}/read", response_model=ChatThreadOut)
async def mark_chat_read(thread_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    thread = await repo.mark_chat_thread_read(thread_id, user.id)
    if not thread:
        raise HTTPException(404, detail="会话不存在")
    return await repo._chat_thread_payload(thread)


@router.get("/expert/wallet", response_model=WalletOut)
async def get_expert_wallet(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    return await repo.get_wallet(expert.id)


@router.get("/expert/wallet/transactions", response_model=WalletTransactionPageOut)
async def list_expert_wallet_transactions(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    items, total = await repo.list_wallet_transactions(expert.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/expert/withdrawals", response_model=WithdrawalOut)
async def create_expert_withdrawal(data: WithdrawalCreateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    withdrawal = await repo.create_withdrawal(expert.id, data.model_dump())
    if not withdrawal:
        raise HTTPException(400, detail="提现金额无效或余额不足")
    return withdrawal


@router.get("/expert/withdrawals", response_model=WithdrawalPageOut)
async def list_expert_withdrawals(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    items, total = await repo.list_withdrawals(expert.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/orders", response_model=ServiceOrderOut)
async def create_order(data: ServiceOrderCreateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    values = data.model_dump()
    asset_id = values.pop("naming_asset_id", None)
    name = values.pop("name", None)
    category = values.pop("category", None)
    moral = values.pop("moral", None)
    if not asset_id:
        asset = await AssetRepository(session).create_name(user.id, {
            "thread_id": f"manual_{uuid.uuid4().hex}",
            "name": name, "category": category, "moral": moral,
            "reference": "用户直接提交", "domain": None, "domain_status": None,
        }, commit=False)
        asset_id = asset.id
    values["naming_asset_id"] = asset_id
    service = await repo.create_order(user.id, values)
    if not service:
        raise HTTPException(400, detail="专家、套餐或名字资产无效")
    return await repo.order_payload(service)


@router.post("/orders/{order_id}/alipay", response_model=AlipayPaymentOut)
async def create_expert_alipay_payment(
        order_id: int,
        request: Request,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = PaymentRepository(session)
    prepared = await repository.prepare_expert_alipay_order(order_id, user.id)
    if not prepared:
        raise HTTPException(409, detail="专家订单不存在或不能发起支付")
    service, finance_order = prepared
    try:
        payment_url = AlipayClient().build_pay_url(
            finance_order,
            notify_url=alipay_notify_url(request),
            return_url=alipay_return_url(request),
        )
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {
        "order_id": service.id,
        "out_trade_no": finance_order.out_trade_no or "",
        "payment_url": payment_url,
    }


@router.get("/orders", response_model=ServiceOrderPageOut)
async def my_orders(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    items, total = await MarketplaceRepository(session).list_customer_orders(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/orders/{order_id}", response_model=ServiceOrderOut)
async def get_order(order_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    service = await repo.get_order(order_id)
    expert = await repo.get_expert_for_user(user.id)
    if not service or (service.customer_id != user.id and (not expert or service.expert_id != expert.id)):
        raise HTTPException(404, detail="订单不存在")
    return await repo.order_payload(service)


async def customer_action(order_id: int, action: str, user: User, session: AsyncSession):
    repo = MarketplaceRepository(session)
    service = await repo.get_order(order_id)
    if not service or not await repo.customer_transition(service, user.id, action):
        raise HTTPException(409, detail="当前订单状态不允许该操作")
    return await repo.order_payload(service)


@router.put("/orders/{order_id}/pay", response_model=ServiceOrderOut)
async def mock_pay(
        order_id: int,
        _: None = Depends(require_mock_payment_enabled),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    return await customer_action(order_id, "PAY", user, session)


@router.put("/orders/{order_id}/cancel", response_model=ServiceOrderOut)
async def cancel_order(order_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    service = await repo.get_order(order_id)
    if service and await repo.customer_transition(service, user.id, "CANCEL"):
        return await repo.order_payload(service)
    try:
        refunded = await PaymentRepository(session).request_expert_alipay_refund(order_id, user.id, "CUSTOMER", "用户申请取消专家服务订单")
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not refunded:
        raise HTTPException(409, detail="当前订单状态不允许该操作")
    service = await repo.get_order(order_id)
    return await repo.order_payload(service)


@router.put("/orders/{order_id}/complete", response_model=ServiceOrderOut)
async def complete_order(order_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await customer_action(order_id, "COMPLETE", user, session)


@router.post("/orders/{order_id}/review", response_model=ExpertReviewOut)
async def review_order(order_id: int, data: ReviewIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    service = await repo.get_order(order_id)
    review = await repo.add_review(service, user.id, data.model_dump()) if service else None
    if not review:
        raise HTTPException(409, detail="订单未完成、无权评价或已评价")
    return review


@router.get("/expert/orders", response_model=ServiceOrderPageOut)
async def expert_orders(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: str | None = None, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    items, total = await repo.list_expert_orders(expert.id, page, page_size, status)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def expert_action(order_id: int, action: str, user: User, session: AsyncSession, reason: str | None = None):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    service = await repo.get_order(order_id)
    if not service or not await repo.expert_transition(service, expert.id, action, reason):
        raise HTTPException(409, detail="当前订单状态不允许该操作")
    return await repo.order_payload(service)


@router.put("/expert/orders/{order_id}/accept", response_model=ServiceOrderOut)
async def accept_order(order_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await expert_action(order_id, "ACCEPT", user, session)


@router.put("/expert/orders/{order_id}/reject", response_model=ServiceOrderOut)
async def reject_order(order_id: int, data: RejectOrderIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    service = await repo.get_order(order_id)
    if service and await repo.expert_transition(service, expert.id, "REJECT", data.reason):
        return await repo.order_payload(service)
    try:
        refunded = await PaymentRepository(session).request_expert_alipay_refund(order_id, expert.id, "EXPERT", data.reason)
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not refunded:
        raise HTTPException(409, detail="当前订单状态不允许该操作")
    service = await repo.get_order(order_id)
    return await repo.order_payload(service)


@router.post("/expert/orders/{order_id}/report/draft", response_model=ReportOut)
async def draft_report(order_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    service = await repo.get_order(order_id)
    if not service or service.expert_id != expert.id or service.status != "IN_PROGRESS":
        raise HTTPException(409, detail="当前订单不能生成报告")
    asset = await AssetRepository(session).get_name(service.naming_asset_id, service.customer_id)
    draft = await generate_expert_report_draft(asset.name, asset.moral, service.requirements, expert.expert_type)
    return await repo.save_report(service, expert.id, draft.model_dump())


@router.put("/expert/orders/{order_id}/report", response_model=ReportOut)
async def save_report(order_id: int, data: ReportIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    service = await repo.get_order(order_id)
    report = await repo.save_report(service, expert.id, data.model_dump()) if service else None
    if not report:
        raise HTTPException(409, detail="当前订单不能保存报告")
    return report


@router.put("/expert/orders/{order_id}/report/submit", response_model=ReportOut)
async def submit_report(order_id: int, data: ReportIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if any(not str(value).strip() for value in data.model_dump().values()):
        raise HTTPException(400, detail="报告所有章节均不能为空")
    repo = MarketplaceRepository(session)
    expert = await require_expert(user, repo)
    service = await repo.get_order(order_id)
    report = await repo.save_report(service, expert.id, data.model_dump(), submit=True) if service else None
    if not report:
        raise HTTPException(409, detail="当前订单不能提交报告")
    return report
