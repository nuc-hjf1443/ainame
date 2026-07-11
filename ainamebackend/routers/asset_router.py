from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session
from models.user import User
from repository.asset_repo import AssetRepository
from repository.visual_repo import BrandVisualRepository
from schemas.asset_schemas import AssetPageOut, NamingAssetCreateIn, NamingAssetOut, VisualAssetPageOut
from services.name_report_service import build_name_report_pdf
from services.visual_service import refresh_brand_visual_status


router = APIRouter(prefix="/me/assets", tags=["assets"])


@router.post("/names", response_model=NamingAssetOut)
async def create_name_asset(
        data: NamingAssetCreateIn,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    try:
        return await AssetRepository(session).create_name(user.id, data.model_dump())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, detail="该名字已经收藏")


@router.get("/names", response_model=AssetPageOut)
async def list_name_assets(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    items, total = await AssetRepository(session).list_names(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/names/{asset_id}/report")
async def download_name_report(
        asset_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    asset = await AssetRepository(session).get_name(asset_id, user.id)
    if not asset:
        raise HTTPException(404, detail="名字资产不存在")

    visual_repo = BrandVisualRepository(session)
    brand_kit = await visual_repo.get_latest_user_brand_kit_for_name(asset.id, user.id)
    brand_assets = await visual_repo.list_brand_kit_assets(brand_kit.id) if brand_kit else []
    content = build_name_report_pdf(asset, brand_kit=brand_kit, brand_assets=brand_assets)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="name-report-{asset.id}.pdf"'},
    )


@router.delete("/names/{asset_id}")
async def delete_name_asset(
        asset_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repo = AssetRepository(session)
    asset = await repo.get_name(asset_id, user.id)
    if not asset:
        raise HTTPException(404, detail="名字资产不存在")
    try:
        await repo.delete_name(asset)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, detail="该名字已用于社区帖子或专家订单，不能取消收藏")
    return {"message": "已取消收藏"}


@router.get("/visuals", response_model=VisualAssetPageOut)
async def list_visual_assets(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    items, total = await AssetRepository(session).list_visuals(user.id, page, page_size)
    visual_repo = BrandVisualRepository(session)
    refreshed_items = []
    for item in items:
        if item.status not in {"SUCCESS", "FAILED"} and item.task_id:
            item = await refresh_brand_visual_status(item, visual_repo)
        item = await visual_repo.ensure_visual_public_url(item)
        refreshed_items.append(item)
    items = refreshed_items
    return {"items": items, "total": total, "page": page, "page_size": page_size}
