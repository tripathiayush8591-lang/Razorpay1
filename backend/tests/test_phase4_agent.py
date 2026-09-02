import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.session import SessionLocal
from app.models.audit import AuditEvent
from app.models.order import MerchantOrder
from app.models.payment import PaymentAttempt
from app.models.product import Product

client = TestClient(app)


def test_agent_chat_missing_or_placeholder_key_triggers_fallback():
    session_id = f"test_agent_{uuid.uuid4().hex[:8]}"

    # With empty/placeholder GEMINI_API_KEY, agent falls back gracefully and executes real commerce tools
    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Find carbon plate race shoes",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "CarbonSpeed Elite Racer" in data["message"] or "carbon" in data["message"].lower()
    assert len(data["tool_activity"]) > 0
    # Verified that search_products and check_inventory were executed
    activities = [a["activity"] for a in data["tool_activity"]]
    assert any("search_products" in a for a in activities)
    assert any("check_inventory" in a for a in activities)
    assert len(data["recommendations"]) >= 1
    assert data["recommendations"][0]["product"]["sku"] == "CARB-RACE-NEON-42"


def test_agent_chat_beginner_running_kit_intent():
    session_id = f"test_kit_{uuid.uuid4().hex[:8]}"

    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Build me a beginner running kit under ₹8,000",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]

    # 1. Natural language response explaining recommendation and budget compliance
    assert "beginner running kit" in data["message"].lower() or "8,000" in data["message"]
    assert data["approval_required"] is True

    # 2. Real tool activity trace
    activities = [a["activity"] for a in data["tool_activity"]]
    assert any("search_products" in a for a in activities)
    assert any("add_to_cart" in a for a in activities)
    assert any("get_final_quote" in a for a in activities)

    # 3. Product recommendations
    assert len(data["recommendations"]) >= 2
    rec_skus = [r["product"]["sku"] for r in data["recommendations"]]
    assert "RUN-X2-BLK-42" in rec_skus

    # 4. Authoritative cart and quote
    assert data["cart"] is not None
    assert len(data["cart"]["items"]) >= 2

    assert data["quote"] is not None
    assert data["quote"]["valid"] is True
    # Quote total must be strictly <= 8,000 INR (800,000 paise)
    assert data["quote"]["total_paise"] <= 800000
    assert data["quote"]["total_paise"] > 0


def test_agent_chat_add_hydration_flask_intent():
    session_id = f"test_flask_{uuid.uuid4().hex[:8]}"

    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Add hydration flask",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert "flask" in data["message"].lower() or "hydrorun" in data["message"].lower()
    assert data["cart"] is not None
    cart_skus = [item["product"]["sku"] for item in data["cart"]["items"]]
    assert "HYD-FLSK-500ML" in cart_skus
    assert data["quote"] is not None
    assert data["quote"]["valid"] is True
    assert data["approval_required"] is True


def test_agent_chat_multi_turn_history():
    session_id = f"test_multiturn_{uuid.uuid4().hex[:8]}"

    # First turn: Ask about shoes
    res1 = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Find carbon plate race shoes",
            "session_id": session_id,
        },
    )
    assert res1.status_code == 200

    # Second turn: Multi-turn "Add the socks too"
    res2 = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Add the socks too",
            "session_id": session_id,
            "history": [
                {"role": "user", "content": "Find carbon plate race shoes"},
                {"role": "assistant", "content": res1.json()["data"]["message"]},
            ],
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()["data"]

    assert "socks" in data2["message"].lower()
    cart_skus = [item["product"]["sku"] for item in data2["cart"]["items"]]
    assert "ACC-FLT-SCK-3PK" in cart_skus


def test_agent_chat_same_session_cart_binding():
    session_id = f"test_binding_{uuid.uuid4().hex[:8]}"

    # Step 1: User adds shoes from storefront directly via Cart API
    cart_res = client.post("/api/carts", headers={"X-Session-ID": session_id})
    cart_id = cart_res.json()["data"]["id"]

    client.post(
        f"/api/carts/{cart_id}/items",
        headers={"X-Session-ID": session_id},
        json={"product_id": "prod_runpro_x2", "quantity": 1},
    )

    # Step 2: User opens AI assistant with the same cart_id and says "Add hydration flask"
    chat_res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Add hydration flask",
            "session_id": session_id,
            "cart_id": cart_id,
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()["data"]

    # Step 3: Verify the cart has BOTH the manually added shoe AND the agent-added flask
    assert chat_data["cart"]["id"] == cart_id
    cart_skus = [item["product"]["sku"] for item in chat_data["cart"]["items"]]
    assert "RUN-X2-BLK-42" in cart_skus
    assert "HYD-FLSK-500ML" in cart_skus

    # Step 4: Verify querying the storefront cart endpoint returns the exact same merged state
    get_cart_res = client.get(f"/api/carts/{cart_id}", headers={"X-Session-ID": session_id})
    assert get_cart_res.status_code == 200
    storefront_skus = [item["product"]["sku"] for item in get_cart_res.json()["data"]["items"]]
    assert "RUN-X2-BLK-42" in storefront_skus
    assert "HYD-FLSK-500ML" in storefront_skus


def test_agent_chat_unauthorized_cart_access_rejected():
    session_a = f"test_agent_a_{uuid.uuid4().hex[:8]}"
    session_b = f"test_agent_b_{uuid.uuid4().hex[:8]}"

    # Session A creates a cart
    cart_a = client.post("/api/carts", headers={"X-Session-ID": session_a}).json()["data"]["id"]

    # Session B tries to call agent chat supplying Session A's cart_id
    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_b},
        json={
            "message": "Add hydration flask",
            "session_id": session_b,
            "cart_id": cart_a,
        },
    )
    # Must be rejected with HTTP 403 Forbidden
    assert res.status_code == 403


def test_agent_chat_authoritative_quote_reflects_live_price():
    session_id = f"test_price_change_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()

    try:
        # Create kit with RunPro X2 and Socks
        res = client.post(
            "/api/agent/chat",
            headers={"X-Session-ID": session_id},
            json={
                "message": "Build me a beginner running kit under ₹8,000",
                "session_id": session_id,
            },
        )
        assert res.status_code == 200
        initial_total = res.json()["data"]["quote"]["total_paise"]

        # Directly modify the product price in SQLite
        prod = db.scalar(select(Product).where(Product.sku == "RUN-X2-BLK-42"))
        assert prod is not None
        original_price = prod.price_paise
        prod.price_paise = original_price + 50000  # + ₹500
        db.commit()

        # Re-query agent or get quote tool
        cart_id = res.json()["data"]["cart"]["id"]
        quote_res = client.post(
            "/api/agent/tools/get-final-quote",
            headers={"X-Session-ID": session_id},
            json={"cart_id": cart_id},
        )
        assert quote_res.status_code == 200
        new_total = quote_res.json()["data"]["total_paise"]

        # Authoritative quote must reflect the price change
        assert new_total == initial_total + 50000

        # Restore original price
        prod.price_paise = original_price
        db.commit()
    finally:
        db.close()


def test_agent_chat_audit_event_logged():
    session_id = f"test_audit_{uuid.uuid4().hex[:8]}"

    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Find carbon plate race shoes",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200

    db = SessionLocal()
    try:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.session_id == session_id, AuditEvent.action == "agent_chat_turn")
            .order_by(AuditEvent.created_at.desc())
        )
        event = db.scalar(stmt)
        assert event is not None
        assert event.actor_type == "agent"
        assert "provider" in event.metadata_json
        assert "tools_executed" in event.metadata_json
    finally:
        db.close()


def test_approval_boundary_no_payment_or_order_created():
    session_id = f"test_boundary_{uuid.uuid4().hex[:8]}"

    res = client.post(
        "/api/agent/chat",
        headers={"X-Session-ID": session_id},
        json={
            "message": "Build me a beginner running kit under ₹8,000",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["approval_required"] is True

    cart_id = data["cart"]["id"]

    # Verify that NO merchant order or payment attempt exists in SQLite
    db = SessionLocal()
    try:
        order = db.scalar(select(MerchantOrder).where(MerchantOrder.cart_id == cart_id))
        assert order is None, "Phase 4 must NOT create merchant orders"

        payments = list(db.scalars(select(PaymentAttempt)).all())
        # No payment attempts should be associated with this cart
        assert len(payments) == 0, "Phase 4 must NOT initiate payment attempts"
    finally:
        db.close()


def test_agent_direct_tools_endpoints():
    session_id = f"test_direct_tools_{uuid.uuid4().hex[:8]}"

    # 1. Search products
    s_res = client.post(
        "/api/agent/tools/search-products",
        headers={"X-Session-ID": session_id},
        json={"q": "running", "max_price_paise": 600000},
    )
    assert s_res.status_code == 200
    products = s_res.json()["data"]
    assert len(products) > 0
    prod_id = products[0]["id"]

    # 2. Get product
    g_res = client.post(
        "/api/agent/tools/get-product",
        headers={"X-Session-ID": session_id},
        json={"product_id": prod_id},
    )
    assert g_res.status_code == 200
    assert g_res.json()["data"]["id"] == prod_id

    # 3. Add to cart
    cart_id = client.post("/api/carts", headers={"X-Session-ID": session_id}).json()["data"]["id"]
    a_res = client.post(
        "/api/agent/tools/add-to-cart",
        headers={"X-Session-ID": session_id},
        json={"cart_id": cart_id, "product_id": prod_id, "quantity": 2},
    )
    assert a_res.status_code == 200
    cart_data = a_res.json()["data"]
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 2
    item_id = cart_data["items"][0]["id"]

    # 4. Get quote
    q_res = client.post(
        "/api/agent/tools/get-final-quote",
        headers={"X-Session-ID": session_id},
        json={"cart_id": cart_id},
    )
    assert q_res.status_code == 200
    assert q_res.json()["data"]["valid"] is True
    assert q_res.json()["data"]["subtotal_paise"] > 0

    # 5. Remove from cart
    r_res = client.post(
        "/api/agent/tools/remove-from-cart",
        headers={"X-Session-ID": session_id},
        json={"cart_id": cart_id, "item_id": item_id},
    )
    assert r_res.status_code == 200
    assert len(r_res.json()["data"]["items"]) == 0
