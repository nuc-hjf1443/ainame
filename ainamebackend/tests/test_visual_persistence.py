from datetime import date

import httpx
import pytest

from services import visual_service
from services.brand_kit_service import prepare_brand_kit
from models.asset import NamingAsset
from models.user import User
from repository.visual_repo import BrandVisualRepository
from schemas.visual_schemas import BrandKitCreateIn


@pytest.mark.asyncio
async def test_persist_visual_image(monkeypatch, tmp_path):
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, headers={"content-type": "image/png"}, content=b"png-data"))
    monkeypatch.setattr(visual_service.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(visual_service, "VISUAL_DIR", tmp_path)
    monkeypatch.setattr(visual_service.settings, "PUBLIC_BASE_URL", "http://test")
    monkeypatch.setattr(visual_service.settings, "VISUAL_MAX_FILE_SIZE", 1024)

    url, path = await visual_service.persist_visual_image("http://source/image", 7)

    assert url.startswith("http://test/uploads/visuals/7/")
    assert tmp_path.joinpath("7", path.split("\\")[-1]).exists()


@pytest.mark.asyncio
async def test_rejects_oversized_visual(monkeypatch, tmp_path):
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, headers={"content-type": "image/png"}, content=b"too-large"))
    monkeypatch.setattr(visual_service.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(visual_service, "VISUAL_DIR", tmp_path)
    monkeypatch.setattr(visual_service.settings, "VISUAL_MAX_FILE_SIZE", 3)
    with pytest.raises(ValueError, match="10 MB"):
        await visual_service.persist_visual_image("http://source/image", 7)


@pytest.mark.asyncio
async def test_brand_kit_prepares_two_logos_and_two_business_cards(session):
    user = User(email="brand-kit@test.local", username="brand-kit", _password="test")
    session.add(user)
    await session.commit()
    data = BrandKitCreateIn(
        thread_id="brand-thread",
        name="靶心互娱",
        moral="精准命中目标，为玩家带来射击娱乐体验",
        industry="射击小游戏公司",
        audience="年轻游戏玩家",
        design_style="现代简约",
        primary_color="蓝色",
    )

    repository = BrandVisualRepository(session)
    kit = await prepare_brand_kit(data, user.id, repository, date(2026, 6, 23))
    payload = await repository.brand_kit_payload(kit)

    assert payload["status"] == "PENDING"
    assert len(payload["assets"]) == 4
    assert [asset.asset_type for asset in payload["assets"]].count("LOGO") == 2
    assert [asset.asset_type for asset in payload["assets"]].count("BUSINESS_CARD") == 2
    assert all(asset.brand_kit_id == kit.id for asset in payload["assets"])
    assert kit.quota_usage_date == date(2026, 6, 23)


@pytest.mark.asyncio
async def test_brand_kit_links_naming_asset_and_can_be_listed_and_deleted(session):
    user = User(email="brand-kit-link@test.local", username="brand-kit-link", _password="test")
    session.add(user)
    await session.flush()
    asset = NamingAsset(
        user_id=user.id,
        thread_id="brand-thread-linked",
        name="芯擎",
        category="企业名",
        moral="芯片引擎，驱动未来科技。",
        reference="测试资产",
    )
    session.add(asset)
    await session.commit()

    data = BrandKitCreateIn(
        naming_asset_id=asset.id,
        thread_id=asset.thread_id,
        name=asset.name,
        moral=asset.moral,
        industry="芯片公司",
        audience="B端客户",
        design_style="现代简约",
        primary_color="蓝色",
    )
    repository = BrandVisualRepository(session)
    kit = await prepare_brand_kit(data, user.id, repository, date(2026, 6, 23))
    kits, total = await repository.list_user_brand_kits(user.id, 1, 20)
    payload = await repository.brand_kit_payload(kit)

    assert total == 1
    assert kits[0].id == kit.id
    assert payload["naming_asset_id"] == asset.id
    assert len(payload["assets"]) == 4

    await repository.delete_brand_kit(kit)
    kits, total = await repository.list_user_brand_kits(user.id, 1, 20)
    assert total == 0
    assert kits == []
    assert await repository.list_brand_kit_assets(kit.id) == []
