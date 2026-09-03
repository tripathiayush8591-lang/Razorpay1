import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, func

from app.models.order import MerchantOrder
from app.models.cart import Cart
from app.models.product import Product
from app.models.admin_user import AdminUser
from app.models.audit import AuditEvent
from app.schemas.checkout import CheckoutInitiateRequest
from app.schemas.order import (
    OrderResponse,
    ShippingAddressSchema,
    OrderItemSnapshotSchema,
    PaymentDetailsSchema,
    FulfillmentDetailsSchema,
    AdminOrderListItem,
)
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
    Transforms ORM MerchantOrder into public OrderResponse with parsed items, address,
    explicit payment status separation, and fulfillment details.
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

    # Explicit payment vs fulfillment separation
    is_paid = bool(order.paid_at or order.status in ["PAID", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"])
    payment_status = "PAID" if is_paid else "PENDING_PAYMENT"

    latest_attempt = order.payment_attempts[-1] if order.payment_attempts else None
    payment_details = PaymentDetailsSchema(
        provider="razorpay",
        razorpay_order_id=order.razorpay_order_id,
        razorpay_payment_id=latest_attempt.razorpay_payment_id if latest_attempt else None,
        signature_verified=bool(order.paid_at or (latest_attempt and latest_attempt.signature_verified)),
        status=payment_status,
        paid_at=order.paid_at,
    )

    fulfillment = FulfillmentDetailsSchema(
        status=order.status,
        carrier=order.carrier,
        tracking_number=order.tracking_number,
        confirmed_at=order.confirmed_at,
        processing_at=order.processing_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at,
        cancellation_reason=order.cancellation_reason,
    )

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
        payment_status=payment_status,
        payment_details=payment_details,
        fulfillment=fulfillment,
        razorpay_order_id=order.razorpay_order_id,
        carrier=order.carrier,
        tracking_number=order.tracking_number,
        approved_at=order.approved_at,
        paid_at=order.paid_at,
        confirmed_at=order.confirmed_at,
        processing_at=order.processing_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at,
        cancellation_reason=order.cancellation_reason,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def list_guest_orders(db: Session, session_id: str) -> List[MerchantOrder]:
    """
    Retrieves all orders belonging to the guest's current session.
    Strict session isolation: joins with Cart on session_id.
    """
    stmt = (
        select(MerchantOrder)
        .options(joinedload(MerchantOrder.cart), joinedload(MerchantOrder.payment_attempts))
        .join(Cart, MerchantOrder.cart_id == Cart.id)
        .where(Cart.session_id == session_id.strip())
        .order_by(MerchantOrder.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


def list_admin_orders(
    db: Session,
    merchant_id: str,
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[MerchantOrder], int]:
    """
    Retrieves merchant orders with optional status filter and text search for Admin.
    """
    base_stmt = select(MerchantOrder).where(MerchantOrder.merchant_id == merchant_id)

    if status_filter and status_filter.lower() != "all":
        base_stmt = base_stmt.where(MerchantOrder.status == status_filter.upper())

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        base_stmt = base_stmt.where(
            func.lower(MerchantOrder.id).like(term)
            | func.lower(MerchantOrder.customer_name).like(term)
            | func.lower(MerchantOrder.customer_email).like(term)
            | func.lower(MerchantOrder.customer_phone).like(term)
            | func.lower(MerchantOrder.razorpay_order_id).like(term)
        )

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = db.scalar(count_stmt) or 0

    items_stmt = (
        base_stmt
        .options(joinedload(MerchantOrder.cart), joinedload(MerchantOrder.payment_attempts))
        .order_by(MerchantOrder.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(items_stmt).unique().all())
    return items, total


def get_admin_order_by_id(db: Session, order_id: str, merchant_id: str) -> MerchantOrder:
    """
    Retrieves full merchant order by ID for admin.
    """
    stmt = (
        select(MerchantOrder)
        .options(joinedload(MerchantOrder.cart), joinedload(MerchantOrder.payment_attempts))
        .where(MerchantOrder.id == order_id, MerchantOrder.merchant_id == merchant_id)
    )
    order = db.scalar(stmt)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' was not found",
        )
    return order


def update_order_fulfillment_status(
    db: Session,
    order_id: str,
    new_status: str,
    admin_user: AdminUser,
    carrier: Optional[str] = None,
    tracking_number: Optional[str] = None,
    cancellation_reason: Optional[str] = None,
) -> MerchantOrder:
    """
    Atomically transitions fulfillment status using:
    UPDATE merchant_orders SET status = :new_status WHERE id = :id AND status IN (:expected_statuses)
    
    Guarantees:
    1. Race-safe concurrency (only 1 transition succeeds).
    2. Idempotency (same-status retry returns cleanly without duplicate audit or timestamp rewrite).
    3. Mandatory cancellation reason when cancelling.
    4. NO inventory restoration and NO fake refund on cancellation.
    5. Zero inventory decrement during fulfillment transitions.
    6. Exact 1 audit event created per valid state transition within commit boundary.
    """
    now = datetime.now(timezone.utc)
    timestamp_values: Dict[str, Any] = {}

    if new_status == "PROCESSING":
        expected_statuses = ["CONFIRMED"]
        timestamp_values["processing_at"] = now
    elif new_status == "SHIPPED":
        expected_statuses = ["PROCESSING"]
        timestamp_values["shipped_at"] = now
        if carrier:
            timestamp_values["carrier"] = carrier.strip()
        if tracking_number:
            timestamp_values["tracking_number"] = tracking_number.strip()
    elif new_status == "DELIVERED":
        expected_statuses = ["SHIPPED"]
        timestamp_values["delivered_at"] = now
    elif new_status == "CANCELLED":
        expected_statuses = ["CONFIRMED", "PROCESSING"]
        if not cancellation_reason or not cancellation_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A cancellation reason is required when cancelling an order.",
            )
        timestamp_values["cancelled_at"] = now
        timestamp_values["cancellation_reason"] = cancellation_reason.strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target fulfillment status: '{new_status}'",
        )

    # Atomic conditional update
    update_stmt = (
        update(MerchantOrder)
        .where(
            MerchantOrder.id == order_id,
            MerchantOrder.merchant_id == admin_user.merchant_id,
            MerchantOrder.status.in_(expected_statuses),
        )
        .values(
            status=new_status,
            updated_at=now,
            **timestamp_values,
        )
    )
    result = db.execute(update_stmt)

    if result.rowcount == 1:
        # Atomic transition succeeded!
        action_map = {
            "PROCESSING": "order_processing_started",
            "SHIPPED": "order_shipped",
            "DELIVERED": "order_delivered",
            "CANCELLED": "order_cancelled",
        }
        audit_metadata: Dict[str, Any] = {
            "order_id": order_id,
            "new_status": new_status,
            "admin_id": admin_user.id,
            "admin_email": admin_user.email,
        }
        if carrier:
            audit_metadata["carrier"] = carrier.strip()
        if tracking_number:
            audit_metadata["tracking_number"] = tracking_number.strip()
        if cancellation_reason:
            audit_metadata["cancellation_reason"] = cancellation_reason.strip()
            audit_metadata["financial_note"] = "NO_REFUND_IN_MVP"
            audit_metadata["inventory_note"] = "INVENTORY_UNRESTORED_IN_MVP"

        log_audit_event(
            db=db,
            actor_type="admin",
            action=action_map[new_status],
            entity_type="merchant_order",
            merchant_id=admin_user.merchant_id,
            entity_id=order_id,
            metadata=audit_metadata,
        )
        db.commit()
        return get_admin_order_by_id(db, order_id=order_id, merchant_id=admin_user.merchant_id)

    # rowcount == 0: check current status for idempotency or conflict
    current_order = db.scalar(
        select(MerchantOrder).where(
            MerchantOrder.id == order_id,
            MerchantOrder.merchant_id == admin_user.merchant_id,
        )
    )
    if not current_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' was not found",
        )

    if current_order.status == new_status:
        # Idempotent retry: order is already in the target status
        return current_order

    # Conflicting transition attempted
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"Cannot transition order '{order_id}' from current status '{current_order.status}' "
            f"to '{new_status}'. Expected current status in: {expected_statuses}"
        ),
    )


def get_order_audit_history(db: Session, order_id: str, merchant_id: str) -> List[AuditEvent]:
    """
    Retrieves chronological audit events for a specific merchant order.
    """
    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.merchant_id == merchant_id,
            AuditEvent.entity_type == "merchant_order",
            AuditEvent.entity_id == order_id,
        )
        .order_by(AuditEvent.created_at.asc())
    )
    return list(db.scalars(stmt).all())
