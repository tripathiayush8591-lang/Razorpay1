import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, case, and_

from app.core.config import settings
from app.models.product import Product
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest


def list_products(
    db: Session,
    merchant_id: Optional[str] = None,
    active_only: bool = True,
    category: Optional[str] = None,
    max_price_paise: Optional[int] = None,
    q: Optional[str] = None,
) -> List[Product]:
    """Authoritative product listing with category, max price, and search filtering."""
    stmt = select(Product)

    if merchant_id:
        stmt = stmt.where(Product.merchant_id == merchant_id)

    if active_only:
        stmt = stmt.where(Product.active.is_(True))

    if category and category.lower() != "all":
        stmt = stmt.where(Product.category.ilike(f"%{category}%"))

    if max_price_paise is not None:
        stmt = stmt.where(Product.price_paise <= max_price_paise)

    if q:
        search = f"%{q}%"
        words = [w for w in q.strip().split() if len(w) > 1]
        if len(words) > 1:
            word_conditions = []
            for w in words:
                w_search = f"%{w}%"
                word_conditions.append(
                    Product.sku.ilike(w_search)
                    | Product.name.ilike(w_search)
                    | Product.category.ilike(w_search)
                    | Product.description.ilike(w_search)
                    | Product.short_description.ilike(w_search)
                    | Product.tags_json.ilike(w_search)
                )
            stmt = stmt.where(
                Product.name.ilike(search)
                | Product.category.ilike(search)
                | Product.description.ilike(search)
                | and_(*word_conditions)
            )
        else:
            stmt = stmt.where(
                Product.sku.ilike(search)
                | Product.name.ilike(search)
                | Product.category.ilike(search)
                | Product.description.ilike(search)
                | Product.short_description.ilike(search)
                | Product.tags_json.ilike(search)
            )

        relevance = case(
            (Product.name.ilike(search), 1),
            (Product.category.ilike(search), 2),
            (Product.short_description.ilike(search), 3),
            (Product.tags_json.ilike(search), 4),
            else_=5,
        )
        stmt = stmt.order_by(relevance.asc(), Product.created_at.desc())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    return list(db.scalars(stmt).all())


def get_product_by_id(
    db: Session,
    product_id: str,
    active_only: bool = False,
) -> Product:
    """Retrieve product by ID or raise 404."""
    stmt = select(Product).where(Product.id == product_id)
    if active_only:
        stmt = stmt.where(Product.active.is_(True))

    product = db.scalar(stmt)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found",
        )
    return product


def create_product(
    db: Session,
    merchant_id: str,
    data: ProductCreateRequest,
) -> Product:
    """Create a new product SKU in the authoritative database."""
    # Check if SKU already exists
    existing = db.scalar(select(Product).where(Product.sku == data.sku.strip()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{data.sku}' already exists",
        )

    product_id = f"prod_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    product = Product(
        id=product_id,
        merchant_id=merchant_id,
        sku=data.sku.strip(),
        name=data.name.strip(),
        category=data.category.strip(),
        short_description=data.short_description.strip(),
        description=data.description.strip(),
        price_paise=data.price_paise,
        inventory_quantity=data.inventory_quantity,
        image_url=data.image_url.strip(),
        tags_json=json.dumps(data.tags),
        attributes_json=json.dumps(data.attributes),
        active=data.active,
        created_at=now,
        updated_at=now,
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: str,
    data: ProductUpdateRequest,
) -> Product:
    """Apply partial updates to an existing product SKU with safe superseded image cleanup."""
    product = get_product_by_id(db, product_id, active_only=False)
    old_image_url = product.image_url

    # If SKU is being updated, verify it is not already taken by another product
    if data.sku is not None and data.sku.strip() != product.sku:
        existing = db.scalar(
            select(Product).where(Product.sku == data.sku.strip(), Product.id != product_id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{data.sku}' already exists",
            )
        product.sku = data.sku.strip()

    if data.name is not None:
        product.name = data.name.strip()
    if data.category is not None:
        product.category = data.category.strip()
    if data.short_description is not None:
        product.short_description = data.short_description.strip()
    if data.description is not None:
        product.description = data.description.strip()
    if data.price_paise is not None:
        product.price_paise = data.price_paise
    if data.inventory_quantity is not None:
        product.inventory_quantity = data.inventory_quantity
    if data.image_url is not None:
        product.image_url = data.image_url.strip()
    if data.tags is not None:
        product.tags_json = json.dumps(data.tags)
    if data.attributes is not None:
        product.attributes_json = json.dumps(data.attributes)
    if data.active is not None:
        product.active = data.active

    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)

    # Safe cleanup: If image was updated and old image was a local upload, clean it up
    # only after new product state has successfully committed and no other SKU references it
    if (
        data.image_url is not None
        and data.image_url.strip() != old_image_url
        and old_image_url
        and old_image_url.startswith("/static/uploads/products/")
    ):
        other_ref = db.scalar(
            select(Product).where(Product.image_url == old_image_url, Product.id != product_id)
        )
        if not other_ref:
            filename = Path(old_image_url).name
            file_path = settings.STATIC_UPLOADS_DIR / "products" / filename
            try:
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
            except Exception:
                pass

    return product


def deactivate_product(
    db: Session,
    product_id: str,
) -> Product:
    """Soft-delete a product SKU by setting active=False."""
    product = get_product_by_id(db, product_id, active_only=False)
    product.active = False
    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)
    return product
