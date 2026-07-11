import logging
from datetime import date

from models import AsyncSessionFactory
from models.visual import BrandKit, BrandVisual
from repository.visual_repo import BrandVisualRepository
from core.aigc_tools import submit_visual_task
from services.visual_service import persist_visual_image, refresh_brand_visual_status
from schemas.visual_schemas import BrandKitCreateIn


logger = logging.getLogger(__name__)
ASSET_SPECS = (
    ("LOGO", 1, "primary logo concept, centered symbol and clean Chinese brand wordmark"),
    ("BUSINESS_CARD", 1, "premium business card front and back mockup using the brand identity"),
)


def _asset_prompt(data: BrandKitCreateIn, description: str) -> str:
    return (
        f"Create a professional {description} for the Chinese brand '{data.name}'. "
        f"Brand meaning: {data.moral or 'confident and memorable'}. Industry: {data.industry}. "
        f"Target audience: {data.audience}. Visual style: {data.design_style}. "
        f"Primary color: {data.primary_color}. Square 1:1 composition, clean light background, "
        "commercial identity presentation, crisp details, no watermark, no unrelated text."
    )


async def prepare_brand_kit(
        data: BrandKitCreateIn,
        user_id: int,
        repository: BrandVisualRepository,
        quota_usage_date: date,
) -> BrandKit:
    slogan = f"{data.name}，让品牌被看见"
    kit = BrandKit(
        user_id=user_id,
        naming_asset_id=data.naming_asset_id,
        thread_id=data.thread_id,
        name=data.name,
        moral=data.moral,
        industry=data.industry,
        audience=data.audience,
        design_style=data.design_style,
        primary_color=data.primary_color,
        image_model=data.image_model,
        slogan=slogan[:255],
        status="PENDING",
        quota_usage_date=quota_usage_date,
    )
    assets = [
        BrandVisual(
            user_id=user_id,
            thread_id=data.thread_id,
            name=data.name,
            category="企业名",
            moral=data.moral,
            design_style=data.design_style,
            image_model=data.image_model,
            asset_type=asset_type,
            variant_index=variant_index,
            slogan=slogan[:255],
            prompt_used=_asset_prompt(data, description),
            status="PENDING",
        )
        for asset_type, variant_index, description in ASSET_SPECS
    ]
    return await repository.create_brand_kit(kit, assets)


async def process_brand_kit(kit_id: int, user_id: int) -> None:
    async with AsyncSessionFactory() as session:
        repository = BrandVisualRepository(session)
        kit = await repository.get_user_brand_kit(kit_id, user_id)
        if not kit:
            return
        await repository.set_brand_kit_status(kit, "PROCESSING")
        assets = await repository.list_brand_kit_assets(kit.id)
        for asset in assets:
            if asset.status != "PENDING":
                continue
            try:
                task = await submit_visual_task(asset.prompt_used or "", asset.image_model)
                image_url, image_path = task.image_url, None
                if task.status == "SUCCESS":
                    if not task.image_url:
                        raise ValueError("视觉服务未返回图片地址")
                    image_url, image_path = await persist_visual_image(task.image_url, user_id)
                if task.status == "FAILED":
                    raise RuntimeError("视觉生成失败，请稍后重新生成")
                await repository.update_visual_status(
                    asset,
                    status=task.status,
                    task_id=task.task_id,
                    image_url=image_url,
                    image_path=image_path,
                )
            except Exception as exc:
                logger.warning(
                    "Brand kit visual asset generation failed for kit_id=%s asset_id=%s",
                    kit.id,
                    asset.id,
                    exc_info=True,
                )
                await repository.update_visual_status(
                    asset,
                    status="FAILED",
                    error_message=str(exc)[:1000],
                    clear_image=True,
                    clear_task=True,
                )
                continue

        kit = await repository.sync_brand_kit_status(kit)


async def regenerate_brand_kit_asset(
        kit: BrandKit,
        asset: BrandVisual,
        repository: BrandVisualRepository,
        *,
        image_model: str | None = None,
) -> tuple[BrandKit, BrandVisual]:
    if image_model:
        asset.image_model = image_model
        await repository.session.commit()
        await repository.session.refresh(asset)

    await repository.set_brand_kit_status(kit, "PROCESSING")
    try:
        await repository.update_visual_status(
            asset,
            status="PROCESSING",
            error_message=None,
            clear_image=True,
            clear_task=True,
        )
        task = await submit_visual_task(asset.prompt_used or "", asset.image_model)
        image_url, image_path = task.image_url, None
        if task.status == "SUCCESS":
            if not task.image_url:
                raise ValueError("Visual service did not return an image URL")
            image_url, image_path = await persist_visual_image(task.image_url, asset.user_id)
        if task.status == "FAILED":
            raise RuntimeError("Visual generation failed")
        asset = await repository.update_visual_status(
            asset,
            status=task.status,
            task_id=task.task_id,
            image_url=image_url,
            image_path=image_path,
            error_message=None,
        )
    except Exception as exc:
        logger.warning(
            "Brand kit visual asset regeneration failed for kit_id=%s asset_id=%s",
            kit.id,
            asset.id,
            exc_info=True,
        )
        asset = await repository.update_visual_status(
            asset,
            status="FAILED",
            error_message=str(exc)[:1000],
            clear_image=True,
            clear_task=True,
        )
    kit = await repository.sync_brand_kit_status(kit)
    return kit, asset


async def process_brand_kit_asset(asset_id: int, user_id: int) -> None:
    async with AsyncSessionFactory() as session:
        repository = BrandVisualRepository(session)
        asset = await repository.get_user_visual(asset_id, user_id)
        if not asset or not asset.brand_kit_id:
            return
        kit = await repository.get_user_brand_kit(asset.brand_kit_id, user_id)
        if not kit:
            return
        await regenerate_brand_kit_asset(kit, asset, repository)


async def refresh_brand_kit(kit: BrandKit, repository: BrandVisualRepository) -> BrandKit | None:
    assets = await repository.list_brand_kit_assets(kit.id)
    for asset in assets:
        if asset.status not in {"SUCCESS", "FAILED"} and asset.task_id:
            refreshed = await refresh_brand_visual_status(asset, repository)
            await repository.ensure_visual_public_url(refreshed)
    return await repository.sync_brand_kit_status(kit)
