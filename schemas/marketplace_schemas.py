from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ExpertType = Literal["CULTURE_MASTER", "BRAND_CONSULTANT"]


class ExpertApplyIn(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)
    expert_type: ExpertType
    bio: str = Field(..., min_length=20, max_length=3000)
    credentials: str = Field(..., min_length=10, max_length=3000)
    years_experience: int = Field(..., ge=0, le=80)


class ExpertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    display_name: str
    expert_type: str
    bio: str
    credentials: str
    years_experience: int
    status: str
    review_note: str | None
    average_rating: float = 0
    review_count: int = 0
    created_time: datetime


class ExpertPageOut(BaseModel):
    items: list[ExpertOut]
    total: int
    page: int
    page_size: int


class ServicePackageIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expert_type: ExpertType
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    delivery_days: int = Field(..., ge=1, le=365)
    description: str = Field(..., min_length=1, max_length=3000)
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class ServicePackageUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    expert_type: ExpertType | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    delivery_days: int | None = Field(default=None, ge=1, le=365)
    description: str | None = Field(default=None, min_length=1, max_length=3000)
    status: Literal["ACTIVE", "INACTIVE"] | None = None


class ServicePackageOut(ServicePackageIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_time: datetime


class ServiceOrderCreateIn(BaseModel):
    expert_id: int
    package_id: int
    naming_asset_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: Literal["人名", "企业名", "宠物名"] | None = None
    moral: str | None = Field(default=None, max_length=2000)
    requirements: str = Field(..., min_length=5, max_length=3000)

    @model_validator(mode="after")
    def validate_name_source(self):
        if not self.naming_asset_id and (not self.name or not self.category):
            raise ValueError("请选择名字资产，或直接填写名字和分类")
        return self


class ReportIn(BaseModel):
    overview: str = ""
    professional_analysis: str = ""
    phonetic_semantic_analysis: str = ""
    communication_advantages: str = ""
    risk_notes: str = ""
    recommendations: str = ""
    conclusion: str = ""


class ReportOut(ReportIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_order_id: int
    status: str
    updated_time: datetime


class ServiceOrderOut(BaseModel):
    id: int
    finance_order_id: int
    customer_id: int
    expert_id: int
    expert_name: str
    package_id: int
    package_name: str
    naming_asset_id: int
    asset_name: str
    original_amount: Decimal
    discount_rate: Decimal
    amount: Decimal
    requirements: str
    payment_status: str
    status: str
    rejection_reason: str | None
    report: ReportOut | None = None
    created_time: datetime


class ServiceOrderPageOut(BaseModel):
    items: list[ServiceOrderOut]
    total: int
    page: int
    page_size: int


class RejectOrderIn(BaseModel):
    reason: str = Field(..., min_length=2, max_length=1000)


class ReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: str | None = Field(default=None, max_length=1000)


class ExpertReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_order_id: int
    rating: int
    content: str | None
    created_time: datetime


class ExpertReviewDecisionIn(BaseModel):
    status: Literal["APPROVED", "REJECTED", "SUSPENDED"]
    review_note: str | None = Field(default=None, max_length=1000)


class CommunityModerationIn(BaseModel):
    action: Literal["HIDE", "DISMISS"]
    resolution: str | None = Field(default=None, max_length=1000)
