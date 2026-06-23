from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


VisualCategory = Literal["人名", "企业名", "宠物名"]
VisualStatus = Literal["PENDING", "PROCESSING", "SUCCESS", "FAILED"]
VisualImageModel = Literal["wan2.6-image"]


class VisualGenerateIn(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100, description="关联的上下文Thread ID")
    name: str = Field(..., min_length=1, max_length=100, description="选定的名字")
    moral: str = Field("", max_length=2000, description="名字的寓意")
    category: VisualCategory = Field(..., description="分类")
    design_style: str = Field(default="现代极简商业风", max_length=100, description="期望的视觉设计风格")
    image_model: VisualImageModel = Field(default="wan2.6-image", description="图像生成模型")


class VisualGenerateOut(BaseModel):
    visual_id: int = Field(..., description="内部记录ID")
    task_id: str = Field(..., description="第三方绘画任务ID")
    slogan: str = Field(..., description="AI生成的品牌Slogan")
    status: VisualStatus = Field(..., description="当前状态")
    image_url: str | None = Field(default=None, description="生成图片地址")
    image_model: str = Field(..., description="图像生成模型")


class VisualStatusOut(BaseModel):
    visual_id: int
    status: VisualStatus
    image_url: str | None = None
    slogan: str | None = None
    image_model: str | None = None


class SloganAndPromptSchema(BaseModel):
    slogan: str = Field(..., description="一句简短、押韵、有记忆点的中文品牌口号，15字以内")
    mj_prompt: str = Field(..., description="用于图像生成的英文品牌视觉提示词")


class BrandKitCreateIn(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    moral: str = Field(default="", max_length=2000)
    category: Literal["企业名"] = "企业名"
    industry: str = Field(..., min_length=2, max_length=200)
    audience: str = Field(..., min_length=2, max_length=200)
    design_style: str = Field(default="现代简约", min_length=2, max_length=100)
    primary_color: str = Field(default="蓝色", min_length=1, max_length=50)
    image_model: VisualImageModel = "wan2.6-image"


class BrandKitAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_type: str
    variant_index: int
    status: VisualStatus
    image_url: str | None
    error_message: str | None


class BrandKitOut(BaseModel):
    id: int
    name: str
    moral: str | None
    industry: str
    audience: str
    design_style: str
    primary_color: str
    slogan: str
    status: VisualStatus
    assets: list[BrandKitAssetOut]
    created_time: datetime
