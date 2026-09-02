from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductResponse


class CartCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255, description="Client guest session identifier")


class CartItemAddRequest(BaseModel):
    product_id: str = Field(..., min_length=1, description="Product ID to add to cart")
    quantity: int = Field(1, ge=1, description="Quantity to add")


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=0, description="Authoritative quantity (0 removes the item)")


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cart_id: str
    product_id: str
    quantity: int
    unit_price_paise_snapshot: int
    product: Optional[ProductResponse] = None
    created_at: datetime
    updated_at: datetime


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    session_id: str
    status: str
    currency: str
    items: List[CartItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, cart: Any) -> "CartResponse":
        items_out = []
        for item in getattr(cart, "items", []):
            prod_resp = None
            if getattr(item, "product", None):
                prod_resp = ProductResponse.from_orm_model(item.product)
            items_out.append(
                CartItemResponse(
                    id=item.id,
                    cart_id=item.cart_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price_paise_snapshot=item.unit_price_paise_snapshot,
                    product=prod_resp,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )
        return cls(
            id=cart.id,
            merchant_id=cart.merchant_id,
            session_id=cart.session_id,
            status=cart.status,
            currency=cart.currency,
            items=items_out,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

