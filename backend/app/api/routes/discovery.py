from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.product import ProductResponse
from app.schemas.discovery import (
    ProductAvailabilityResponse,
    DeliveryEstimateResponse,
    OffersResponse,
)
from app.services.discovery import (
    get_product_availability,
    get_related_products,
    estimate_delivery,
    get_offers,
)

router = APIRouter(prefix="/api", tags=["discovery"])


@router.get("/products/{product_id}/availability", response_model=ApiResponse[ProductAvailabilityResponse])
def product_availability_endpoint(
    product_id: str,
    db: Session = Depends(get_db),
):
    """Authoritative product availability status, price, and physical stock."""
    avail = get_product_availability(db, product_id)
    return ApiResponse(data=avail)


@router.get("/products/{product_id}/related", response_model=ApiResponse[List[ProductResponse]])
def related_products_endpoint(
    product_id: str,
    limit: int = Query(4, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Related products determined by authoritative merchant cross-sell policy."""
    products = get_related_products(db, product_id, limit=limit)
    data = [ProductResponse.from_orm_model(p) for p in products]
    return ApiResponse(data=data)


@router.get("/offers", response_model=ApiResponse[OffersResponse])
def merchant_offers_endpoint(
    db: Session = Depends(get_db),
):
    """Active store offers, discounts, and delivery perks."""
    offers = get_offers(db)
    return ApiResponse(data=offers)


@router.get("/delivery/estimate", response_model=ApiResponse[DeliveryEstimateResponse])
def delivery_estimate_endpoint(
    subtotal_paise: int = Query(0, ge=0),
    postal_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Calculate authoritative delivery fees and delivery timeframe for a given cart subtotal."""
    estimate = estimate_delivery(db, subtotal_paise=subtotal_paise, postal_code=postal_code)
    return ApiResponse(data=estimate)
