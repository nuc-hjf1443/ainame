from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from services.brand_kit_service import prepare_brand_kit, process_brand_kit, process_brand_kit_asset, refresh_brand_kit
from services.quota_service import refund_brand_kit_quota_once, refund_quota, refund_visual_quota_once, reserve_quota
from services.visual_service import create_brand_visual, refresh_brand_visual_status
from dependencies import get_current_user, get_session
from models.user import User
from repository.asset_repo import AssetRepository
from repository.visual_repo import BrandVisualRepository
from schemas.visual_schemas import BrandKitAssetRegenerateIn, BrandKitCreateIn, BrandKitOut, BrandKitPageOut, VisualGenerateIn, VisualGenerateOut, VisualStatusOut


auth_handler = AuthHandler()
router = APIRouter(prefix="/visual", tags=["visual"])


@router.post("/kits", response_model=BrandKitOut)
async def create_brand_kit(
        data: BrandKitCreateIn,
        background_tasks: BackgroundTasks,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    if data.naming_asset_id:
        asset = await AssetRepository(session).get_name(data.naming_asset_id, user.id)
        if not asset or asset.category != "企业名":
            raise HTTPException(status_code=400, detail="请选择自己的企业名资产生成品牌视觉")
        data = data.model_copy(update={
            "thread_id": asset.thread_id,
            "name": asset.name,
            "moral": asset.moral or "",
            "category": "企业名",
        })
    quota_usage_date = await reserve_quota(session, user.id, "VISUAL")
    repository = BrandVisualRepository(session)
    try:
        kit = await prepare_brand_kit(data, user.id, repository, quota_usage_date)
    except Exception:
        await refund_quota(session, user.id, "VISUAL", quota_usage_date)
        raise
    background_tasks.add_task(process_brand_kit, kit.id, user.id)
    return await repository.brand_kit_payload(kit)


@router.get("/kits", response_model=BrandKitPageOut)
async def list_brand_kits(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = BrandVisualRepository(session)
    kits, total = await repository.list_user_brand_kits(user.id, page, page_size)
    refreshed_kits = []
    for kit in kits:
        refreshed = await refresh_brand_kit(kit, repository)
        if refreshed:
            refreshed_kits.append(refreshed)
    return {
        "items": [await repository.brand_kit_payload(kit) for kit in refreshed_kits],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/kits/{kit_id}", response_model=BrandKitOut)
async def get_brand_kit(
        kit_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = BrandVisualRepository(session)
    kit = await repository.get_user_brand_kit(kit_id, user.id)
    if not kit:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌方案不存在")
    kit = await refresh_brand_kit(kit, repository)
    if not kit:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌视觉生成失败，额度已退回，请重新生成")
    if kit.status == "__never__":
        await refund_brand_kit_quota_once(session, kit.id, user.id)
        await repository.delete_brand_kit(kit)
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌视觉生成失败，额度已退回，请重新生成")
    return await repository.brand_kit_payload(kit)


@router.post("/kits/{kit_id}/assets/{asset_id}/regenerate", response_model=BrandKitOut)
async def regenerate_brand_kit_visual_asset(
        kit_id: int,
        asset_id: int,
        data: BrandKitAssetRegenerateIn,
        background_tasks: BackgroundTasks,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = BrandVisualRepository(session)
    kit = await repository.get_user_brand_kit(kit_id, user.id)
    if not kit:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌方案不存在")
    asset = await repository.get_user_brand_kit_asset(kit_id, asset_id, user.id)
    if not asset:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌素材不存在")
    if asset.status in {"PENDING", "PROCESSING"}:
        raise HTTPException(status_code=409, detail="该素材正在生成中")

    if data.image_model:
        asset.image_model = data.image_model
        await session.commit()
        await session.refresh(asset)
    await repository.set_brand_kit_status(kit, "PROCESSING")
    await repository.update_visual_status(
        asset,
        status="PROCESSING",
        error_message=None,
        clear_image=True,
        clear_task=True,
    )
    background_tasks.add_task(process_brand_kit_asset, asset.id, user.id)
    return await repository.brand_kit_payload(kit)


@router.delete("/kits/{kit_id}")
async def delete_brand_kit(
        kit_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = BrandVisualRepository(session)
    kit = await repository.get_user_brand_kit(kit_id, user.id)
    if not kit:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="品牌方案不存在")
    await repository.delete_brand_kit(kit)
    return {"message": "品牌视觉方案已删除"}


@router.post("/generate", response_model=VisualGenerateOut)
async def generate_visual(
        data: VisualGenerateIn,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    if data.category != "企业名":
        raise HTTPException(status_code=400, detail="仅企业起名支持视觉生成")
    quota_usage_date = await reserve_quota(session, user.id, "VISUAL")
    repository = BrandVisualRepository(session)
    try:
        visual = await create_brand_visual(data, user.id, repository, quota_usage_date)
        if visual.status == "FAILED":
            await refund_visual_quota_once(session, visual.id, user.id)
            await repository.delete_visual(visual)
            raise HTTPException(status_code=500, detail="视觉生成失败，额度已退回，请重新生成")
    except HTTPException:
        raise
    except Exception:
        await refund_quota(session, user.id, "VISUAL", quota_usage_date)
        raise
    return VisualGenerateOut(
        visual_id=visual.id,
        task_id=visual.task_id or "",
        slogan=visual.slogan or "",
        status=visual.status,
        image_url=visual.image_url,
        image_model=visual.image_model,
    )


@router.get("/{visual_id}", response_model=VisualStatusOut)
async def get_visual_status(
        visual_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    repository = BrandVisualRepository(session)
    visual = await repository.get_user_visual(visual_id, user.id)
    if not visual:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉生成记录不存在")

    previous_status = visual.status
    visual = await refresh_brand_visual_status(visual, repository)
    visual = await repository.ensure_visual_public_url(visual)
    if previous_status != "FAILED" and visual.status == "FAILED":
        await refund_visual_quota_once(session, visual.id, user.id)
        await repository.delete_visual(visual)
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉生成失败，额度已退回，请重新生成")
    return VisualStatusOut(
        visual_id=visual.id,
        status=visual.status,
        image_url=visual.image_url,
        slogan=visual.slogan,
        image_model=visual.image_model,
    )
