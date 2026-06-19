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


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: UserRole
    is_banned: bool


class UserPageOut(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: PageInt
    page_size: PageSizeInt


class BanUserOut(BaseModel):
    id: int
    is_banned: bool


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    package_id: int | None
    amount: Decimal
    status: str
    paid_time: datetime | None
    created_time: datetime
    updated_time: datetime


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
