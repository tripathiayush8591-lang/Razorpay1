from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    sku: str
    name: str
    price_paise: int
    inventory_quantity: int
    in_stock: bool
    active: bool


class DeliveryEstimateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    standard_delivery_paise: int
    express_delivery_paise: int
    free_delivery_threshold_paise: int
    estimated_days_standard: int
    estimated_days_express: int
    delivery_paise: int
    is_free: bool


class OfferItemResponse(BaseModel):
    id: str
    title: str
    description: str
    discount_percent: Optional[int] = None
    terms: Optional[str] = None


class OffersResponse(BaseModel):
    offers: List[OfferItemResponse] = Field(default_factory=list)
    max_discount_percent: int
