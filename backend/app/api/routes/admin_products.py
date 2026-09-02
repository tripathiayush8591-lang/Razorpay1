from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.product import ProductResponse, ProductCreateRequest, ProductUpdateRequest
from app.services.catalog import (
    list_products,
    get_product_by_id,
    create_product,
    update_product,
    deactivate_product,
)

router = APIRouter(prefix="/api/admin/products", tags=["admin-products"])


@router.get("", response_model=ApiResponse[List[ProductResponse]])
def get_admin_products(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_price_paise: Optional[int] = Query(None, description="Max price filter in paise"),
    active_only: bool = Query(False, description="Filter for active SKUs only"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProductResponse]]:
    """Retrieve all merchant products (including inactive SKUs) with optional filtering."""
    products = list_products(
        db=db,
        merchant_id=current_admin.merchant_id,
        active_only=active_only,
        category=category,
        max_price_paise=max_price_paise,
        q=q,
    )
    data = [ProductResponse.from_orm_model(p) for p in products]
    return ApiResponse(success=True, data=data)


@router.post("", response_model=ApiResponse[ProductResponse])
def create_admin_product(
    payload: ProductCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductResponse]:
    """Create a new product SKU in the authoritative merchant catalog."""
    product = create_product(
        db=db,
        merchant_id=current_admin.merchant_id,
        data=payload,
    )
    return ApiResponse(success=True, data=ProductResponse.from_orm_model(product))


@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_admin_product(
    product_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductResponse]:
    """Retrieve product SKU details by product ID."""
    product = get_product_by_id(db=db, product_id=product_id, active_only=False)
    return ApiResponse(success=True, data=ProductResponse.from_orm_model(product))


@router.patch("/{product_id}", response_model=ApiResponse[ProductResponse])
def update_admin_product(
    product_id: str,
    payload: ProductUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductResponse]:
    """Partially update an existing product SKU."""
    product = update_product(db=db, product_id=product_id, data=payload)
    return ApiResponse(success=True, data=ProductResponse.from_orm_model(product))


@router.delete("/{product_id}", response_model=ApiResponse[ProductResponse])
def delete_admin_product(
    product_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductResponse]:
    """Soft-delete a product SKU by setting active=False (does not hard-delete)."""
    product = deactivate_product(db=db, product_id=product_id)
    return ApiResponse(success=True, data=ProductResponse.from_orm_model(product))
