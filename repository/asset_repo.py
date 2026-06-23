from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import NamingAsset
from models.visual import BrandVisual


class AssetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_name(self, user_id: int, values: dict, *, commit: bool = True) -> NamingAsset:
        asset = NamingAsset(user_id=user_id, **values)
        self.session.add(asset)
        if commit:
            await self.session.commit()
            await self.session.refresh(asset)
        else:
            await self.session.flush()
        return asset

    async def get_name(self, asset_id: int, user_id: int) -> NamingAsset | None:
        result = await self.session.execute(select(NamingAsset).where(NamingAsset.id == asset_id, NamingAsset.user_id == user_id))
        return result.scalar_one_or_none()

    async def delete_name(self, asset: NamingAsset) -> None:
        await self.session.delete(asset)
        await self.session.commit()

    async def list_names(self, user_id: int, page: int, page_size: int):
        where = NamingAsset.user_id == user_id
        total = await self.session.scalar(select(func.count()).select_from(NamingAsset).where(where)) or 0
        result = await self.session.execute(select(NamingAsset).where(where).order_by(NamingAsset.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return result.scalars().all(), total

    async def list_visuals(self, user_id: int, page: int, page_size: int):
        where = BrandVisual.user_id == user_id
        total = await self.session.scalar(select(func.count()).select_from(BrandVisual).where(where)) or 0
        result = await self.session.execute(select(BrandVisual).where(where).order_by(BrandVisual.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return result.scalars().all(), total
