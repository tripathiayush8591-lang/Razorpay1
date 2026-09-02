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
from app.models.cart import Cart
from app.models.order import MerchantOrder
from app.models.payment import PaymentAttempt
from app.models.audit import AuditEvent
from app.integrations.razorpay import razorpay_client, RazorpayIntegrationError

client = TestClient(app)


def helper_setup_cart_with_item(session_id: str, quantity: int = 1):
    """Helper to create an active cart with the seeded RunPro X2 product."""
    res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = res.json()["data"]["id"]

    add_res = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_runpro_x2", "quantity": quantity},
        headers={"X-Session-ID": session_id},
    )
    assert add_res.status_code == 200

    quote_res = client.post(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": session_id})
    assert quote_res.status_code == 200
    quote = quote_res.json()["data"]

    return cart_id, quote


# 1. Checkout requires valid guest session
def test_checkout_requires_session():
    res = client.post("/api/carts/cart_dummy/checkout", json={
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_phone": "+919999999999",
        "shipping_address": {
            "line1": "123 Street",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
        },
        "approved_total_paise": 500000,
    })
    assert res.status_code == 400
    assert "Session identifier is required" in res.json()["detail"]


# 2. Guest cannot checkout another session's cart
def test_guest_cannot_checkout_other_session_cart():
    session_a = f"sess_a_{uuid.uuid4().hex[:8]}"
    session_b = f"sess_b_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_a)

    res = client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"X-Session-ID": session_b},
        json={
            "customer_name": "Attacker",
            "customer_email": "attacker@example.com",
            "customer_phone": "+919999999999",
            "shipping_address": {
                "line1": "Fake St",
                "city": "FakeCity",
                "state": "FakeState",
                "postal_code": "123456",
            },
            "approved_total_paise": quote["total_paise"],
        },
    )
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


# 3. Empty cart rejected
def test_empty_cart_checkout_rejected():
    session_id = f"sess_empty_{uuid.uuid4().hex[:8]}"
    cart_res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = cart_res.json()["data"]["id"]

    res = client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"X-Session-ID": session_id},
        json={
            "customer_name": "Buyer",
            "customer_email": "buyer@example.com",
            "customer_phone": "+919999999999",
            "shipping_address": {
                "line1": "123 St",
                "city": "City",
                "state": "State",
                "postal_code": "123456",
            },
            "approved_total_paise": 1000,
        },
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# 4. Inactive product rejected
def test_inactive_product_rejected():
    session_id = f"sess_inact_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    db = SessionLocal()
    prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    original_active = prod.active
    try:
        prod.active = False
        db.commit()

        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        assert res.status_code == 400
    finally:
        prod.active = original_active
        db.commit()
        db.close()


# 5. Insufficient inventory rejected
def test_insufficient_inventory_rejected():
    session_id = f"sess_stock_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    db = SessionLocal()
    prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    orig_stock = prod.inventory_quantity
    try:
        prod.inventory_quantity = 0
        db.commit()

        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        assert res.status_code == 400
        assert "out of stock" in res.json()["detail"].lower()
    finally:
        prod.inventory_quantity = orig_stock
        db.commit()
        db.close()


# 6 & 7. Fresh quote is authoritative & stale approved_total rejected
def test_stale_approved_total_rejected():
    session_id = f"sess_stale_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    # Submit an approved amount that does not match current backend quote
    res = client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"X-Session-ID": session_id},
        json={
            "customer_name": "Buyer",
            "customer_email": "buyer@example.com",
            "customer_phone": "+919999999999",
            "shipping_address": {
                "line1": "123 St",
                "city": "City",
                "state": "State",
                "postal_code": "123456",
            },
            "approved_total_paise": quote["total_paise"] - 1000,  # tampered / stale
        },
    )
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert detail["code"] == "QUOTE_EXPIRED_OR_CHANGED"
    assert detail["authoritative_total_paise"] == quote["total_paise"]


# 8, 9, 10. Razorpay order created with authoritative quote, MerchantOrder created with immutable snapshot
def test_checkout_initiation_success():
    session_id = f"sess_ok_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    mock_rzp_order = {
        "id": f"order_rzp_{uuid.uuid4().hex[:8]}",
        "amount": quote["total_paise"],
        "currency": "INR",
        "status": "created",
    }

    with patch.object(razorpay_client, "create_order", return_value=mock_rzp_order) as mock_create:
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Aarav Sharma",
                "customer_email": "aarav@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "42 Indiranagar 100ft Road",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                    "country": "India",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]

        # Verify Razorpay create was called with authoritative quote amount
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["amount_paise"] == quote["total_paise"]
        assert call_kwargs["currency"] == "INR"

        # Verify response fields
        assert data["razorpay_order_id"] == mock_rzp_order["id"]
        assert data["amount_paise"] == quote["total_paise"]
        assert data["currency"] == "INR"
        assert "merchant_order_id" in data

        # Verify DB MerchantOrder
        db = SessionLocal()
        order = db.query(MerchantOrder).filter(MerchantOrder.id == data["merchant_order_id"]).first()
        assert order is not None
        assert order.status == "PENDING_PAYMENT"
        assert order.razorpay_order_id == mock_rzp_order["id"]

        # Verify immutable snapshot exists and has item details
        snapshot = json.loads(order.items_snapshot_json)
        assert len(snapshot) > 0
        assert snapshot[0]["product_id"] == "prod_runpro_x2"
        assert snapshot[0]["unit_price_paise"] > 0
        db.close()


# 11. Razorpay order creation failure handled safely
def test_razorpay_creation_failure_handled():
    session_id = f"sess_fail_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    with patch.object(razorpay_client, "create_order", side_effect=RazorpayIntegrationError("Gateway unavailable", 502)):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        assert res.status_code == 502
        assert "Gateway unavailable" in res.json()["detail"]


# 12, 17, 19, 24. Valid signature, captured payment, inventory decrement, cart conversion
def test_valid_payment_verification_confirms_order():
    session_id = f"sess_pay_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id, quantity=1)

    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"
    mock_rzp_pay_id = f"pay_{uuid.uuid4().hex[:8]}"
    dummy_sig = "valid_test_signature_hex"

    db = SessionLocal()
    prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    initial_stock = prod.inventory_quantity
    db.close()

    # 1. Initiate checkout
    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Aarav Sharma",
                "customer_email": "aarav@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "42 Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    # 2. Verify payment with mocked valid signature and captured provider payment
    mock_payment_info = {
        "id": mock_rzp_pay_id,
        "order_id": mock_rzp_order_id,
        "amount": quote["total_paise"],
        "status": "captured",
    }

    with patch.object(razorpay_client, "verify_payment_signature", return_value=True), \
         patch.object(razorpay_client, "fetch_payment", return_value=mock_payment_info):
        verify_res = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": mock_rzp_pay_id,
                "razorpay_signature": dummy_sig,
            },
        )
        assert verify_res.status_code == 200
        v_data = verify_res.json()["data"]
        assert v_data["status"] == "CONFIRMED"
        assert v_data["order_id"] == merchant_order_id

    # 3. Check DB state: order CONFIRMED, inventory decremented by 1, cart converted
    db = SessionLocal()
    order = db.query(MerchantOrder).filter(MerchantOrder.id == merchant_order_id).first()
    assert order.status == "CONFIRMED"
    assert order.paid_at is not None
    assert order.confirmed_at is not None

    prod_after = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    assert prod_after.inventory_quantity == initial_stock - 1

    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    assert cart.status == "converted"
    db.close()


# 13. Invalid signature rejected
def test_invalid_signature_rejected():
    session_id = f"sess_bad_sig_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"

    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    with patch.object(razorpay_client, "verify_payment_signature", return_value=False):
        verify_res = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": "pay_fake",
                "razorpay_signature": "bad_sig",
            },
        )
        assert verify_res.status_code == 400
        assert "signature verification failed" in verify_res.json()["detail"].lower()


# 14 & 15. Client-supplied wrong Razorpay order ID / mismatched order rejected
def test_order_id_mismatch_rejected():
    session_id = f"sess_mismatch_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"

    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    verify_res = client.post(
        "/api/payments/razorpay/verify",
        headers={"X-Session-ID": session_id},
        json={
            "merchant_order_id": merchant_order_id,
            "razorpay_order_id": "order_wrong_rzp_123",  # Mismatch
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "sig_123",
        },
    )
    assert verify_res.status_code == 400
    assert "Mismatched Razorpay order ID" in verify_res.json()["detail"]


# 16. Uncaptured payment does not become PAID
def test_uncaptured_payment_does_not_become_paid():
    session_id = f"sess_uncap_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"

    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    mock_payment_failed_info = {
        "id": "pay_fail_123",
        "order_id": mock_rzp_order_id,
        "amount": quote["total_paise"],
        "status": "failed",  # Not captured
    }

    with patch.object(razorpay_client, "verify_payment_signature", return_value=True), \
         patch.object(razorpay_client, "fetch_payment", return_value=mock_payment_failed_info):
        verify_res = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": "pay_fail_123",
                "razorpay_signature": "valid_sig",
            },
        )
        assert verify_res.status_code == 400
        assert "not in captured state" in verify_res.json()["detail"].lower()


# 18. Payment failure does not decrement inventory
def test_payment_failure_does_not_decrement_inventory():
    db = SessionLocal()
    prod = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    stock_before = prod.inventory_quantity
    db.close()

    # Call failed signature
    session_id = f"sess_inv_fail_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"

    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    with patch.object(razorpay_client, "verify_payment_signature", return_value=False):
        client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": "pay_f",
                "razorpay_signature": "invalid_sig",
            },
        )

    db = SessionLocal()
    prod_after = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
    assert prod_after.inventory_quantity == stock_before
    db.close()


# 20. Duplicate verification is idempotent
def test_duplicate_verification_is_idempotent():
    session_id = f"sess_idem_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"
    mock_rzp_pay_id = f"pay_{uuid.uuid4().hex[:8]}"

    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        merchant_order_id = res.json()["data"]["merchant_order_id"]

    mock_payment_info = {
        "id": mock_rzp_pay_id,
        "order_id": mock_rzp_order_id,
        "amount": quote["total_paise"],
        "status": "captured",
    }

    with patch.object(razorpay_client, "verify_payment_signature", return_value=True), \
         patch.object(razorpay_client, "fetch_payment", return_value=mock_payment_info):
        res1 = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": mock_rzp_pay_id,
                "razorpay_signature": "valid_sig",
            },
        )
        assert res1.status_code == 200

        # Second identical verification request: returns success idempotently
        res2 = client.post(
            "/api/payments/razorpay/verify",
            headers={"X-Session-ID": session_id},
            json={
                "merchant_order_id": merchant_order_id,
                "razorpay_order_id": mock_rzp_order_id,
                "razorpay_payment_id": mock_rzp_pay_id,
                "razorpay_signature": "valid_sig",
            },
        )
        assert res2.status_code == 200
        assert res2.json()["data"]["status"] == "CONFIRMED"


# 21 & 22. Webhook idempotency and signature validation
def test_webhook_processing_and_idempotency():
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    rzp_order_id = f"order_wh_{uuid.uuid4().hex[:8]}"
    rzp_pay_id = f"pay_wh_{uuid.uuid4().hex[:8]}"

    # Create dummy merchant order for this rzp_order_id
    db = SessionLocal()
    order = MerchantOrder(
        id=f"order_{uuid.uuid4().hex[:8]}",
        merchant_id="merchant_runcraft_prime",
        customer_name="WH User",
        customer_email="wh@example.com",
        customer_phone="+919999999999",
        shipping_address_json="{}",
        items_snapshot_json="[]",
        amount_paise=500000,
        currency="INR",
        status="PENDING_PAYMENT",
        razorpay_order_id=rzp_order_id,
    )
    db.add(order)
    db.commit()
    db.close()

    payload_dict = {
        "entity": "event",
        "account_id": "acc_123",
        "event": "payment.captured",
        "id": event_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": rzp_pay_id,
                    "order_id": rzp_order_id,
                    "amount": 500000,
                    "status": "captured",
                }
            }
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")

    # 1. Invalid signature returns 400
    res_bad = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": "bad_sig", "X-Razorpay-Event-Id": event_id},
    )
    assert res_bad.status_code == 400

    # 2. Valid signature succeeds
    valid_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    res_ok = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig, "X-Razorpay-Event-Id": event_id},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["data"]["status"] == "processed"

    # Verify order transitioned to CONFIRMED
    db = SessionLocal()
    o = db.query(MerchantOrder).filter(MerchantOrder.razorpay_order_id == rzp_order_id).first()
    assert o.status == "CONFIRMED"
    db.close()

    # 3. Duplicate event ID is acknowledged without error
    res_dup = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig, "X-Razorpay-Event-Id": event_id},
    )
    assert res_dup.status_code == 200
    assert res_dup.json()["data"]["status"] == "duplicate_acknowledged"


# 23. Out of order webhook cannot corrupt paid state
def test_out_of_order_webhook_cannot_corrupt_paid_state():
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    event_id = f"evt_stale_{uuid.uuid4().hex[:12]}"
    rzp_order_id = f"order_stale_{uuid.uuid4().hex[:8]}"

    db = SessionLocal()
    order = MerchantOrder(
        id=f"order_{uuid.uuid4().hex[:8]}",
        merchant_id="merchant_runcraft_prime",
        customer_name="WH User",
        customer_email="wh@example.com",
        customer_phone="+919999999999",
        shipping_address_json="{}",
        items_snapshot_json="[]",
        amount_paise=500000,
        currency="INR",
        status="CONFIRMED",  # Already paid
        razorpay_order_id=rzp_order_id,
    )
    db.add(order)
    db.commit()
    db.close()

    # Delayed payment.failed webhook arrives
    payload_dict = {
        "entity": "event",
        "event": "payment.failed",
        "id": event_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_stale",
                    "order_id": rzp_order_id,
                }
            }
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    res = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": event_id},
    )
    assert res.status_code == 200

    # Confirm order remained CONFIRMED and was not downgraded
    db = SessionLocal()
    o = db.query(MerchantOrder).filter(MerchantOrder.razorpay_order_id == rzp_order_id).first()
    assert o.status == "CONFIRMED"
    db.close()


# 25 & 26. Order retrieval session protection & successful retrieval
def test_order_retrieval_session_protection():
    session_a = f"sess_ret_a_{uuid.uuid4().hex[:8]}"
    session_b = f"sess_ret_b_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_a)

    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"
    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_a},
            json={
                "customer_name": "Aarav Sharma",
                "customer_email": "aarav@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "42 Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        order_id = res.json()["data"]["merchant_order_id"]

    # Session A (owner) can retrieve order
    res_a = client.get(f"/api/orders/{order_id}", headers={"X-Session-ID": session_a})
    assert res_a.status_code == 200
    order_data = res_a.json()["data"]
    assert order_data["id"] == order_id
    assert order_data["customer_name"] == "Aarav Sharma"
    assert len(order_data["items"]) > 0

    # Session B cannot retrieve order (403 Forbidden)
    res_b = client.get(f"/api/orders/{order_id}", headers={"X-Session-ID": session_b})
    assert res_b.status_code == 403
    assert "Forbidden" in res_b.json()["detail"]


# 27. Audit events created
def test_audit_events_created():
    session_id = f"sess_audit_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)

    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"
    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        order_id = res.json()["data"]["merchant_order_id"]

    db = SessionLocal()
    audit = db.query(AuditEvent).filter(
        AuditEvent.entity_id == order_id,
        AuditEvent.action == "checkout_initiated",
    ).first()
    assert audit is not None
    assert audit.actor_type == "shopper"
    db.close()


# 28. Razorpay secret never appears in API responses
def test_razorpay_secret_never_exposed():
    session_id = f"sess_sec_{uuid.uuid4().hex[:8]}"
    cart_id, quote = helper_setup_cart_with_item(session_id)
    secret = settings.RAZORPAY_KEY_SECRET

    mock_rzp_order_id = f"order_rzp_{uuid.uuid4().hex[:8]}"
    with patch.object(razorpay_client, "create_order", return_value={"id": mock_rzp_order_id, "amount": quote["total_paise"], "currency": "INR"}):
        res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "+919999999999",
                "shipping_address": {
                    "line1": "123 St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "123456",
                },
                "approved_total_paise": quote["total_paise"],
            },
        )
        assert secret not in res.text
        order_id = res.json()["data"]["merchant_order_id"]

        order_res = client.get(f"/api/orders/{order_id}", headers={"X-Session-ID": session_id})
        assert secret not in order_res.text
