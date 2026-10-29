from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from src.payments.models import PaymentStatus


class CheckoutSessionCreate(BaseModel):
    order_id: int

    model_config = ConfigDict(from_attributes=True)


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

    model_config = ConfigDict(from_attributes=True)


class PaymentItemResponse(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatus
    amount: Decimal
    external_payment_id: str | None
    items: list[PaymentItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
