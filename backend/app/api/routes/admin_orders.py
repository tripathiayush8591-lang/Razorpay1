import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.order import (
    OrderResponse,
    AdminOrderListItem,
    AdminOrdersPageResponse,
    FulfillmentUpdateRequest,
    AuditEventResponse,
)
from app.services.orders import (
    list_admin_orders,
    get_admin_order_by_id,
    update_order_fulfillment_status,
    get_order_audit_history,
    to_order_response,
)

router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


@router.get("", response_model=ApiResponse[AdminOrdersPageResponse])
def get_admin_orders_endpoint(
    q: Optional[str] = Query(None, description="Search by order ID, customer name, email, phone, or razorpay order ID"),
    status: Optional[str] = Query(None, description="Filter by status (CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, PENDING_PAYMENT, or all)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    List all merchant orders with optional search and status filtering for admin.
    """
    orders, total = list_admin_orders(
        db=db,
        merchant_id=current_admin.merchant_id,
        status_filter=status,
        q=q,
        limit=limit,
        offset=offset,
    )

    items: List[AdminOrderListItem] = []
    for o in orders:
        try:
            snapshot_items = json.loads(o.items_snapshot_json or "[]")
            items_count = sum(it.get("quantity", 1) for it in snapshot_items)
        except Exception:
            items_count = 0

        is_paid = bool(o.paid_at or o.status in ["PAID", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"])
        payment_status = "PAID" if is_paid else "PENDING_PAYMENT"

        items.append(
            AdminOrderListItem(
                id=o.id,
                customer_name=o.customer_name,
                customer_email=o.customer_email,
                customer_phone=o.customer_phone,
                amount_paise=o.amount_paise,
                currency=o.currency,
                status=o.status,
                payment_status=payment_status,
                items_count=items_count,
                razorpay_order_id=o.razorpay_order_id,
                carrier=o.carrier,
                tracking_number=o.tracking_number,
                created_at=o.created_at,
                confirmed_at=o.confirmed_at,
            )
        )

    data = AdminOrdersPageResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=data)


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_admin_order_detail_endpoint(
    order_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive order detail for admin, including immutable items snapshot.
    """
    order = get_admin_order_by_id(db=db, order_id=order_id, merchant_id=current_admin.merchant_id)
    return ApiResponse(data=to_order_response(order))


@router.post("/{order_id}/fulfillment", response_model=ApiResponse[OrderResponse])
def update_admin_order_fulfillment_endpoint(
    order_id: str,
    payload: FulfillmentUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Transition fulfillment status (PROCESSING, SHIPPED, DELIVERED, CANCELLED).
    Enforces atomic state transition, race-safe idempotency, and audit trail.
    """
    order = update_order_fulfillment_status(
        db=db,
        order_id=order_id,
        new_status=payload.status,
        admin_user=current_admin,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        cancellation_reason=payload.cancellation_reason,
    )
    return ApiResponse(data=to_order_response(order))


@router.get("/{order_id}/audit", response_model=ApiResponse[List[AuditEventResponse]])
def get_admin_order_audit_endpoint(
    order_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve chronological audit trail for a specific merchant order.
    """
    # Ensure order belongs to merchant
    get_admin_order_by_id(db=db, order_id=order_id, merchant_id=current_admin.merchant_id)

    audit_events = get_order_audit_history(
        db=db,
        order_id=order_id,
        merchant_id=current_admin.merchant_id,
    )

    data: List[AuditEventResponse] = []
    for evt in audit_events:
        try:
            meta = json.loads(evt.metadata_json or "{}")
        except Exception:
            meta = {}
        data.append(
            AuditEventResponse(
                id=evt.id,
                merchant_id=evt.merchant_id,
                session_id=evt.session_id,
                actor_type=evt.actor_type,
                action=evt.action,
                entity_type=evt.entity_type,
                entity_id=evt.entity_id,
                metadata=meta,
                created_at=evt.created_at,
            )
        )

    return ApiResponse(data=data)
