from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ExpertType = Literal["CULTURE_MASTER", "BRAND_CONSULTANT"]
ExpertLevel = Literal["STANDARD", "SENIOR", "MASTER"]


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
    expert_level: str = "STANDARD"
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
    expert_level: ExpertLevel = "STANDARD"
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    delivery_days: int = Field(..., ge=1, le=365)
    description: str = Field(..., min_length=1, max_length=3000)
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class ServicePackageUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    expert_type: ExpertType | None = None
    expert_level: ExpertLevel | None = None
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
    chat_thread_id: int | None = None
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
    chat_thread_id: int | None = None
    out_trade_no: str | None = None
    status: str
    rejection_reason: str | None
    report: ReportOut | None = None
    reviewed: bool = False
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
    expert_level: ExpertLevel | None = None


class CommunityModerationIn(BaseModel):
    action: Literal["HIDE", "DISMISS"]
    resolution: str | None = Field(default=None, max_length=1000)


class ChatThreadCreateIn(BaseModel):
    expert_id: int
    package_id: int


class ChatMessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class ChatAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thread_id: int
    message_id: int | None
    uploader_user_id: int
    file_name: str
    file_url: str
    file_type: str | None
    file_size: int
    created_time: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thread_id: int
    sender_user_id: int
    content: str
    read_time: datetime | None
    created_time: datetime
    attachments: list[ChatAttachmentOut] = Field(default_factory=list)


class ChatMessagePageOut(BaseModel):
    items: list[ChatMessageOut]
    total: int
    page: int
    page_size: int


class ChatThreadOut(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    expert_id: int
    expert_user_id: int
    expert_name: str
    package_id: int
    package_name: str
    service_order_id: int | None
    status: str
    customer_unread_count: int
    expert_unread_count: int
    last_message_at: datetime | None
    latest_message: str | None = None
    created_time: datetime


class ChatThreadDetailOut(ChatThreadOut):
    order: ServiceOrderOut | None = None
    package_price: Decimal | None = None
    expert_type: str | None = None


class ChatThreadPageOut(BaseModel):
    items: list[ChatThreadOut]
    total: int
    page: int
    page_size: int


class WalletOut(BaseModel):
    id: int
    expert_id: int
    available_balance: Decimal
    withdrawing_balance: Decimal
    total_income: Decimal
    total_withdrawn: Decimal
    updated_time: datetime


class WalletTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wallet_id: int
    expert_id: int
    service_order_id: int | None
    withdrawal_id: int | None
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    note: str | None
    created_time: datetime


class WalletTransactionPageOut(BaseModel):
    items: list[WalletTransactionOut]
    total: int
    page: int
    page_size: int


class WithdrawalCreateIn(BaseModel):
    amount: Decimal = Field(..., ge=Decimal("1.00"), max_digits=10, decimal_places=2)
    alipay_account: str = Field(..., min_length=3, max_length=100)
    real_name: str = Field(..., min_length=1, max_length=100)


class WithdrawalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wallet_id: int
    expert_id: int
    amount: Decimal
    alipay_account: str
    real_name: str
    status: str
    review_note: str | None
    reviewed_by: int | None
    reviewed_time: datetime | None
    created_time: datetime
    updated_time: datetime


class WithdrawalPageOut(BaseModel):
    items: list[WithdrawalOut]
    total: int
    page: int
    page_size: int


class WithdrawalReviewIn(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    review_note: str | None = Field(default=None, max_length=1000)
