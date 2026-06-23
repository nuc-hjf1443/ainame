from langchain_deepseek import ChatDeepSeek

import settings
from schemas.marketplace_schemas import ReportIn


async def generate_expert_report_draft(name: str, moral: str | None, requirements: str, expert_type: str) -> ReportIn:
    fallback = ReportIn(
        overview=f"本报告围绕“{name}”进行综合评估。",
        professional_analysis=f"结合{moral or '现有命名信息'}，从专业领域分析其定位与内涵。",
        phonetic_semantic_analysis="建议进一步核对读音、字形辨识度与核心语义的一致性。",
        communication_advantages="名称简洁度和记忆点需要结合目标受众与使用场景验证。",
        risk_notes="正式使用前应完成商标、工商名称或重名风险查询。",
        recommendations=f"围绕客户需求“{requirements}”继续优化应用语境与视觉表达。",
        conclusion="该名称具备进一步深化的基础，最终结论应由专家结合实际资料修订。",
    )
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_deepseek_api_key":
        return fallback
    llm = ChatDeepSeek(model="deepseek-chat", api_key=settings.DEEPSEEK_API_KEY, temperature=0.4)
    structured = llm.with_structured_output(ReportIn, method="json_mode")
    prompt = f"""你是平台入驻的命名专家。请只返回 JSON，为名字“{name}”生成可编辑的专业报告草稿。
专家类型：{expert_type}；名字寓意：{moral or '未提供'}；客户要求：{requirements}。
JSON 必须包含 overview、professional_analysis、phonetic_semantic_analysis、communication_advantages、risk_notes、recommendations、conclusion 七个字符串字段。"""
    try:
        result = await structured.ainvoke(prompt)
        return ReportIn.model_validate(result) if result else fallback
    except Exception:
        return fallback
