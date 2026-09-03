from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


from app.schemas.order import (
    ShippingAddressSchema,
    OrderItemSnapshotSchema,
    OrderResponse,
)


class CheckoutInitiateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., min_length=3, max_length=255)
    customer_phone: str = Field(..., min_length=5, max_length=50)
    shipping_address: ShippingAddressSchema
    approved_total_paise: int = Field(..., gt=0)


class CheckoutInitiateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_order_id: str
    razorpay_order_id: str
    razorpay_key_id: str
    amount_paise: int
    currency: str = "INR"
    customer_name: str
    customer_email: str
    customer_phone: str


class PaymentVerifyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    status: str
    amount_paise: int
    currency: str = "INR"
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None





class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    received: bool = True
    event: str
    status: str
