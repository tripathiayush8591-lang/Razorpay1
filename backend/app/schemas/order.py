from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShippingAddressSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line1: str
    city: str
    state: str
    postal_code: str
    country: str = "India"


class OrderItemSnapshotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    sku: str
    name: str
    quantity: int
    unit_price_paise: int
    total_paise: int


class PaymentDetailsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str = "razorpay"
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    signature_verified: bool = False
    status: str = "PENDING_PAYMENT"
    paid_at: Optional[datetime] = None


class FulfillmentDetailsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    processing_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None


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
    payment_status: str = "PENDING_PAYMENT"
    payment_details: Optional[PaymentDetailsSchema] = None
    fulfillment: Optional[FulfillmentDetailsSchema] = None
    razorpay_order_id: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    processing_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FulfillmentUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    cancellation_reason: Optional[str] = Field(None, max_length=500)


class AdminOrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    amount_paise: int
    currency: str = "INR"
    status: str
    payment_status: str
    items_count: int
    razorpay_order_id: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None


class AdminOrdersPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[AdminOrderListItem]
    total: int
    limit: int
    offset: int


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: Optional[str] = None
    session_id: Optional[str] = None
    actor_type: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
