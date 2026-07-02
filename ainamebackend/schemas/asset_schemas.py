from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NamingAssetCreateIn(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    category: Literal["人名", "企业名", "宠物名"]
    moral: str | None = Field(default=None, max_length=2000)
    reference: str | None = Field(default=None, max_length=2000)
    domain: str | None = Field(default=None, max_length=255)
    domain_status: str | None = Field(default=None, max_length=100)


class NamingAssetOut(NamingAssetCreateIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_time: datetime


class VisualAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thread_id: str
    name: str
    category: str
    moral: str | None
    slogan: str | None
    image_url: str | None
    status: str
    created_time: datetime


class AssetPageOut(BaseModel):
    items: list[NamingAssetOut]
    total: int
    page: int
    page_size: int


class VisualAssetPageOut(BaseModel):
    items: list[VisualAssetOut]
    total: int
    page: int
    page_size: int
