import json
import uuid
import hmac
import hashlib
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.order import MerchantOrder
from app.models.audit import AuditEvent

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_inventory():
    """Ensure sufficient inventory for test runs."""
    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        if prod:
            prod.inventory_quantity = 50
            db.commit()
    yield


def helper_get_admin_token() -> str:
    """Logs in as seeded demo admin and returns bearer token."""
    res = client.post("/api/admin/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["data"]["token"]


def helper_create_confirmed_order(session_id: str, quantity: int = 1) -> dict:
    """Helper to initiate and verify an order end-to-end to reach CONFIRMED status."""
    # 1. Cart
    res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = res.json()["data"]["id"]

    # 2. Add Item
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_runpro_x2", "quantity": quantity},
        headers={"X-Session-ID": session_id},
    )

    # 3. Quote
    quote_res = client.post(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": session_id})
    quote = quote_res.json()["data"]

    # 4. Checkout
    checkout_res = client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"X-Session-ID": session_id},
        json={
            "customer_name": "Test Runner",
            "customer_email": "runner@example.com",
            "customer_phone": "+919876543210",
            "shipping_address": {
                "line1": "100 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560001",
                "country": "India",
            },
            "approved_total_paise": quote["total_paise"],
        },
    )
    assert checkout_res.status_code == 200, f"Checkout failed: {checkout_res.text}"
    checkout_data = checkout_res.json()["data"]

    # 5. Payment Verify with mock
    order_id = checkout_data["merchant_order_id"]
    rzp_order_id = checkout_data["razorpay_order_id"]
    rzp_payment_id = f"pay_{uuid.uuid4().hex[:14]}"

    msg = f"{rzp_order_id}|{rzp_payment_id}".encode("utf-8")
    sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    with patch("app.integrations.razorpay.razorpay_client.fetch_payment") as mock_fetch:
        mock_fetch.return_value = {
            "id": rzp_payment_id,
            "order_id": rzp_order_id,
            "status": "captured",
            "amount": quote["total_paise"],
        }
        verify_res = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": order_id,
                "razorpay_order_id": rzp_order_id,
                "razorpay_payment_id": rzp_payment_id,
                "razorpay_signature": sig,
            },
        )
        assert verify_res.status_code == 200, f"Verify failed: {verify_res.text}"

    # Return full order response
    get_res = client.get(f"/api/orders/{order_id}", headers={"X-Session-ID": session_id})
    assert get_res.status_code == 200
    return get_res.json()["data"]


# 1. Admin order listing requires authentication
def test_admin_order_list_requires_auth():
    res = client.get("/api/admin/orders")
    assert res.status_code == 401


# 2. Admin can list and search orders
def test_admin_can_list_and_search_orders():
    admin_token = helper_get_admin_token()
    session_id = f"sess_admin_list_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # List all
    res = client.get(
        "/api/admin/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

    # Search by order ID
    search_res = client.get(
        f"/api/admin/orders?q={order['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()["data"]
    assert any(item["id"] == order["id"] for item in search_data["items"])

    # Filter by status
    status_res = client.get(
        "/api/admin/orders?status=CONFIRMED",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert status_res.status_code == 200
    for item in status_res.json()["data"]["items"]:
        assert item["status"] == "CONFIRMED"


# 3. Admin order detail returns complete order with snapshot
def test_admin_order_detail_success():
    admin_token = helper_get_admin_token()
    session_id = f"sess_detail_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.get(
        f"/api/admin/orders/{order['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    detail = res.json()["data"]
    assert detail["id"] == order["id"]
    assert detail["customer_name"] == "Test Runner"
    assert detail["customer_email"] == "runner@example.com"
    assert detail["status"] == "CONFIRMED"
    assert detail["payment_status"] == "PAID"
    assert detail["items"][0]["sku"] == "RUN-X2-BLK-42"
    assert detail["shipping_address"]["city"] == "Bengaluru"


# 4. Guest order history returns own session orders
def test_guest_order_history_success():
    session_id = f"sess_guest_hist_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.get("/api/orders", headers={"X-Session-ID": session_id})
    assert res.status_code == 200
    orders = res.json()["data"]
    assert len(orders) >= 1
    assert any(o["id"] == order["id"] for o in orders)


# 5. Guest order history is isolated from other sessions
def test_guest_order_history_isolation():
    session_a = f"sess_iso_a_{uuid.uuid4().hex[:8]}"
    session_b = f"sess_iso_b_{uuid.uuid4().hex[:8]}"

    order_a = helper_create_confirmed_order(session_a)

    # Session B queries orders
    res_b = client.get("/api/orders", headers={"X-Session-ID": session_b})
    assert res_b.status_code == 200
    orders_b = res_b.json()["data"]
    assert not any(o["id"] == order_a["id"] for o in orders_b)


# 6. Guest cannot retrieve another session's order
def test_guest_cannot_view_foreign_order():
    session_a = f"sess_sec_a_{uuid.uuid4().hex[:8]}"
    session_b = f"sess_sec_b_{uuid.uuid4().hex[:8]}"

    order_a = helper_create_confirmed_order(session_a)

    # Session B attempts to view Session A's order
    res = client.get(f"/api/orders/{order_a['id']}", headers={"X-Session-ID": session_b})
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


# 7. Admin can retrieve any guest order
def test_admin_can_view_any_order():
    admin_token = helper_get_admin_token()
    session_a = f"sess_admin_view_{uuid.uuid4().hex[:8]}"
    order_a = helper_create_confirmed_order(session_a)

    # Admin calls guest endpoint with Bearer token
    res = client.get(
        f"/api/orders/{order_a['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["id"] == order_a["id"]


# 8. Immutable snapshot remains unchanged after catalog product price change
def test_immutable_snapshot_preserved_after_price_change():
    session_id = f"sess_snap_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)
    original_item_price = order["items"][0]["unit_price_paise"]

    # Change product price in catalog
    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        old_price = prod.price_paise
        prod.price_paise = 999900
        db.commit()

    try:
        # Re-fetch order
        res = client.get(f"/api/orders/{order['id']}", headers={"X-Session-ID": session_id})
        assert res.status_code == 200
        re_order = res.json()["data"]
        # Snapshot price must be the original price, not 999900
        assert re_order["items"][0]["unit_price_paise"] == original_item_price
        assert re_order["amount_paise"] == order["amount_paise"]
    finally:
        # Revert product price
        with SessionLocal() as db:
            prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
            prod.price_paise = old_price
            db.commit()


# 9. Valid CONFIRMED -> PROCESSING transition
def test_transition_confirmed_to_processing():
    admin_token = helper_get_admin_token()
    session_id = f"sess_proc_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    assert res.status_code == 200
    updated = res.json()["data"]
    assert updated["status"] == "PROCESSING"
    assert updated["processing_at"] is not None
    assert updated["payment_status"] == "PAID"


# 10. Valid PROCESSING -> SHIPPED transition
def test_transition_processing_to_shipped():
    admin_token = helper_get_admin_token()
    session_id = f"sess_ship_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # First to PROCESSING
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )

    # Then to SHIPPED
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "SHIPPED",
            "carrier": "BlueDart Express",
            "tracking_number": "BLR-98421",
        },
    )
    assert res.status_code == 200
    shipped = res.json()["data"]
    assert shipped["status"] == "SHIPPED"
    assert shipped["carrier"] == "BlueDart Express"
    assert shipped["tracking_number"] == "BLR-98421"
    assert shipped["shipped_at"] is not None


# 11. Valid SHIPPED -> DELIVERED transition
def test_transition_shipped_to_delivered():
    admin_token = helper_get_admin_token()
    session_id = f"sess_deliv_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # To PROCESSING
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    # To SHIPPED
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SHIPPED", "carrier": "RunCraft Fleet", "tracking_number": "TRK-100"},
    )
    # To DELIVERED
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "DELIVERED"},
    )
    assert res.status_code == 200
    delivered = res.json()["data"]
    assert delivered["status"] == "DELIVERED"
    assert delivered["delivered_at"] is not None


# 12. Invalid fulfillment transition rejected
def test_invalid_transition_rejected():
    admin_token = helper_get_admin_token()
    session_id = f"sess_inv_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # CONFIRMED -> DELIVERED directly (skipping PROCESSING and SHIPPED)
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "DELIVERED"},
    )
    assert res.status_code == 409
    assert "Cannot transition order" in res.json()["detail"]


# 13. Guest cannot mutate fulfillment status
def test_guest_cannot_mutate_fulfillment():
    session_id = f"sess_guest_mut_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"X-Session-ID": session_id},
        json={"status": "PROCESSING"},
    )
    assert res.status_code == 401


# 14. Admin can cancel CONFIRMED order
def test_admin_cancel_confirmed_order():
    admin_token = helper_get_admin_token()
    session_id = f"sess_cancel_conf_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "CANCELLED",
            "cancellation_reason": "Customer requested address change before dispatch",
        },
    )
    assert res.status_code == 200
    cancelled = res.json()["data"]
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["cancelled_at"] is not None
    assert cancelled["cancellation_reason"] == "Customer requested address change before dispatch"


# 15. Admin can cancel PROCESSING order
def test_admin_cancel_processing_order():
    admin_token = helper_get_admin_token()
    session_id = f"sess_cancel_proc_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # CONFIRMED -> PROCESSING
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )

    # PROCESSING -> CANCELLED
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "CANCELLED",
            "cancellation_reason": "Item damaged during warehouse packaging",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "CANCELLED"


# 16. Cancellation requires mandatory reason
def test_admin_cancel_requires_reason():
    admin_token = helper_get_admin_token()
    session_id = f"sess_cancel_no_reason_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CANCELLED", "cancellation_reason": ""},
    )
    assert res.status_code == 400
    assert "cancellation reason is required" in res.json()["detail"]


# 17. Cancellation does NOT restore inventory (MVP safety rule)
def test_cancellation_does_not_restore_inventory():
    admin_token = helper_get_admin_token()
    session_id = f"sess_cancel_stock_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # Read current stock
    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        stock_before_cancellation = prod.inventory_quantity

    # Cancel order
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "CANCELLED",
            "cancellation_reason": "Order cancelled - stock holds pending refund workflow",
        },
    )
    assert res.status_code == 200

    # Verify inventory is completely UNCHANGED
    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        stock_after_cancellation = prod.inventory_quantity

    assert stock_after_cancellation == stock_before_cancellation


# 18. Cannot cancel SHIPPED or DELIVERED order
def test_cannot_cancel_shipped_or_delivered_order():
    admin_token = helper_get_admin_token()
    session_id = f"sess_no_cancel_ship_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # Transition to SHIPPED
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SHIPPED", "carrier": "Express"},
    )

    # Attempt to cancel
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CANCELLED", "cancellation_reason": "Too late"},
    )
    assert res.status_code == 409


# 19. Cancelled order cannot be fulfilled
def test_cancelled_order_cannot_be_fulfilled():
    admin_token = helper_get_admin_token()
    session_id = f"sess_cancelled_locked_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # Cancel
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CANCELLED", "cancellation_reason": "Admin cancel"},
    )

    # Try to mark PROCESSING
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    assert res.status_code == 409


# 20. Inventory is NOT decremented during fulfillment transitions
def test_inventory_not_decremented_during_fulfillment():
    admin_token = helper_get_admin_token()
    session_id = f"sess_stock_fulfill_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        baseline_stock = prod.inventory_quantity

    # Run through PROCESSING, SHIPPED, DELIVERED
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SHIPPED", "carrier": "FastCourier"},
    )
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "DELIVERED"},
    )

    # Check stock after all transitions
    with SessionLocal() as db:
        prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        final_stock = prod.inventory_quantity

    assert final_stock == baseline_stock


# 21. Idempotent fulfillment action (repeated same-status request returns cleanly)
def test_idempotent_fulfillment_action():
    admin_token = helper_get_admin_token()
    session_id = f"sess_idemp_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # Mark PROCESSING first time
    res1 = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    assert res1.status_code == 200
    processing_at_1 = res1.json()["data"]["processing_at"]

    # Count audit events for order_processing_started
    with SessionLocal() as db:
        events_1 = db.query(AuditEvent).filter(
            AuditEvent.entity_id == order["id"],
            AuditEvent.action == "order_processing_started",
        ).count()
        assert events_1 == 1

    # Mark PROCESSING second time (idempotent duplicate retry)
    res2 = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    assert res2.status_code == 200
    processing_at_2 = res2.json()["data"]["processing_at"]

    # Verify timestamp and audit count were NOT duplicated
    assert processing_at_1 == processing_at_2
    with SessionLocal() as db:
        events_2 = db.query(AuditEvent).filter(
            AuditEvent.entity_id == order["id"],
            AuditEvent.action == "order_processing_started",
        ).count()
        assert events_2 == 1


# 22. Audit trail endpoint returns chronological events
def test_order_audit_trail_endpoint():
    admin_token = helper_get_admin_token()
    session_id = f"sess_audit_trail_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SHIPPED", "carrier": "ExpressAir", "tracking_number": "EXP-99"},
    )

    res = client.get(
        f"/api/admin/orders/{order['id']}/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    events = res.json()["data"]
    actions = [e["action"] for e in events]

    assert "payment_verified" in actions
    assert "order_confirmed" in actions
    assert "order_processing_started" in actions
    assert "order_shipped" in actions


# 23. Explicit payment vs fulfillment separation
def test_payment_vs_fulfillment_separation():
    admin_token = helper_get_admin_token()
    session_id = f"sess_sep_{uuid.uuid4().hex[:8]}"
    order = helper_create_confirmed_order(session_id)

    # Initial confirmed state
    assert order["payment_status"] == "PAID"
    assert order["status"] == "CONFIRMED"

    # In transit state
    client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PROCESSING"},
    )
    res = client.post(
        f"/api/admin/orders/{order['id']}/fulfillment",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SHIPPED", "carrier": "DHL", "tracking_number": "DHL-123"},
    )
    shipped = res.json()["data"]

    # Payment status remains PAID; fulfillment status is SHIPPED
    assert shipped["payment_status"] == "PAID"
    assert shipped["status"] == "SHIPPED"
    assert shipped["payment_details"]["provider"] == "razorpay"
    assert shipped["fulfillment"]["status"] == "SHIPPED"
