from pydantic import BaseModel


class AlipayPaymentOut(BaseModel):
    order_id: int
    out_trade_no: str
    payment_url: str


class PaymentSyncOut(BaseModel):
    out_trade_no: str
    status: str
    order_type: str | None
    order_id: int
