from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.product import ProductResponse
from app.services.catalog import list_products, get_product_by_id

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ApiResponse[List[ProductResponse]])
def get_public_products(
    q: Optional[str] = Query(None, description="Search query by name, description, or tag"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_price_paise: Optional[int] = Query(None, description="Max price in paise"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProductResponse]]:
    """Storefront product discovery endpoint returning only active products."""
    products = list_products(
        db=db,
        active_only=True,
        category=category,
        max_price_paise=max_price_paise,
        q=q,
    )
    data = [ProductResponse.from_orm_model(p) for p in products]
    return ApiResponse(success=True, data=data)


@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_public_product_by_id(
    product_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[ProductResponse]:
    """Storefront product detail endpoint for active products."""
    product = get_product_by_id(db=db, product_id=product_id, active_only=True)
    return ApiResponse(success=True, data=ProductResponse.from_orm_model(product))
