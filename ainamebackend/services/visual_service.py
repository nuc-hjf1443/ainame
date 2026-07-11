import asyncio
import logging
import uuid
from datetime import date
from pathlib import Path

import httpx
from langchain_deepseek import ChatDeepSeek

import settings
from core.aigc_tools import (
    fetch_visual_task,
    is_transient_aigc_error,
    normalize_aigc_status,
    submit_visual_task,
    visual_error_message,
)
from models.visual import BrandVisual
from repository.visual_repo import BrandVisualRepository
from schemas.visual_schemas import SloganAndPromptSchema, VisualGenerateIn


logger = logging.getLogger(__name__)
VISUAL_DIR = settings.BASE_DIR / "uploads" / "visuals"
IMAGE_EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


async def _persist_visual_image_once(source_url: str, user_id: int) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        async with client.stream("GET", source_url) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
            extension = IMAGE_EXTENSIONS.get(content_type)
            if not extension:
                raise ValueError("视觉服务返回的不是受支持图片")
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > settings.VISUAL_MAX_FILE_SIZE:
                    raise ValueError("生成图片超过 10 MB 限制")
                chunks.append(chunk)

    relative_path = Path(str(user_id)) / f"{uuid.uuid4().hex}{extension}"
    target = VISUAL_DIR / relative_path
    await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(target.write_bytes, b"".join(chunks))
    public_url = f"{settings.PUBLIC_BASE_URL}/uploads/visuals/{relative_path.as_posix()}"
    return public_url, str(target)


async def persist_visual_image(source_url: str, user_id: int) -> tuple[str, str]:
    attempts = settings.AIGC_NETWORK_RETRY_ATTEMPTS
    for attempt in range(1, attempts + 1):
        try:
            return await _persist_visual_image_once(source_url, user_id)
        except Exception as exc:
            if not is_transient_aigc_error(exc) or attempt >= attempts:
                if is_transient_aigc_error(exc):
                    raise RuntimeError(visual_error_message(exc)) from exc
                raise
            logger.warning(
                "Generated visual image download interrupted; retrying attempt %s/%s",
                attempt,
                attempts,
                exc_info=True,
            )
            await asyncio.sleep(min(2.0, 0.6 * attempt))

    raise RuntimeError("视觉生成服务连接中断，请稍后刷新状态或重新生成")


def _fallback_slogan_prompt(data: VisualGenerateIn) -> SloganAndPromptSchema:
    slogan = f"{data.name}，让灵感成真"
    prompt = (
        f"Brand logo and business card concept for '{data.name}', "
        f"meaning: {data.moral or 'elegant brand identity'}, "
        f"style: {data.design_style}, image model: {data.image_model}, clean commercial visual identity, "
        "premium typography, balanced square composition, professional mockup, "
        "1:1 aspect ratio, no watermark, no model-specific command parameters"
    )
    return SloganAndPromptSchema(slogan=slogan[:15], mj_prompt=prompt)


async def generate_slogan_and_prompt(data: VisualGenerateIn) -> SloganAndPromptSchema:
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_deepseek_api_key":
        return _fallback_slogan_prompt(data)

    llm = ChatDeepSeek(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.5,
    )
    structured_llm = llm.with_structured_output(SloganAndPromptSchema).with_retry(stop_after_attempt=3)
    prompt = f"""
你是一个顶尖的品牌策划师和UI/UX视觉设计师。现在客户选定了一个名字：{data.name}，其寓意是：{data.moral}。
客户期望的设计风格是：{data.design_style}。
客户选择的图像生成模型是：{data.image_model}。
请结构化输出以下两项内容：
1. slogan：一句简短、押韵、有记忆点的品牌口号（限15字内）。
2. mj_prompt：一段用于 wan2.6-image 生成品牌Logo和名片概念图的高质量英文提示词。包含视觉主体、色彩搭配、风格描述，并明确使用1:1方形构图。不要包含 --v、--ar 等模型命令参数。
"""
    try:
        return await structured_llm.ainvoke(prompt)
    except Exception:
        return _fallback_slogan_prompt(data)


async def create_brand_visual(
        data: VisualGenerateIn,
        user_id: int,
        repository: BrandVisualRepository,
        quota_usage_date: date,
) -> BrandVisual:
    slogan_prompt = await generate_slogan_and_prompt(data)
    visual = BrandVisual(
        user_id=user_id,
        thread_id=data.thread_id,
        name=data.name,
        category=data.category,
        moral=data.moral,
        design_style=data.design_style,
        image_model=data.image_model,
        slogan=slogan_prompt.slogan,
        prompt_used=slogan_prompt.mj_prompt,
        status="PENDING",
        quota_usage_date=quota_usage_date,
    )
    visual = await repository.create_visual(visual)

    try:
        task = await submit_visual_task(slogan_prompt.mj_prompt, data.image_model)
        image_url, image_path = task.image_url, None
        if task.status == "SUCCESS":
            if not task.image_url:
                raise ValueError("视觉服务未返回图片地址")
            image_url, image_path = await persist_visual_image(task.image_url, user_id)
    except Exception as exc:
        logger.warning("Brand visual generation failed for visual_id=%s", visual.id, exc_info=True)
        return await repository.update_visual_status(visual, status="FAILED", error_message=visual_error_message(exc)[:1000])

    return await repository.update_visual_status(
        visual,
        status=task.status,
        task_id=task.task_id,
        image_url=image_url,
        image_path=image_path,
    )


async def refresh_brand_visual_status(
        visual: BrandVisual,
        repository: BrandVisualRepository
) -> BrandVisual:
    if visual.status in {"SUCCESS", "FAILED"} or not visual.task_id:
        return visual

    try:
        task = await fetch_visual_task(visual.task_id)
        image_url, image_path = task.image_url, None
        if task.status == "SUCCESS":
            if not task.image_url:
                raise ValueError("视觉服务未返回图片地址")
            image_url, image_path = await persist_visual_image(task.image_url, visual.user_id)
    except Exception as exc:
        if visual.status == "PROCESSING":
            logger.warning("Brand visual refresh failed for visual_id=%s", visual.id, exc_info=True)
            return await repository.update_visual_status(visual, status="FAILED", error_message=visual_error_message(exc)[:1000])
        return visual

    return await repository.update_visual_status(
        visual,
        status=normalize_aigc_status(task.status),
        image_url=image_url,
        image_path=image_path,
    )
