import json
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.services.cart import get_cart_by_id
from app.services.policy import get_merchant_policy
from app.schemas.quote import QuoteItemResponse, QuoteResponse


def generate_cart_quote(
    db: Session,
    cart_id: str,
    session_id: str,
) -> QuoteResponse:
    """
    Authoritative server-side quote calculation.
    Always re-reads current live product prices and physical inventory from SQLite.
    Snapshot price from CartItem is never used as authoritative for checkout.
    """
    cart = get_cart_by_id(db, cart_id, session_id=session_id)
    policy = get_merchant_policy(db, cart.merchant_id)

    delivery_rules = {}
    try:
        delivery_rules = json.loads(policy.delivery_rules_json)
    except Exception:
        pass

    free_threshold = delivery_rules.get("free_delivery_threshold_paise", 100000)
    standard_fee = delivery_rules.get("standard_delivery_paise", 15000)

    if not cart.items:
        return QuoteResponse(
            cart_id=cart.id,
            items=[],
            subtotal_paise=0,
            discount_paise=0,
            delivery_paise=0,
            total_paise=0,
            currency=cart.currency,
            valid=False,
            warnings=["Cart is empty"],
        )

    quote_items: List[QuoteItemResponse] = []
    subtotal_paise = 0
    warnings: List[str] = []
    all_in_stock = True

    for item in cart.items:
        # Re-fetch live product directly from SQLite
        live_product = db.scalar(select(Product).where(Product.id == item.product_id))

        if not live_product or not live_product.active:
            all_in_stock = False
            item_name = live_product.name if live_product else item.product_id
            warnings.append(f"Item '{item_name}' is currently unavailable")
            unit_price = item.unit_price_paise_snapshot
            line_total = unit_price * item.quantity
            quote_items.append(
                QuoteItemResponse(
                    product_id=item.product_id,
                    sku=live_product.sku if live_product else "UNKNOWN",
                    name=item_name,
                    quantity=item.quantity,
                    unit_price_paise=unit_price,
                    total_paise=line_total,
                    in_stock=False,
                )
            )
            subtotal_paise += line_total
            continue

        # Re-read authoritative current price
        unit_price = live_product.price_paise
        line_total = unit_price * item.quantity
        subtotal_paise += line_total

        # Authoritative inventory check
        has_stock = live_product.inventory_quantity >= item.quantity
        if not has_stock:
            all_in_stock = False
            if live_product.inventory_quantity == 0:
                warnings.append(f"{live_product.name} is currently out of stock")
            else:
                warnings.append(
                    f"Only {live_product.inventory_quantity} units available for {live_product.name} (requested: {item.quantity})"
                )

        quote_items.append(
            QuoteItemResponse(
                product_id=live_product.id,
                sku=live_product.sku,
                name=live_product.name,
                quantity=item.quantity,
                unit_price_paise=unit_price,
                total_paise=line_total,
                in_stock=has_stock,
            )
        )

    # Authoritative delivery calculation
    is_free_delivery = subtotal_paise >= free_threshold
    delivery_paise = 0 if is_free_delivery else standard_fee

    # Discounts: Phase 3 default is 0
    discount_paise = 0

    total_paise = subtotal_paise - discount_paise + delivery_paise

    # Quote validity requires stock availability unless merchant policy explicitly allows out of stock
    is_valid = True
    if not all_in_stock and not policy.allow_out_of_stock:
        is_valid = False

    return QuoteResponse(
        cart_id=cart.id,
        items=quote_items,
        subtotal_paise=subtotal_paise,
        discount_paise=discount_paise,
        delivery_paise=delivery_paise,
        total_paise=total_paise,
        currency=cart.currency,
        valid=is_valid,
        warnings=warnings,
    )
