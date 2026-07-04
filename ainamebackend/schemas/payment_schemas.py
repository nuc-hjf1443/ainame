from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class AlipayPaymentOut(BaseModel):
    order_id: int
    out_trade_no: str
    payment_url: str


class PaymentSyncOut(BaseModel):
    out_trade_no: str
    status: str
    order_type: str | None
    order_id: int


class MyPaymentOrderOut(BaseModel):
    id: int
    amount: Decimal
    status: str
    order_type: str | None = None
    payment_provider: str | None = None
    payment_subject: str | None = None
    package_name: str | None = None
    out_trade_no: str | None = None
    provider_trade_no: str | None = None
    paid_time: datetime | None = None
    created_time: datetime
    updated_time: datetime
    payment_deadline: datetime | None = None
    service_order_id: int | None = None
    service_status: str | None = None
    service_package_name: str | None = None


class MyPaymentOrderPageOut(BaseModel):
    items: list[MyPaymentOrderOut]
    total: int
    page: int
    page_size: int
