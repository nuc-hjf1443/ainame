from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.visual import BrandVisual


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

    async def update_visual_status(
            self,
            visual: BrandVisual,
            status: str,
            image_url: str | None = None,
            task_id: str | None = None
    ) -> BrandVisual:
        visual.status = status
        if image_url:
            visual.image_url = image_url
        if task_id:
            visual.task_id = task_id
        await self.session.commit()
        await self.session.refresh(visual)
        return visual
