from datetime import date

import httpx
import pytest

from core import visual_service
from core.brand_kit_service import prepare_brand_kit
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
