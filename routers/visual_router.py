from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from core.visual_service import create_brand_visual, refresh_brand_visual_status
from dependencies import get_session
from repository.visual_repo import BrandVisualRepository
from schemas.visual_schemas import VisualGenerateIn, VisualGenerateOut, VisualStatusOut


auth_handler = AuthHandler()
router = APIRouter(prefix="/visual", tags=["visual"])


@router.post("/generate", response_model=VisualGenerateOut)
async def generate_visual(
        data: VisualGenerateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session)
):
    repository = BrandVisualRepository(session)
    visual = await create_brand_visual(data, int(user_id), repository)
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
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session)
):
    repository = BrandVisualRepository(session)
    visual = await repository.get_user_visual(visual_id, int(user_id))
    if not visual:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉生成记录不存在")

    visual = await refresh_brand_visual_status(visual, repository)
    return VisualStatusOut(
        visual_id=visual.id,
        status=visual.status,
        image_url=visual.image_url,
        slogan=visual.slogan,
        image_model=visual.image_model,
    )
