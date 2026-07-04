from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_502_BAD_GATEWAY

from services.alipay_service import AlipayError
from dependencies import get_session, require_admin
from models.user import User
from repository.admin_repo import AdminRepository
from schemas.admin_schemas import (
    AgentConfigOut,
    AgentConfigUpdateIn,
    AdminPackageIn,
    AdminPackageOut,
    AdminPackageUpdateIn,
    BanUserOut,
    KnowledgeBaseOut,
    KnowledgeBaseUpsertIn,
    OrderPageOut,
    OrderOut,
    RefundAuditPageOut,
    RefundAuditOut,
    RefundReviewIn,
    SensitiveWordPageOut,
    ResetPasswordIn,
    UserPageOut,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/packages", response_model=list[AdminPackageOut])
async def list_admin_packages(
        package_scope: str | None = Query(default=None, max_length=30),
        session: AsyncSession = Depends(get_session),
):
    return await AdminRepository(session).list_packages(package_scope)


@router.post("/packages", response_model=AdminPackageOut)
async def create_admin_package(data: AdminPackageIn, session: AsyncSession = Depends(get_session)):
    values = data.model_dump()
    if values["package_scope"] == "EXPERT_SERVICE" and (not values.get("expert_type") or not values.get("delivery_days")):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="专家套餐必须填写专家类型和交付天数")
    return await AdminRepository(session).create_package(values)


@router.put("/packages/{package_scope}/{package_id}", response_model=AdminPackageOut)
async def update_admin_package(
        package_scope: str,
        package_id: int,
        data: AdminPackageUpdateIn,
        session: AsyncSession = Depends(get_session),
):
    package = await AdminRepository(session).update_package(package_scope, package_id, data.model_dump(exclude_unset=True))
    if not package:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="套餐不存在")
    return package


@router.delete("/packages/{package_scope}/{package_id}")
async def delete_admin_package(
        package_scope: str,
        package_id: int,
        session: AsyncSession = Depends(get_session),
):
    result = await AdminRepository(session).delete_package(package_scope, package_id)
    if result is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="套餐不存在")
    if result is False:
        raise HTTPException(status_code=409, detail="套餐已有订单引用，不能删除，请改为下架")
    return {"id": package_id, "package_scope": package_scope, "deleted": True}


@router.get("/users", response_model=UserPageOut)
async def list_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        keyword: str | None = Query(default=None, max_length=100),
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    users, total = await repository.list_users(page, page_size, keyword)
    return {"items": users, "total": total, "page": page, "page_size": page_size}


@router.put("/users/{user_id}/ban", response_model=BanUserOut)
async def toggle_user_ban(
        user_id: int,
        current_admin: User = Depends(require_admin),
        session: AsyncSession = Depends(get_session)
):
    if current_admin.id == user_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="管理员不能封禁自己的账号")
    repository = AdminRepository(session)
    user = await repository.toggle_user_ban(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="用户不存在")
    return {"id": user.id, "is_banned": user.is_banned}


@router.put("/users/{user_id}/password")
async def reset_user_password(
        user_id: int,
        data: ResetPasswordIn,
        current_admin: User = Depends(require_admin),
        session: AsyncSession = Depends(get_session),
):
    if current_admin.id == user_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="不能在此重置当前管理员密码")
    user = await AdminRepository(session).reset_user_password(user_id, data.password)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="用户不存在")
    return {"message": "密码已重置"}


@router.delete("/users/{user_id}")
async def delete_user(
        user_id: int,
        current_admin: User = Depends(require_admin),
        session: AsyncSession = Depends(get_session),
):
    if current_admin.id == user_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="管理员不能删除自己的账号")
    user = await AdminRepository(session).soft_delete_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="用户不存在")
    return {"message": "用户已删除"}


@router.get("/finance/orders", response_model=OrderPageOut)
async def list_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: str | None = Query(default=None, max_length=30),
        order_type: str | None = Query(default=None, max_length=30),
        payment_provider: str | None = Query(default=None, max_length=30),
        keyword: str | None = Query(default=None, max_length=100),
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    orders, total = await repository.list_orders(page, page_size, status, order_type, payment_provider, keyword)
    return {"items": orders, "total": total, "page": page, "page_size": page_size}


@router.post("/finance/orders/{order_id}/sync", response_model=OrderOut)
async def sync_finance_order_payment(
        order_id: int,
        session: AsyncSession = Depends(get_session),
):
    repository = AdminRepository(session)
    try:
        order = await repository.sync_alipay_order(order_id)
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="支付宝订单不存在或无法同步")
    return order


@router.get("/finance/refunds", response_model=RefundAuditPageOut)
async def list_refunds(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: str | None = Query(default=None, max_length=20),
        session: AsyncSession = Depends(get_session),
):
    repository = AdminRepository(session)
    refunds, total = await repository.list_refunds(page, page_size, status)
    return {"items": refunds, "total": total, "page": page, "page_size": page_size}


@router.put("/finance/refunds/{refund_id}", response_model=RefundAuditOut)
async def review_refund(
        refund_id: int,
        data: RefundReviewIn,
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    try:
        refund = await repository.review_refund(refund_id, data.status, data.review_note)
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not refund:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="退款申请不存在")
    return await repository._refund_payload(refund)


@router.get("/ai/agents", response_model=list[AgentConfigOut])
async def list_agents(session: AsyncSession = Depends(get_session)):
    repository = AdminRepository(session)
    return await repository.list_agents()


@router.put("/ai/agents/{agent_id}", response_model=AgentConfigOut)
async def update_agent(
        agent_id: int,
        data: AgentConfigUpdateIn,
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    agent = await repository.update_agent(agent_id, data.model_dump(exclude_unset=True))
    if not agent:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="智能体配置不存在")
    return agent


@router.post("/ai/knowledge", response_model=KnowledgeBaseOut)
async def upsert_knowledge(
        data: KnowledgeBaseUpsertIn,
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    knowledge = await repository.upsert_knowledge(data.model_dump())
    if not knowledge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="知识库记录不存在")
    return knowledge


@router.get("/audit/sensitive", response_model=SensitiveWordPageOut)
async def list_sensitive_logs(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    logs, total = await repository.list_sensitive_logs(page, page_size)
    return {"items": logs, "total": total, "page": page, "page_size": page_size}
