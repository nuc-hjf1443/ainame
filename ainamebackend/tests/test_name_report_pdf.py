from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfReader

from models.asset import NamingAsset
from models.user import User
from models.visual import BrandKit, BrandVisual
from repository.asset_repo import AssetRepository
from routers.asset_router import download_name_report


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@pytest.mark.asyncio
async def test_download_name_report_without_brand_kit(session):
    user = User(email="report@test.local", username="report-user", _password="test")
    session.add(user)
    await session.commit()
    asset = await AssetRepository(session).create_name(user.id, {
        "thread_id": "report-thread",
        "name": "Qiming",
        "category": "企业名",
        "moral": "Open and bright brand direction",
        "reference": "Inspired by brightness",
        "domain": "qiming.com",
        "domain_status": "available",
    })

    response = await download_name_report(asset.id, user=user, session=session)
    text = extract_pdf_text(response.body)

    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == f'attachment; filename="name-report-{asset.id}.pdf"'
    assert "Qiming" in text
    assert "qiming.com" in text
    assert "Open and bright brand direction" in text


@pytest.mark.asyncio
async def test_download_name_report_rejects_other_user_asset(session):
    owner = User(email="owner-report@test.local", username="owner", _password="test")
    other = User(email="other-report@test.local", username="other", _password="test")
    session.add_all([owner, other])
    await session.commit()
    asset = await AssetRepository(session).create_name(owner.id, {
        "thread_id": "owner-thread",
        "name": "PrivateName",
        "category": "企业名",
        "moral": None,
        "reference": None,
        "domain": None,
        "domain_status": None,
    })

    with pytest.raises(HTTPException) as exc:
        await download_name_report(asset.id, user=other, session=session)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_download_name_report_uses_linked_brand_kit(monkeypatch, tmp_path, session):
    import services.name_report_service as report_service

    monkeypatch.setattr(report_service.settings, "BASE_DIR", tmp_path)
    logo_path = tmp_path / "uploads" / "visuals" / "1" / "logo.png"
    logo_path.parent.mkdir(parents=True)
    Image.new("RGB", (24, 24), color=(34, 92, 180)).save(logo_path)

    user = User(email="kit-report@test.local", username="kit-report", _password="test")
    session.add(user)
    await session.flush()
    asset = NamingAsset(
        user_id=user.id,
        thread_id="kit-thread",
        name="BrightKit",
        category="企业名",
        moral="A confident brand name",
        reference="Brand strategy source",
        domain="brightkit.com",
        domain_status="available",
    )
    session.add(asset)
    await session.flush()
    kit = BrandKit(
        user_id=user.id,
        naming_asset_id=asset.id,
        thread_id=asset.thread_id,
        name=asset.name,
        moral=asset.moral,
        industry="Software",
        audience="Teams",
        design_style="Modern",
        primary_color="Blue",
        slogan="BrightKit makes naming clear",
        status="SUCCESS",
    )
    session.add(kit)
    await session.flush()
    session.add(BrandVisual(
        user_id=user.id,
        brand_kit_id=kit.id,
        thread_id=asset.thread_id,
        name=asset.name,
        category=asset.category,
        moral=asset.moral,
        asset_type="LOGO",
        variant_index=1,
        slogan=kit.slogan,
        image_path=str(Path(logo_path)),
        image_url="http://test/uploads/visuals/1/logo.png",
        status="SUCCESS",
    ))
    await session.commit()

    response = await download_name_report(asset.id, user=user, session=session)
    text = extract_pdf_text(response.body)

    assert "BrightKit" in text
    assert "BrightKit makes naming clear" in text
    assert "Modern" in text
