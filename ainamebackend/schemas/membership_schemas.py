from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MembershipPackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    package_code: str
    name: str
    price: Decimal
    api_quota: int
    duration_days: int
    naming_daily_quota: int
    visual_daily_quota: int
    expert_discount: Decimal
    description: str | None


class MembershipOrderIn(BaseModel):
    package_id: int


class MembershipOrderOut(BaseModel):
    id: int
    package_id: int
    amount: Decimal
    status: str
    paid_time: datetime | None


class QuotaOut(BaseModel):
    used: int
    limit: int
    remaining: int


class MyProfileOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    bio: str | None
    role: str
    account_type: str
    expert_status: str | None
    created_time: datetime
    is_vip: bool
    vip_package_code: str | None
    vip_package_name: str | None
    vip_expires_at: datetime | None
    naming_balance: int
    naming_quota: QuotaOut
    visual_quota: QuotaOut


class MyProfileUpdateIn(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    bio: str | None = Field(default=None, max_length=1000)
