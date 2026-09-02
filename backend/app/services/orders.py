import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.order import MerchantOrder
from app.models.cart import Cart
from app.models.product import Product
from app.schemas.checkout import CheckoutInitiateRequest, OrderResponse, ShippingAddressSchema, OrderItemSnapshotSchema
from app.schemas.quote import QuoteResponse
from app.services.audit import log_audit_event


def create_or_reuse_merchant_order(
    db: Session,
    cart: Cart,
    quote: QuoteResponse,
    checkout_data: CheckoutInitiateRequest,
    razorpay_order_id: Optional[str] = None,
) -> MerchantOrder:
    """
    Creates or reuses a MerchantOrder in PENDING_PAYMENT status with an immutable line-item snapshot.
    """
    now = datetime.now(timezone.utc)

    # Prepare immutable snapshot from authoritative quote
    snapshot_items = [
        {
            "product_id": item.product_id,
            "sku": item.sku,
            "name": item.name,
            "quantity": item.quantity,
            "unit_price_paise": item.unit_price_paise,
            "total_paise": item.total_paise,
        }
        for item in quote.items
    ]
    snapshot_json = json.dumps(snapshot_items)
    shipping_json = json.dumps(checkout_data.shipping_address.model_dump())

    # Check if there is already a reusable PENDING_PAYMENT order for this cart
    stmt = (
        select(MerchantOrder)
        .where(
            MerchantOrder.cart_id == cart.id,
            MerchantOrder.status == "PENDING_PAYMENT",
        )
        .order_by(MerchantOrder.created_at.desc())
    )
    existing_order = db.scalar(stmt)

    if existing_order:
        existing_order.customer_name = checkout_data.customer_name
        existing_order.customer_email = checkout_data.customer_email
        existing_order.customer_phone = checkout_data.customer_phone
        existing_order.shipping_address_json = shipping_json
        existing_order.items_snapshot_json = snapshot_json
        existing_order.amount_paise = quote.total_paise
        existing_order.currency = quote.currency
        existing_order.approved_at = now
        if razorpay_order_id:
            existing_order.razorpay_order_id = razorpay_order_id
        existing_order.updated_at = now
        db.commit()
        return existing_order

    new_order = MerchantOrder(
        id=f"order_{uuid.uuid4().hex[:12]}",
        merchant_id=cart.merchant_id,
        cart_id=cart.id,
        customer_name=checkout_data.customer_name,
        customer_email=checkout_data.customer_email,
        customer_phone=checkout_data.customer_phone,
        shipping_address_json=shipping_json,
        items_snapshot_json=snapshot_json,
        amount_paise=quote.total_paise,
        currency=quote.currency,
        status="PENDING_PAYMENT",
        razorpay_order_id=razorpay_order_id,
        approved_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(new_order)
    db.commit()
    return new_order


def finalize_order_paid(
    db: Session,
    order: MerchantOrder,
    razorpay_payment_id: str,
    event_source: str = "checkout_verify",
) -> MerchantOrder:
    """
    Finalizes an order authoritatively:
    1. Idempotency guard: if already PAID or CONFIRMED, return safely.
    2. Atomically decrements product inventory.
    3. Converts/closes the associated cart.
    4. Transitions order status to CONFIRMED.
    5. Records authoritative audit events.
    """
    if order.status in ["PAID", "CONFIRMED"]:
        # Already finalized, idempotent return
        return order

    now = datetime.now(timezone.utc)

    # 1. Parse immutable snapshot items and decrement inventory
    try:
        snapshot_items: List[Dict[str, Any]] = json.loads(order.items_snapshot_json or "[]")
    except Exception:
        snapshot_items = []

    for item in snapshot_items:
        prod_id = item.get("product_id")
        qty = item.get("quantity", 0)
        if prod_id and qty > 0:
            product = db.scalar(select(Product).where(Product.id == prod_id))
            if product:
                # Decrement inventory exactly once
                product.inventory_quantity = max(0, product.inventory_quantity - qty)
                product.updated_at = now

    # 2. Convert / close the cart
    if order.cart_id:
        cart = db.scalar(select(Cart).where(Cart.id == order.cart_id))
        if cart:
            cart.status = "converted"
            cart.updated_at = now

    # 3. Transition order status
    order.status = "CONFIRMED"
    order.paid_at = now
    order.confirmed_at = now
    order.updated_at = now

    db.commit()

    # 4. Record audit events
    log_audit_event(
        db=db,
        actor_type="shopper" if event_source == "checkout_verify" else "system",
        action="payment_verified",
        entity_type="merchant_order",
        session_id=order.cart.session_id if order.cart else None,
        merchant_id=order.merchant_id,
        entity_id=order.id,
        metadata={
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount_paise": order.amount_paise,
            "currency": order.currency,
            "source": event_source,
        },
    )

    log_audit_event(
        db=db,
        actor_type="system",
        action="order_confirmed",
        entity_type="merchant_order",
        session_id=order.cart.session_id if order.cart else None,
        merchant_id=order.merchant_id,
        entity_id=order.id,
        metadata={
            "order_id": order.id,
            "status": "CONFIRMED",
            "items_count": len(snapshot_items),
            "amount_paise": order.amount_paise,
        },
    )

    return order


def get_order_by_id(
    db: Session,
    order_id: str,
    session_id: Optional[str] = None,
    allow_admin: bool = False,
) -> MerchantOrder:
    """
    Retrieves an order by ID with session ownership enforcement.
    """
    stmt = (
        select(MerchantOrder)
        .options(joinedload(MerchantOrder.cart))
        .where(MerchantOrder.id == order_id)
    )
    order = db.scalar(stmt)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' was not found",
        )

    if not allow_admin and session_id:
        # Check ownership via cart session
        if order.cart and order.cart.session_id.strip() != session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to view this order",
            )

    return order


def to_order_response(order: MerchantOrder) -> OrderResponse:
    """
    Transforms ORM MerchantOrder into public OrderResponse with parsed items and address.
    """
    try:
        shipping_dict = json.loads(order.shipping_address_json or "{}")
        shipping = ShippingAddressSchema(**shipping_dict)
    except Exception:
        shipping = ShippingAddressSchema(
            line1="",
            city="",
            state="",
            postal_code="",
            country="India",
        )

    try:
        items_list = json.loads(order.items_snapshot_json or "[]")
        items = [OrderItemSnapshotSchema(**it) for it in items_list]
    except Exception:
        items = []

    return OrderResponse(
        id=order.id,
        merchant_id=order.merchant_id,
        cart_id=order.cart_id,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        shipping_address=shipping,
        items=items,
        amount_paise=order.amount_paise,
        currency=order.currency,
        status=order.status,
        razorpay_order_id=order.razorpay_order_id,
        approved_at=order.approved_at,
        paid_at=order.paid_at,
        confirmed_at=order.confirmed_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
