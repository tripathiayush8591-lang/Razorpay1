import json
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.merchant import Merchant
from app.models.product import Product
from app.models.policy import MerchantPolicy
from app.services.catalog import get_product_by_id
from app.services.policy import get_merchant_policy
from app.schemas.discovery import (
    ProductAvailabilityResponse,
    DeliveryEstimateResponse,
    OfferItemResponse,
    OffersResponse,
)


def check_price(db: Session, product_id: str) -> int:
    """Return the authoritative price in paise for a product."""
    product = get_product_by_id(db, product_id, active_only=True)
    return product.price_paise


def check_inventory(db: Session, product_id: str, requested_quantity: int = 1) -> Tuple[int, bool]:
    """Check inventory quantity and whether requested quantity is available."""
    product = get_product_by_id(db, product_id, active_only=True)
    available = product.inventory_quantity
    return available, (available >= requested_quantity)


def get_product_availability(db: Session, product_id: str) -> ProductAvailabilityResponse:
    """Authoritative product availability status."""
    product = get_product_by_id(db, product_id, active_only=False)
    return ProductAvailabilityResponse(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        price_paise=product.price_paise,
        inventory_quantity=product.inventory_quantity,
        in_stock=product.inventory_quantity > 0,
        active=product.active,
    )


def get_related_products(db: Session, product_id: str, limit: int = 4) -> List[Product]:
    """Retrieve related products based on authoritative cross-sell policy rules."""
    target_product = get_product_by_id(db, product_id, active_only=True)
    policy = get_merchant_policy(db, target_product.merchant_id)

    recommend_categories: List[str] = []
    try:
        rules = json.loads(policy.cross_sell_rules_json)
        if isinstance(rules, list):
            for rule in rules:
                trigger = rule.get("trigger_category", "").strip().lower()
                rec = rule.get("recommend_category", "").strip()
                if trigger == target_product.category.strip().lower() and rec:
                    recommend_categories.append(rec)
    except Exception:
        recommend_categories = []

    related_products: List[Product] = []
    if recommend_categories:
        stmt = (
            select(Product)
            .where(
                Product.merchant_id == target_product.merchant_id,
                Product.active.is_(True),
                Product.id != target_product.id,
                Product.category.in_(recommend_categories),
            )
            .limit(limit)
        )
        related_products = list(db.scalars(stmt).all())

    # Fallback to same category or popular active products if needed to fill limit
    if len(related_products) < limit:
        existing_ids = {p.id for p in related_products} | {target_product.id}
        stmt = (
            select(Product)
            .where(
                Product.merchant_id == target_product.merchant_id,
                Product.active.is_(True),
                Product.id.not_in(existing_ids),
            )
            .order_by(Product.inventory_quantity.desc())
            .limit(limit - len(related_products))
        )
        fallback = list(db.scalars(stmt).all())
        related_products.extend(fallback)

    return related_products


def estimate_delivery(
    db: Session,
    subtotal_paise: int,
    merchant_id: Optional[str] = None,
    postal_code: Optional[str] = None,
) -> DeliveryEstimateResponse:
    """Authoritative delivery estimate based on merchant policy."""
    if not merchant_id:
        merchant = db.scalar(select(Merchant).limit(1))
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not configured",
            )
        merchant_id = merchant.id

    policy = get_merchant_policy(db, merchant_id)
    delivery_rules = {}
    try:
        delivery_rules = json.loads(policy.delivery_rules_json)
    except Exception:
        pass

    free_threshold = delivery_rules.get("free_delivery_threshold_paise", 100000)
    standard_fee = delivery_rules.get("standard_delivery_paise", 15000)
    express_fee = delivery_rules.get("express_delivery_paise", 35000)
    days_standard = delivery_rules.get("estimated_days_standard", 4)
    days_express = delivery_rules.get("estimated_days_express", 2)

    is_free = subtotal_paise >= free_threshold
    actual_fee = 0 if is_free else standard_fee

    return DeliveryEstimateResponse(
        standard_delivery_paise=standard_fee,
        express_delivery_paise=express_fee,
        free_delivery_threshold_paise=free_threshold,
        estimated_days_standard=days_standard,
        estimated_days_express=days_express,
        delivery_paise=actual_fee,
        is_free=is_free,
    )


def get_offers(db: Session, merchant_id: Optional[str] = None) -> OffersResponse:
    """Retrieve active promotional and policy-based offers."""
    if not merchant_id:
        merchant = db.scalar(select(Merchant).limit(1))
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not configured",
            )
        merchant_id = merchant.id

    policy = get_merchant_policy(db, merchant_id)
    delivery_rules = {}
    try:
        delivery_rules = json.loads(policy.delivery_rules_json)
    except Exception:
        pass
    free_threshold = delivery_rules.get("free_delivery_threshold_paise", 100000)
    free_threshold_inr = free_threshold // 100

    offers = [
        OfferItemResponse(
            id="offer_free_shipping",
            title=f"Free Delivery over ₹{free_threshold_inr:,}",
            description=f"Orders of ₹{free_threshold_inr:,} or more qualify for zero shipping costs automatically.",
            terms="Applied automatically at checkout calculation.",
        ),
        OfferItemResponse(
            id="offer_agent_eligible",
            title="Agentic Concierge Pricing",
            description=f"In-app and autonomous buyers can negotiate bundle discounts up to {policy.max_discount_percent}%.",
            discount_percent=policy.max_discount_percent,
            terms="Subject to merchant policy verification at quote generation.",
        ),
    ]

    return OffersResponse(
        offers=offers,
        max_discount_percent=policy.max_discount_percent,
    )
