from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.visual import BrandKit, BrandVisual


class BrandVisualRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_visual(self, visual: BrandVisual) -> BrandVisual:
        self.session.add(visual)
        await self.session.commit()
        await self.session.refresh(visual)
        return visual

    async def get_user_visual(self, visual_id: int, user_id: int) -> BrandVisual | None:
        result = await self.session.execute(
            select(BrandVisual).where(
                BrandVisual.id == visual_id,
                BrandVisual.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_brand_kit(self, kit: BrandKit, assets: list[BrandVisual]) -> BrandKit:
        self.session.add(kit)
        await self.session.flush()
        for asset in assets:
            asset.brand_kit_id = kit.id
            self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(kit)
        return kit

    async def get_user_brand_kit(self, kit_id: int, user_id: int) -> BrandKit | None:
        return await self.session.scalar(
            select(BrandKit).where(BrandKit.id == kit_id, BrandKit.user_id == user_id)
        )

    async def list_brand_kit_assets(self, kit_id: int) -> list[BrandVisual]:
        result = await self.session.execute(
            select(BrandVisual).where(BrandVisual.brand_kit_id == kit_id)
            .order_by(BrandVisual.asset_type.desc(), BrandVisual.variant_index)
        )
        return list(result.scalars().all())

    async def list_user_brand_kits(self, user_id: int, page: int, page_size: int):
        where = BrandKit.user_id == user_id
        total = await self.session.scalar(select(func.count()).select_from(BrandKit).where(where)) or 0
        result = await self.session.execute(
            select(BrandKit)
            .where(where)
            .order_by(BrandKit.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def delete_brand_kit(self, kit: BrandKit) -> None:
        assets = await self.list_brand_kit_assets(kit.id)
        for asset in assets:
            await self.session.delete(asset)
        await self.session.delete(kit)
        await self.session.commit()

    async def set_brand_kit_status(self, kit: BrandKit, status: str) -> BrandKit:
        kit.status = status
        await self.session.commit()
        await self.session.refresh(kit)
        return kit

    async def sync_brand_kit_status(self, kit: BrandKit) -> BrandKit:
        assets = await self.list_brand_kit_assets(kit.id)
        statuses = {item.status for item in assets}
        if assets and statuses == {"FAILED"}:
            status = "FAILED"
        elif assets and statuses.issubset({"SUCCESS", "FAILED"}) and "SUCCESS" in statuses:
            status = "SUCCESS"
        elif assets and statuses == {"SUCCESS"}:
            status = "SUCCESS"
        else:
            status = "PROCESSING"
        return await self.set_brand_kit_status(kit, status)

    async def brand_kit_payload(self, kit: BrandKit) -> dict:
        assets = await self.list_brand_kit_assets(kit.id)
        return {
            "id": kit.id,
            "naming_asset_id": kit.naming_asset_id,
            "name": kit.name,
            "moral": kit.moral,
            "industry": kit.industry,
            "audience": kit.audience,
            "design_style": kit.design_style,
            "primary_color": kit.primary_color,
            "slogan": kit.slogan,
            "status": kit.status,
            "assets": assets,
            "created_time": kit.created_time,
        }

    async def update_visual_status(
            self,
            visual: BrandVisual,
            status: str,
            image_url: str | None = None,
            task_id: str | None = None,
            image_path: str | None = None,
            error_message: str | None = None,
    ) -> BrandVisual:
        visual.status = status
        if image_url:
            visual.image_url = image_url
        if task_id:
            visual.task_id = task_id
        if image_path:
            visual.image_path = image_path
        visual.error_message = error_message
        await self.session.commit()
        await self.session.refresh(visual)
        return visual
