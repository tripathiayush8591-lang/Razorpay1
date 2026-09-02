from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShippingAddressSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line1: str
    city: str
    state: str
    postal_code: str
    country: str = "India"


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


class OrderItemSnapshotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    sku: str
    name: str
    quantity: int
    unit_price_paise: int
    total_paise: int


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    cart_id: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: ShippingAddressSchema
    items: List[OrderItemSnapshotSchema] = Field(default_factory=list)
    amount_paise: int
    currency: str = "INR"
    status: str
    razorpay_order_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    received: bool = True
    event: str
    status: str
