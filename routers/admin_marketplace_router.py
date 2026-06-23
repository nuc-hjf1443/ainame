from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session, require_admin
from models.user import User
from repository.community_repo import CommunityRepository
from repository.marketplace_repo import MarketplaceRepository
from repository.membership_repo import MembershipRepository
from schemas.marketplace_schemas import CommunityModerationIn, ExpertOut, ExpertPageOut, ExpertReviewDecisionIn, ServicePackageIn, ServicePackageOut, ServicePackageUpdateIn


router = APIRouter(prefix="/admin/marketplace", tags=["admin-marketplace"], dependencies=[Depends(require_admin)])


@router.post("/users/{user_id}/gift-vip")
async def gift_monthly_vip(user_id: int, session: AsyncSession = Depends(get_session)):
    membership = await MembershipRepository(session).gift_monthly_vip(user_id)
    if not membership:
        raise HTTPException(404, detail="月度 VIP 套餐或用户不存在")
    return {"user_id": user_id, "vip_expires_at": membership.end_time}


@router.get("/experts", response_model=ExpertPageOut)
async def admin_experts(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: str | None = None, session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    items, total = await repo.list_experts(page, page_size, None, admin=True, status=status)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/experts/{expert_id}/review", response_model=ExpertOut)
async def review_expert(expert_id: int, data: ExpertReviewDecisionIn, admin: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    repo = MarketplaceRepository(session)
    profile = await repo.review_expert(expert_id, admin.id, data.status, data.review_note)
    if not profile:
        raise HTTPException(404, detail="专家申请不存在")
    return await repo.expert_payload(profile)


@router.get("/packages", response_model=list[ServicePackageOut])
async def admin_packages(session: AsyncSession = Depends(get_session)):
    return await MarketplaceRepository(session).list_packages(active_only=False)


@router.post("/packages", response_model=ServicePackageOut)
async def create_package(data: ServicePackageIn, session: AsyncSession = Depends(get_session)):
    return await MarketplaceRepository(session).create_package(data.model_dump())


@router.put("/packages/{package_id}", response_model=ServicePackageOut)
async def update_package(package_id: int, data: ServicePackageUpdateIn, session: AsyncSession = Depends(get_session)):
    package = await MarketplaceRepository(session).update_package(package_id, data.model_dump(exclude_unset=True))
    if not package:
        raise HTTPException(404, detail="服务套餐不存在")
    return package


@router.get("/reports")
async def list_reports(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: str | None = None, session: AsyncSession = Depends(get_session)):
    items, total = await CommunityRepository(session).list_reports(page, page_size, status)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/reports/{report_id}")
async def moderate_report(report_id: int, data: CommunityModerationIn, admin: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    report = await CommunityRepository(session).moderate_report(report_id, admin.id, data.action, data.resolution)
    if not report:
        raise HTTPException(404, detail="待处理举报不存在")
    return {"id": report.id, "status": report.status}
