from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session
from models.user import User
from repository.asset_repo import AssetRepository
from schemas.asset_schemas import AssetPageOut, NamingAssetCreateIn, NamingAssetOut, VisualAssetPageOut


router = APIRouter(prefix="/me/assets", tags=["assets"])


@router.post("/names", response_model=NamingAssetOut)
async def create_name_asset(data: NamingAssetCreateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    try:
        return await AssetRepository(session).create_name(user.id, data.model_dump())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, detail="该名字已经收藏")


@router.get("/names", response_model=AssetPageOut)
async def list_name_assets(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    items, total = await AssetRepository(session).list_names(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/names/{asset_id}")
async def delete_name_asset(asset_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
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
async def list_visual_assets(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    items, total = await AssetRepository(session).list_visuals(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
