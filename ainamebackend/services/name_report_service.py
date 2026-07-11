from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import settings
from models.asset import NamingAsset
from models.visual import BrandKit, BrandVisual


DEFAULT_FONT_NAME = "AinameReportFont"
DEFAULT_BOLD_FONT_NAME = "AinameReportFontBold"
FALLBACK_CID_FONT = "STSong-Light"

FONT_CANDIDATES = (
    "C:/Windows/Fonts/Noto Sans SC (TrueType).otf",
    "C:/Windows/Fonts/NotoSansSC-VF.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)
BOLD_FONT_CANDIDATES = (
    "C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)


def _font_registered(name: str) -> bool:
    try:
        pdfmetrics.getFont(name)
        return True
    except KeyError:
        return False


def _register_ttf_font(name: str, configured_path: str, candidates: tuple[str, ...]) -> str | None:
    if _font_registered(name):
        return name
    paths = [configured_path, *candidates] if configured_path else list(candidates)
    for value in paths:
        if not value:
            continue
        path = Path(value)
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
        except Exception:
            continue
    return None


def _register_report_fonts() -> tuple[str, str]:
    regular = _register_ttf_font(DEFAULT_FONT_NAME, settings.PDF_FONT_PATH, FONT_CANDIDATES)
    bold = _register_ttf_font(DEFAULT_BOLD_FONT_NAME, settings.PDF_FONT_BOLD_PATH, BOLD_FONT_CANDIDATES)
    if regular:
        return regular, bold or regular

    if not _font_registered(FALLBACK_CID_FONT):
        pdfmetrics.registerFont(UnicodeCIDFont(FALLBACK_CID_FONT))
    return FALLBACK_CID_FONT, FALLBACK_CID_FONT


def _text(value: object, fallback: str = "-") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def _paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    text = escape(_text(value)).replace("\n", "<br/>")
    return Paragraph(text, style)


def _section(title: str, body: object, styles: dict[str, ParagraphStyle]) -> list:
    return [
        Paragraph(escape(title), styles["section_title"]),
        _paragraph(body, styles["body"]),
        Spacer(1, 5 * mm),
    ]


def _safe_logo_path(assets: list[BrandVisual]) -> Path | None:
    for asset in assets:
        if asset.asset_type != "LOGO" or asset.status != "SUCCESS" or not asset.image_path:
            continue
        path = Path(asset.image_path)
        try:
            resolved = path.resolve()
            visual_root = (settings.BASE_DIR / "uploads" / "visuals").resolve()
            if resolved.exists() and resolved.is_file() and resolved.is_relative_to(visual_root):
                return resolved
        except Exception:
            continue
    return None


def _logo_image(path: Path | None) -> Image | None:
    if not path:
        return None
    try:
        ImageReader(str(path)).getRGBData()
        image = Image(str(path))
        image._restrictSize(72 * mm, 72 * mm)
        return image
    except Exception:
        return None


def _logo_concept(asset: NamingAsset, kit: BrandKit | None, logo_path: Path | None) -> str:
    if kit and logo_path:
        return (
            f"围绕“{asset.name}”的名称识别建立主视觉，结合“{_text(kit.design_style)}”风格与"
            f"“{_text(kit.primary_color)}”主色，已嵌入一版可用 Logo 素材作为交付参考。"
        )
    if kit:
        return (
            f"建议围绕“{asset.name}”的首字、核心寓意或行业符号建立 Logo 识别，视觉方向为"
            f"“{_text(kit.design_style)}”，主色建议使用“{_text(kit.primary_color)}”。"
        )
    return (
        f"建议从“{asset.name}”的字形、寓意和目标行业中提取核心符号，形成简洁、易识别、"
        "可用于头像、门店招牌和线上传播的 Logo 概念。"
    )


def _risk_notes(asset: NamingAsset, kit: BrandKit | None) -> list[str]:
    notes = [
        "正式使用前应进行商标近似检索、工商字号核验和行业合规审查。",
    ]
    domain_status = _text(asset.domain_status, "")
    if asset.domain:
        if any(keyword in domain_status for keyword in ("抢注", "不可", "占用", "taken", "unavailable", "❌")):
            notes.append("当前域名状态提示存在占用风险，建议准备 2-3 个备选域名。")
        elif domain_status:
            notes.append("域名状态仅供命名阶段参考，注册前仍需以域名服务商实时查询为准。")
    else:
        notes.append("当前未形成明确域名建议，企业名落地前应补充官网与社媒账号可用性核验。")
    if not asset.moral:
        notes.append("当前寓意说明较少，传播物料中需要补充更明确的品牌解释。")
    if not asset.reference:
        notes.append("当前出处信息较少，如用于文化型命名，应补充可验证来源。")
    if not kit:
        notes.append("当前未生成品牌视觉方案，Logo、名片和色彩系统仍需单独设计确认。")
    return notes


def _page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_name_report_pdf(
        asset: NamingAsset,
        *,
        brand_kit: BrandKit | None = None,
        brand_assets: list[BrandVisual] | None = None,
        generated_at: datetime | None = None,
) -> bytes:
    font_name, bold_font_name = _register_report_fonts()
    styles = getSampleStyleSheet()
    report_styles = {
        "title": ParagraphStyle(
            "AinameReportTitle",
            parent=styles["Title"],
            fontName=bold_font_name,
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#111827"),
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "AinameReportSubtitle",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#667085"),
            alignment=TA_CENTER,
            spaceAfter=10 * mm,
        ),
        "section_title": ParagraphStyle(
            "AinameReportSectionTitle",
            parent=styles["Heading2"],
            fontName=bold_font_name,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "AinameReportBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            textColor=colors.HexColor("#374151"),
        ),
        "small": ParagraphStyle(
            "AinameReportSmall",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#667085"),
        ),
    }

    generated_at = generated_at or datetime.now()
    brand_assets = brand_assets or []
    logo_path = _safe_logo_path(brand_assets)
    logo_preview = _logo_image(logo_path)
    embedded_logo_path = logo_path if logo_preview else None
    slogan = brand_kit.slogan if brand_kit and brand_kit.slogan else f"{asset.name}，让好名字被看见"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{asset.name} 命名报告",
        author="ainame",
    )

    story: list = [
        Paragraph("命名结果交付报告", report_styles["title"]),
        Paragraph(
            f"生成时间：{generated_at.strftime('%Y-%m-%d %H:%M')}  |  报告编号：NAME-{asset.id}",
            report_styles["subtitle"],
        ),
    ]

    summary_data = [
        [
            _paragraph("最终选名", report_styles["body"]),
            _paragraph(asset.name, report_styles["body"]),
            _paragraph("名称分类", report_styles["body"]),
            _paragraph(asset.category, report_styles["body"]),
        ],
        [
            _paragraph("推荐域名", report_styles["body"]),
            _paragraph(asset.domain, report_styles["body"]),
            _paragraph("域名状态", report_styles["body"]),
            _paragraph(asset.domain_status, report_styles["body"]),
        ],
        [
            _paragraph("推荐 Slogan", report_styles["body"]),
            _paragraph(slogan, report_styles["body"]),
            _paragraph("视觉方案", report_styles["body"]),
            _paragraph(brand_kit.status if brand_kit else "未生成", report_styles["body"]),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[25 * mm, 63 * mm, 25 * mm, 63 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([summary_table, Spacer(1, 7 * mm)])

    story.extend(_section("命名寓意", asset.moral, report_styles))
    story.extend(_section("寓意出处", asset.reference, report_styles))
    story.extend(_section("域名建议", f"{_text(asset.domain)}（{_text(asset.domain_status)}）", report_styles))
    story.extend(_section("Slogan", slogan, report_styles))
    story.extend(_section("Logo 概念", _logo_concept(asset, brand_kit, embedded_logo_path), report_styles))

    if logo_preview:
        story.append(Paragraph("Logo 素材预览", report_styles["section_title"]))
        story.extend([logo_preview, Spacer(1, 5 * mm)])

    risk_items = "<br/>".join(f"{index}. {escape(note)}" for index, note in enumerate(_risk_notes(asset, brand_kit), start=1))
    story.extend([
        Paragraph("风险提示", report_styles["section_title"]),
        Paragraph(risk_items, report_styles["body"]),
        Spacer(1, 5 * mm),
    ])
    story.append(Paragraph("本报告用于命名方案内部评估与交付沟通，不构成商标、工商或法律可用性承诺。", report_styles["small"]))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return buffer.getvalue()
