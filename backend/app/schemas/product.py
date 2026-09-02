import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100, description="Merchant unique SKU code")
    name: str = Field(..., min_length=2, max_length=255, description="Product display name")
    category: str = Field(..., min_length=2, max_length=100, description="Product category")
    short_description: str = Field(..., min_length=5, description="Brief summary")
    description: str = Field(..., min_length=5, description="Full technical description")
    price_paise: int = Field(..., ge=0, description="Authoritative retail price in paise (1 INR = 100 paise)")
    inventory_quantity: int = Field(..., ge=0, description="Available physical stock")
    image_url: str = Field(..., min_length=1, description="Image URL or static relative path")
    tags: List[str] = Field(default_factory=list, description="Keywords and tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom specifications")
    active: bool = Field(True, description="Whether product is active and visible in catalog")


class ProductUpdateRequest(BaseModel):
    sku: Optional[str] = Field(None, min_length=2, max_length=100)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    short_description: Optional[str] = None
    description: Optional[str] = None
    price_paise: Optional[int] = Field(None, ge=0)
    inventory_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    sku: str
    name: str
    category: str
    short_description: str
    description: str
    price_paise: int
    inventory_quantity: int
    image_url: str
    tags: List[str]
    attributes: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, product: Any) -> "ProductResponse":
        try:
            tags = json.loads(product.tags_json) if isinstance(product.tags_json, str) else (product.tags_json or [])
        except Exception:
            tags = []

        try:
            attributes = json.loads(product.attributes_json) if isinstance(product.attributes_json, str) else (product.attributes_json or {})
        except Exception:
            attributes = {}

        return cls(
            id=product.id,
            merchant_id=product.merchant_id,
            sku=product.sku,
            name=product.name,
            category=product.category,
            short_description=product.short_description,
            description=product.description,
            price_paise=product.price_paise,
            inventory_quantity=product.inventory_quantity,
            image_url=product.image_url,
            tags=tags,
            attributes=attributes,
            active=product.active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
