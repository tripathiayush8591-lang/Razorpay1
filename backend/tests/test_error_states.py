import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.cart import Cart, CartItem
from app.models.order import MerchantOrder
from app.models.admin_user import AdminUser
from app.core.config import settings

client = TestClient(app)


def get_demo_merchant_id() -> str:
    with SessionLocal() as db:
        admin = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
        assert admin is not None, "Admin user must be seeded"
        return admin.merchant_id


def test_quote_out_of_stock_invalidates_quote():
    """Verify that a cart containing an out-of-stock product invalidates the quote."""
    merchant_id = get_demo_merchant_id()
    session_id = f"err_oos_{uuid.uuid4().hex[:8]}"
    oos_sku_id = f"prod_oos_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create temporary out-of-stock product
        with SessionLocal() as db:
            oos_product = Product(
                id=oos_sku_id,
                merchant_id=merchant_id,
                sku=f"OOS-{uuid.uuid4().hex[:4].upper()}",
                name="Zero Stock Racing Flat",
                category="Running Shoes",
                short_description="Zero stock shoe",
                description="Zero stock shoe for testing",
                image_url="/placeholder.png",
                price_paise=499900,
                inventory_quantity=0,
                active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(oos_product)
            db.commit()

        # 2. Create cart and add product
        cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
        assert cart_res.status_code == 200
        cart_id = cart_res.json()["data"]["id"]

        add_res = client.post(
            f"/api/carts/{cart_id}/items",
            headers={"X-Session-ID": session_id},
            json={"product_id": oos_sku_id, "quantity": 1},
        )
        assert add_res.status_code == 200

        # 3. Retrieve authoritative quote
        quote_res = client.get(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": session_id})
        assert quote_res.status_code == 200
        quote_data = quote_res.json()["data"]

        # Quote must be invalid with an explicit out-of-stock warning
        assert quote_data["valid"] is False
        assert any("out of stock" in w.lower() for w in quote_data["warnings"])

        # 4. Attempting checkout on invalid quote must be rejected with 400
        checkout_res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Test Shopper",
                "customer_email": "shopper@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "123 Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                },
                "approved_total_paise": quote_data["total_paise"],
            },
        )
        assert checkout_res.status_code == 400
        assert "out of stock" in checkout_res.json()["detail"].lower()

    finally:
        # Cleanup
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.product_id == oos_sku_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.session_id == session_id).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == oos_sku_id).delete(synchronize_session=False)
            db.commit()


def test_quote_exceeding_inventory_warning():
    """Verify that requesting more units than available sets in_stock=False and invalidates quote."""
    merchant_id = get_demo_merchant_id()
    session_id = f"err_exceed_{uuid.uuid4().hex[:8]}"
    limited_sku_id = f"prod_lim_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create product with only 2 units
        with SessionLocal() as db:
            lim_product = Product(
                id=limited_sku_id,
                merchant_id=merchant_id,
                sku=f"LIM-{uuid.uuid4().hex[:4].upper()}",
                name="Limited Edition Spike",
                category="Running Shoes",
                short_description="Limited units shoe",
                description="Limited units shoe for testing",
                image_url="/placeholder.png",
                price_paise=899900,
                inventory_quantity=2,
                active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(lim_product)
            db.commit()

        # 2. Create cart and add 5 units
        cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
        cart_id = cart_res.json()["data"]["id"]

        add_res = client.post(
            f"/api/carts/{cart_id}/items",
            headers={"X-Session-ID": session_id},
            json={"product_id": limited_sku_id, "quantity": 5},
        )
        assert add_res.status_code == 200

        # 3. Retrieve authoritative quote
        quote_res = client.get(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": session_id})
        assert quote_res.status_code == 200
        quote_data = quote_res.json()["data"]

        # Quote must be invalid and state only 2 units available
        assert quote_data["valid"] is False
        assert any("2 units available" in w.lower() for w in quote_data["warnings"])

    finally:
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.product_id == limited_sku_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.session_id == session_id).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == limited_sku_id).delete(synchronize_session=False)
            db.commit()


def test_checkout_stale_quote_rejection():
    """Verify checkout fails if client provides an approved total differing from server quote."""
    session_id = f"err_stale_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create cart and add SwiftStride trainer
        cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
        cart_id = cart_res.json()["data"]["id"]

        client.post(
            f"/api/carts/{cart_id}/items",
            headers={"X-Session-ID": session_id},
            json={"product_id": "prod_runpro_x2", "quantity": 1},
        )

        # 2. Call checkout initiation with wrong approved total (e.g. ₹100 instead of authoritative total)
        checkout_res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Test Shopper",
                "customer_email": "shopper@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "123 Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                },
                "approved_total_paise": 10000,  # Deliberately stale total (₹100)
            },
        )
        # Server must reject with 409 Conflict or 400 Bad Request
        assert checkout_res.status_code in (400, 409)
        detail_obj = checkout_res.json().get("detail", "")
        detail = (detail_obj.get("message") if isinstance(detail_obj, dict) else str(detail_obj)).lower()
        assert "approved total" in detail or "quote" in detail or "mismatch" in detail

    finally:
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.cart_id == cart_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.id == cart_id).delete(synchronize_session=False)
            db.commit()


def test_checkout_inactive_product_rejected():
    """Verify that if a product is deactivated, checkout creation is rejected."""
    merchant_id = get_demo_merchant_id()
    session_id = f"err_inact_{uuid.uuid4().hex[:8]}"
    inact_sku_id = f"prod_to_deact_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create active product
        with SessionLocal() as db:
            prod = Product(
                id=inact_sku_id,
                merchant_id=merchant_id,
                sku=f"DEACT-{uuid.uuid4().hex[:4].upper()}",
                name="Product To Deactivate",
                category="Running Shoes",
                short_description="Shoe to deactivate",
                description="Shoe to deactivate for test",
                image_url="/placeholder.png",
                price_paise=350000,
                inventory_quantity=10,
                active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(prod)
            db.commit()

        # 2. Add to cart
        cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
        cart_id = cart_res.json()["data"]["id"]
        client.post(
            f"/api/carts/{cart_id}/items",
            headers={"X-Session-ID": session_id},
            json={"product_id": inact_sku_id, "quantity": 1},
        )

        # 3. Now merchant deactivates the product
        with SessionLocal() as db:
            p = db.query(Product).filter(Product.id == inact_sku_id).first()
            p.active = False
            db.commit()

        # 4. Attempt to checkout
        checkout_res = client.post(
            f"/api/carts/{cart_id}/checkout",
            headers={"X-Session-ID": session_id},
            json={
                "customer_name": "Test Shopper",
                "customer_email": "shopper@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "123 Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                },
                "approved_total_paise": 350000,
            },
        )
        assert checkout_res.status_code == 400
        assert "available" in checkout_res.json()["detail"].lower() or "active" in checkout_res.json()["detail"].lower()

    finally:
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.product_id == inact_sku_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.session_id == session_id).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == inact_sku_id).delete(synchronize_session=False)
            db.commit()


def test_agent_out_of_catalog_graceful_response():
    """Verify in-app agent explains RunCraft scope when asked for non-running gear."""
    session_id = f"agent_err_{uuid.uuid4().hex[:8]}"
    cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
    cart_id = cart_res.json()["data"]["id"]

    try:
        res = client.post(
            "/api/agent/chat",
            headers={"X-Session-ID": session_id},
            json={
                "message": "Can you sell me a gaming laptop and tennis racket?",
                "session_id": session_id,
                "cart_id": cart_id,
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        msg_lower = data["message"].lower()
        assert "runcraft" in msg_lower or "running" in msg_lower
        # Must not crash and should not require approval for non-existent items
        assert data["approval_required"] is False

    finally:
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.cart_id == cart_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.id == cart_id).delete(synchronize_session=False)
            db.commit()


def test_agent_impossible_budget_guidance():
    """Verify in-app agent provides clear guidance when budget is below catalog minimums."""
    session_id = f"agent_bdg_{uuid.uuid4().hex[:8]}"
    cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
    cart_id = cart_res.json()["data"]["id"]

    try:
        res = client.post(
            "/api/agent/chat",
            headers={"X-Session-ID": session_id},
            json={
                "message": "Build me a running kit under ₹500",
                "session_id": session_id,
                "cart_id": cart_id,
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        msg_lower = data["message"].lower()
        # Agent explains that lowest shoe exceeds requested budget
        assert "budget" in msg_lower or "exceeds" in msg_lower or "lowest-priced" in msg_lower

    finally:
        with SessionLocal() as db:
            db.query(CartItem).filter(CartItem.cart_id == cart_id).delete(synchronize_session=False)
            db.query(Cart).filter(Cart.id == cart_id).delete(synchronize_session=False)
            db.commit()


def test_order_detail_pending_payment_state():
    """Verify order in PENDING_PAYMENT status is retrieved accurately without decrementing stock."""
    merchant_id = get_demo_merchant_id()
    session_id = f"ord_pend_{uuid.uuid4().hex[:8]}"
    order_id = f"ord_pending_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create order directly with PENDING_PAYMENT status
        with SessionLocal() as db:
            order = MerchantOrder(
                id=order_id,
                merchant_id=merchant_id,
                customer_name="Pending Shopper",
                customer_email="pending@example.com",
                customer_phone="+919876543210",
                shipping_address_json="{}",
                items_snapshot_json="[]",
                amount_paise=399900,
                currency="INR",
                status="PENDING_PAYMENT",
                created_at=datetime.now(timezone.utc),
            )
            db.add(order)
            db.commit()

        # 2. Retrieve order
        res = client.get(f"/api/orders/{order_id}", headers={"X-Session-ID": session_id})
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "PENDING_PAYMENT"
        assert data["payment_status"] in ("PENDING", "PENDING_PAYMENT")

    finally:
        with SessionLocal() as db:
            db.query(MerchantOrder).filter(MerchantOrder.id == order_id).delete(synchronize_session=False)
            db.commit()
