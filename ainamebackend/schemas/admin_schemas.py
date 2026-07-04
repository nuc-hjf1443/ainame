from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


PageInt = Annotated[int, Field(ge=1)]
PageSizeInt = Annotated[int, Field(ge=1, le=100)]

UserRole = Literal["ADMIN", "B_END", "C_END"]
RefundReviewStatus = Literal["APPROVED", "REJECTED"]
KnowledgeStatus = Literal["ACTIVE", "INACTIVE", "PROCESSING", "FAILED"]
AgentStatus = Literal["ACTIVE", "INACTIVE"]
PackageScope = Literal["VIP", "NAMING_QUOTA", "EXPERT_SERVICE"]
PackageStatus = Literal["ACTIVE", "INACTIVE"]
ExpertType = Literal["CULTURE_MASTER", "BRAND_CONSULTANT"]
ExpertLevel = Literal["STANDARD", "SENIOR", "MASTER"]


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: UserRole
    is_banned: bool
    bio: str | None = None
    created_time: datetime
    is_deleted: bool = False
    is_vip: bool = False
    vip_expires_at: datetime | None = None
    expert_status: str | None = None


class UserPageOut(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: PageInt
    page_size: PageSizeInt


class BanUserOut(BaseModel):
    id: int
    is_banned: bool


class ResetPasswordIn(BaseModel):
    password: str = Field(..., min_length=3, max_length=50)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    package_id: int | None
    amount: Decimal
    status: str
    order_type: str | None = None
    payment_provider: str | None = None
    payment_subject: str | None = None
    package_name: str | None = None
    out_trade_no: str | None = None
    provider_trade_no: str | None = None
    refund_request_no: str | None = None
    refunded_time: datetime | None = None
    paid_time: datetime | None
    created_time: datetime
    updated_time: datetime
    service_order_id: int | None = None
    service_status: str | None = None
    expert_id: int | None = None
    expert_name: str | None = None
    service_package_id: int | None = None
    service_package_name: str | None = None
    refund_id: int | None = None
    refund_status: str | None = None


class OrderPageOut(BaseModel):
    items: list[OrderOut]
    total: int
    page: PageInt
    page_size: PageSizeInt


class RefundReviewIn(BaseModel):
    status: RefundReviewStatus
    review_note: str | None = Field(default=None, max_length=500)


class RefundAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    reason: str
    status: str
    review_note: str | None
    reviewed_time: datetime | None
    created_time: datetime
    updated_time: datetime
    order_amount: Decimal | None = None
    order_status: str | None = None
    order_type: str | None = None
    payment_provider: str | None = None
    out_trade_no: str | None = None
    user_id: int | None = None
    service_order_id: int | None = None
    service_status: str | None = None


class RefundAuditPageOut(BaseModel):
    items: list[RefundAuditOut]
    total: int
    page: PageInt
    page_size: PageSizeInt


class AgentConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_key: str
    agent_name: str
    prompt_template: str
    model_name: str
    temperature: Decimal
    status: str
    created_time: datetime
    updated_time: datetime


class AgentConfigUpdateIn(BaseModel):
    agent_name: str | None = Field(default=None, min_length=1, max_length=100)
    prompt_template: str | None = Field(default=None, min_length=1)
    model_name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    status: AgentStatus | None = None


class KnowledgeBaseUpsertIn(BaseModel):
    knowledge_id: int | None = None
    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str | None = Field(default=None, max_length=500)
    status: KnowledgeStatus = "ACTIVE"


class KnowledgeBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str | None
    status: str
    created_time: datetime
    updated_time: datetime


class SensitiveWordInterceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    input_text: str
    matched_words: str
    created_time: datetime


class SensitiveWordPageOut(BaseModel):
    items: list[SensitiveWordInterceptionOut]
    total: int
    page: PageInt
    page_size: PageSizeInt


class AdminPackageIn(BaseModel):
    package_scope: PackageScope
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    status: PackageStatus = "ACTIVE"
    description: str | None = Field(default=None, max_length=3000)
    package_code: str | None = Field(default=None, max_length=50)
    api_quota: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=0, le=3650)
    naming_daily_quota: int | None = Field(default=None, ge=0)
    visual_daily_quota: int | None = Field(default=None, ge=0)
    expert_discount: Decimal | None = Field(default=None, ge=0, le=1, max_digits=4, decimal_places=2)
    expert_type: ExpertType | None = None
    expert_level: ExpertLevel | None = None
    delivery_days: int | None = Field(default=None, ge=1, le=365)


class AdminPackageUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    status: PackageStatus | None = None
    description: str | None = Field(default=None, max_length=3000)
    package_code: str | None = Field(default=None, max_length=50)
    api_quota: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=0, le=3650)
    naming_daily_quota: int | None = Field(default=None, ge=0)
    visual_daily_quota: int | None = Field(default=None, ge=0)
    expert_discount: Decimal | None = Field(default=None, ge=0, le=1, max_digits=4, decimal_places=2)
    expert_type: ExpertType | None = None
    expert_level: ExpertLevel | None = None
    delivery_days: int | None = Field(default=None, ge=1, le=365)


class AdminPackageOut(BaseModel):
    id: int
    package_scope: PackageScope
    name: str
    price: Decimal
    status: str
    description: str | None = None
    package_code: str | None = None
    api_quota: int | None = None
    duration_days: int | None = None
    naming_daily_quota: int | None = None
    visual_daily_quota: int | None = None
    expert_discount: Decimal | None = None
    expert_type: str | None = None
    expert_level: str | None = None
    delivery_days: int | None = None
    created_time: datetime
    updated_time: datetime | None = None
