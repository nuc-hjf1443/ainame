from typing import Literal

from pydantic import BaseModel, Field


VisualCategory = Literal["人名", "企业名", "宠物名"]
VisualStatus = Literal["PENDING", "PROCESSING", "SUCCESS", "FAILED"]


class VisualGenerateIn(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100, description="关联的上下文Thread ID")
    name: str = Field(..., min_length=1, max_length=100, description="选定的名字")
    moral: str = Field("", max_length=2000, description="名字的寓意")
    category: VisualCategory = Field(..., description="分类")
    design_style: str = Field(default="现代极简商业风", max_length=100, description="期望的视觉设计风格")


class VisualGenerateOut(BaseModel):
    visual_id: int = Field(..., description="内部记录ID")
    task_id: str = Field(..., description="第三方绘画任务ID")
    slogan: str = Field(..., description="AI生成的品牌Slogan")
    status: VisualStatus = Field(..., description="当前状态")


class VisualStatusOut(BaseModel):
    visual_id: int
    status: VisualStatus
    image_url: str | None = None
    slogan: str | None = None


class SloganAndPromptSchema(BaseModel):
    slogan: str = Field(..., description="一句简短、押韵、有记忆点的中文品牌口号，15字以内")
    mj_prompt: str = Field(..., description="用于图像生成的英文品牌视觉提示词")
