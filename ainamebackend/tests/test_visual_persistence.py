from datetime import date

import httpx
import pytest
from sqlalchemy import select

from services import brand_kit_service, visual_service
from core import aigc_tools
from services.brand_kit_service import prepare_brand_kit
from models.asset import NamingAsset
from models.finance import DailyQuotaUsage
from models.user import User
from repository.visual_repo import BrandVisualRepository
from models.visual import BrandKit, BrandVisual
from schemas.visual_schemas import BrandKitCreateIn
from services.quota_service import current_usage_date


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
async def test_persist_visual_image_retries_incomplete_chunked_read(monkeypatch, tmp_path):
    original_client = httpx.AsyncClient
    attempts = {"count": 0}

    def handler(request):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.RemoteProtocolError(
                "peer closed connection without sending complete message body (incomplete chunked read)"
            )
        return httpx.Response(200, headers={"content-type": "image/png"}, content=b"png-data")

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(visual_service.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(visual_service, "VISUAL_DIR", tmp_path)
    monkeypatch.setattr(visual_service.settings, "PUBLIC_BASE_URL", "http://test")
    monkeypatch.setattr(visual_service.settings, "VISUAL_MAX_FILE_SIZE", 1024)
    monkeypatch.setattr(visual_service.settings, "AIGC_NETWORK_RETRY_ATTEMPTS", 2)

    url, path = await visual_service.persist_visual_image("http://source/image", 7)

    assert attempts["count"] == 2
    assert url.startswith("http://test/uploads/visuals/7/")
    assert tmp_path.joinpath("7", path.split("\\")[-1]).exists()


@pytest.mark.asyncio
async def test_persist_visual_image_uses_chinese_message_after_retries(monkeypatch, tmp_path):
    original_client = httpx.AsyncClient

    def handler(request):
        raise httpx.RemoteProtocolError(
            "peer closed connection without sending complete message body (incomplete chunked read)"
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(visual_service.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(visual_service, "VISUAL_DIR", tmp_path)
    monkeypatch.setattr(visual_service.settings, "AIGC_NETWORK_RETRY_ATTEMPTS", 2)

    with pytest.raises(RuntimeError, match="视觉生成服务连接中断"):
        await visual_service.persist_visual_image("http://source/image", 7)


@pytest.mark.asyncio
async def test_wanx_v1_uses_dashscope_async_image_synthesis(monkeypatch):
    original_client = httpx.AsyncClient
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["payload"] = request.content.decode("utf-8")
        captured["async_header"] = request.headers.get("X-DashScope-Async")
        return httpx.Response(200, json={"output": {"task_id": "task-wanx", "task_status": "PENDING"}})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(aigc_tools.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(aigc_tools.settings, "AIGC_API_KEY", "test-key")
    monkeypatch.setattr(aigc_tools.settings, "AIGC_IMAGE_SYNTHESIS_URL", "https://dashscope.test/image-synthesis")

    result = await aigc_tools.submit_visual_task("brand logo", "wanx-v1")

    assert result.task_id == "task-wanx"
    assert result.status == "PENDING"
    assert captured["url"] == "https://dashscope.test/image-synthesis"
    assert captured["async_header"] == "enable"
    assert '"model":"wanx-v1"' in captured["payload"].replace(" ", "")


@pytest.mark.asyncio
async def test_wan27_image_uses_multimodal_generation(monkeypatch):
    original_client = httpx.AsyncClient
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["payload"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            headers={"X-Request-Id": "request-wan27"},
            json={
                "output": {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "image", "image": "https://example.test/generated.png"}
                                ]
                            }
                        }
                    ]
                }
            },
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(aigc_tools.httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    monkeypatch.setattr(aigc_tools.settings, "AIGC_API_KEY", "test-key")
    monkeypatch.setattr(aigc_tools.settings, "AIGC_WAN_IMAGE_URL", "https://dashscope.test/multimodal")

    result = await aigc_tools.submit_visual_task("brand logo", "wan2.7-image")

    assert result.task_id == "request-wan27"
    assert result.status == "SUCCESS"
    assert result.image_url == "https://example.test/generated.png"
    assert captured["url"] == "https://dashscope.test/multimodal"
    compact_payload = captured["payload"].replace(" ", "")
    assert '"model":"wan2.7-image"' in compact_payload
    assert '"size":"1K"' in compact_payload
    assert '"thinking_mode":false' in compact_payload


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
async def test_brand_kit_prepares_one_logo_and_one_business_card(session):
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
    assert len(payload["assets"]) == 2
    assert [asset.asset_type for asset in payload["assets"]].count("LOGO") == 1
    assert [asset.asset_type for asset in payload["assets"]].count("BUSINESS_CARD") == 1
    assert all(asset.brand_kit_id == kit.id for asset in payload["assets"])
    assert kit.quota_usage_date == date(2026, 6, 23)


@pytest.mark.asyncio
async def test_brand_kit_payload_repairs_missing_public_image_url(session, monkeypatch, tmp_path):
    user = User(email="brand-kit-path@test.local", username="brand-kit-path", _password="test")
    session.add(user)
    await session.commit()

    visual_root = tmp_path / "uploads" / "visuals"
    image_path = visual_root / str(user.id) / "generated.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"png")

    monkeypatch.setattr("repository.visual_repo.VISUAL_ROOT", visual_root)
    monkeypatch.setattr("repository.visual_repo.settings.PUBLIC_BASE_URL", "http://test")

    kit = BrandKit(
        user_id=user.id,
        thread_id="brand-thread-path",
        name="PathKit",
        moral="",
        industry="games",
        audience="players",
        design_style="modern",
        primary_color="blue",
        image_model="wan2.7-image",
        slogan="PathKit",
        status="SUCCESS",
    )
    visual = BrandVisual(
        user_id=user.id,
        thread_id="brand-thread-path",
        name="PathKit",
        category="企业名",
        design_style="modern",
        image_model="wan2.7-image",
        asset_type="LOGO",
        variant_index=1,
        status="SUCCESS",
        image_url="https://expired.example.test/generated.png",
        image_path=str(image_path),
    )

    repository = BrandVisualRepository(session)
    kit = await repository.create_brand_kit(kit, [visual])
    payload = await repository.brand_kit_payload(kit)

    assert payload["assets"][0].image_url == f"http://test/uploads/visuals/{user.id}/generated.png"


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
    assert len(payload["assets"]) == 2

    await repository.delete_brand_kit(kit)
    kits, total = await repository.list_user_brand_kits(user.id, 1, 20)
    assert total == 0
    assert kits == []
    assert await repository.list_brand_kit_assets(kit.id) == []


@pytest.mark.asyncio
async def test_failed_brand_kit_generation_keeps_failed_assets_for_regeneration(session, monkeypatch):
    user = User(email="brand-kit-fail@test.local", username="brand-kit-fail", _password="test")
    session.add(user)
    await session.commit()
    usage = DailyQuotaUsage(user_id=user.id, usage_date=current_usage_date(), visual_used=1)
    session.add(usage)
    await session.commit()

    data = BrandKitCreateIn(
        thread_id="brand-thread-fail",
        name="启明",
        moral="开启光明",
        industry="品牌咨询",
        audience="创业团队",
        design_style="现代简约",
        primary_color="蓝色",
    )
    repository = BrandVisualRepository(session)
    kit = await prepare_brand_kit(data, user.id, repository, current_usage_date())

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def fail_submit(prompt, image_model):
        raise RuntimeError("mock generation failure")

    monkeypatch.setattr(brand_kit_service, "AsyncSessionFactory", lambda: SessionContext())
    monkeypatch.setattr(brand_kit_service, "submit_visual_task", fail_submit)

    await brand_kit_service.process_brand_kit(kit.id, user.id)

    saved_kit = await session.scalar(select(BrandKit).where(BrandKit.id == kit.id))
    failed_assets = (await session.scalars(select(BrandVisual).where(BrandVisual.brand_kit_id == kit.id))).all()

    assert saved_kit is not None
    assert saved_kit.status == "FAILED"
    assert len(failed_assets) == 2
    assert {asset.status for asset in failed_assets} == {"FAILED"}
    assert all(asset.error_message for asset in failed_assets)
    await session.refresh(usage)
    assert usage.visual_used == 1
