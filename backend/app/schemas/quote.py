from typing import List
from pydantic import BaseModel, ConfigDict, Field


class QuoteItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    sku: str
    name: str
    quantity: int
    unit_price_paise: int
    total_paise: int
    in_stock: bool


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cart_id: str
    items: List[QuoteItemResponse] = Field(default_factory=list)
    subtotal_paise: int
    discount_paise: int = 0
    delivery_paise: int = 0
    total_paise: int
    currency: str = "INR"
    valid: bool
    warnings: List[str] = Field(default_factory=list)
