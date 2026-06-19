from langchain_deepseek import ChatDeepSeek

import settings
from core.aigc_tools import fetch_visual_task, normalize_aigc_status, submit_visual_task
from models.visual import BrandVisual
from repository.visual_repo import BrandVisualRepository
from schemas.visual_schemas import SloganAndPromptSchema, VisualGenerateIn


def _fallback_slogan_prompt(data: VisualGenerateIn) -> SloganAndPromptSchema:
    slogan = f"{data.name}，让灵感成真"
    prompt = (
        f"Brand logo and business card concept for '{data.name}', "
        f"meaning: {data.moral or 'elegant brand identity'}, "
        f"style: {data.design_style}, clean commercial visual identity, "
        "premium typography, balanced composition, professional mockup, --v 6.0 --ar 16:9"
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
请结构化输出以下两项内容：
1. slogan：一句简短、押韵、有记忆点的品牌口号（限15字内）。
2. mj_prompt：一段用于Midjourney生成品牌Logo和名片概念图的高质量英文提示词。包含视觉主体、色彩搭配、风格描述和渲染参数（如 --v 6.0 --ar 16:9）。
"""
    try:
        return await structured_llm.ainvoke(prompt)
    except Exception:
        return _fallback_slogan_prompt(data)


async def create_brand_visual(
        data: VisualGenerateIn,
        user_id: int,
        repository: BrandVisualRepository
) -> BrandVisual:
    slogan_prompt = await generate_slogan_and_prompt(data)
    visual = BrandVisual(
        user_id=user_id,
        thread_id=data.thread_id,
        name=data.name,
        category=data.category,
        moral=data.moral,
        design_style=data.design_style,
        slogan=slogan_prompt.slogan,
        prompt_used=slogan_prompt.mj_prompt,
        status="PENDING",
    )
    visual = await repository.create_visual(visual)

    try:
        task = await submit_visual_task(slogan_prompt.mj_prompt)
    except Exception:
        return await repository.update_visual_status(visual, status="FAILED")

    return await repository.update_visual_status(
        visual,
        status=task.status,
        task_id=task.task_id,
        image_url=task.image_url,
    )


async def refresh_brand_visual_status(
        visual: BrandVisual,
        repository: BrandVisualRepository
) -> BrandVisual:
    if visual.status in {"SUCCESS", "FAILED"} or not visual.task_id:
        return visual

    try:
        task = await fetch_visual_task(visual.task_id)
    except Exception:
        return visual

    return await repository.update_visual_status(
        visual,
        status=normalize_aigc_status(task.status),
        image_url=task.image_url,
    )
