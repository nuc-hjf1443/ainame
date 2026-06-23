from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from dependencies import get_session, require_admin
from models.user import User
from repository.admin_repo import AdminRepository
from schemas.admin_schemas import (
    AgentConfigOut,
    AgentConfigUpdateIn,
    BanUserOut,
    KnowledgeBaseOut,
    KnowledgeBaseUpsertIn,
    OrderPageOut,
    RefundAuditOut,
    RefundReviewIn,
    SensitiveWordPageOut,
    ResetPasswordIn,
    UserPageOut,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


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
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    orders, total = await repository.list_orders(page, page_size)
    return {"items": orders, "total": total, "page": page, "page_size": page_size}


@router.put("/finance/refunds/{refund_id}", response_model=RefundAuditOut)
async def review_refund(
        refund_id: int,
        data: RefundReviewIn,
        session: AsyncSession = Depends(get_session)
):
    repository = AdminRepository(session)
    refund = await repository.review_refund(refund_id, data.status, data.review_note)
    if not refund:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="退款申请不存在")
    return refund


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
