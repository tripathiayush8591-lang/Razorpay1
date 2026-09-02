import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.product import Product

client = TestClient(app)


def test_cart_lifecycle_idempotent():
    session_id = f"test_sess_{uuid.uuid4().hex[:8]}"

    # First call: creates cart
    res1 = client.post("/api/carts", json={"session_id": session_id})
    assert res1.status_code == 200
    cart1 = res1.json()["data"]
    assert cart1["id"].startswith("cart_")
    assert cart1["session_id"] == session_id
    assert cart1["status"] == "active"
    assert len(cart1["items"]) == 0

    # Second call with same session_id: returns same cart (idempotent get-or-create)
    res2 = client.post("/api/carts", json={"session_id": session_id})
    assert res2.status_code == 200
    cart2 = res2.json()["data"]
    assert cart2["id"] == cart1["id"]

    # Also works with X-Session-ID header
    res3 = client.post("/api/carts", headers={"X-Session-ID": session_id})
    assert res3.status_code == 200
    assert res3.json()["data"]["id"] == cart1["id"]


def test_cart_ownership_security():
    session_a = f"test_sess_a_{uuid.uuid4().hex[:8]}"
    session_b = f"test_sess_b_{uuid.uuid4().hex[:8]}"

    # Create cart for session A
    res_a = client.post("/api/carts", json={"session_id": session_a})
    cart_id = res_a.json()["data"]["id"]

    # Session A can read it
    read_a = client.get(f"/api/carts/{cart_id}", headers={"X-Session-ID": session_a})
    assert read_a.status_code == 200

    # Session B attempting to read session A's cart is 403 Forbidden
    read_b = client.get(f"/api/carts/{cart_id}", headers={"X-Session-ID": session_b})
    assert read_b.status_code == 403
    assert "Forbidden" in read_b.json()["detail"]

    # Session B attempting to mutate items in session A's cart is 403 Forbidden
    add_b = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_runpro_x2", "quantity": 1},
        headers={"X-Session-ID": session_b},
    )
    assert add_b.status_code == 403

    # Session B attempting to request quote for session A's cart is 403 Forbidden
    quote_b = client.post(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": session_b})
    assert quote_b.status_code == 403


def test_cart_item_mutations():
    session_id = f"test_sess_mut_{uuid.uuid4().hex[:8]}"
    cart_res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = cart_res.json()["data"]["id"]

    headers = {"X-Session-ID": session_id}

    # 1. Add item (prod_runpro_x2, qty 1)
    add1 = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_runpro_x2", "quantity": 1},
        headers=headers,
    )
    assert add1.status_code == 200
    cart = add1.json()["data"]
    assert len(cart["items"]) == 1
    item = cart["items"][0]
    assert item["product_id"] == "prod_runpro_x2"
    assert item["quantity"] == 1
    item_id = item["id"]

    # 2. Add same item again (qty 2) -> increments quantity to 3
    add2 = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_runpro_x2", "quantity": 2},
        headers=headers,
    )
    assert add2.status_code == 200
    cart = add2.json()["data"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3

    # 3. PATCH item quantity to 5
    patch1 = client.patch(
        f"/api/carts/{cart_id}/items/{item_id}",
        json={"quantity": 5},
        headers=headers,
    )
    assert patch1.status_code == 200
    assert patch1.json()["data"]["items"][0]["quantity"] == 5

    # 4. PATCH quantity to 0 -> removes item
    patch0 = client.patch(
        f"/api/carts/{cart_id}/items/{item_id}",
        json={"quantity": 0},
        headers=headers,
    )
    assert patch0.status_code == 200
    assert len(patch0.json()["data"]["items"]) == 0

    # 5. Add another item and DELETE it by cart_item_id
    add_flask = client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_flask_500", "quantity": 2},
        headers=headers,
    )
    assert add_flask.status_code == 200
    flask_item_id = add_flask.json()["data"]["items"][0]["id"]

    delete_res = client.delete(
        f"/api/carts/{cart_id}/items/{flask_item_id}",
        headers=headers,
    )
    assert delete_res.status_code == 200
    assert len(delete_res.json()["data"]["items"]) == 0


def test_quote_authoritative_live_price():
    """
    Acceptance Criterion:
    Changing a SKU price after it was added to cart is reflected in the final quote.
    """
    session_id = f"test_sess_quote_{uuid.uuid4().hex[:8]}"
    headers = {"X-Session-ID": session_id}

    cart_res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = cart_res.json()["data"]["id"]

    # Fetch current price of prod_aerovent_singlet
    prod_res = client.get("/api/products/prod_aerovent_singlet")
    assert prod_res.status_code == 200
    original_price = prod_res.json()["data"]["price_paise"]

    # Add to cart
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_aerovent_singlet", "quantity": 2},
        headers=headers,
    )

    # First quote at original price
    q1 = client.post(f"/api/carts/{cart_id}/quote", headers=headers)
    assert q1.status_code == 200
    data1 = q1.json()["data"]
    assert data1["items"][0]["unit_price_paise"] == original_price
    assert data1["subtotal_paise"] == original_price * 2

    # Change product price directly in the database (simulate admin SKU update)
    new_price = original_price + 30000  # + ₹300
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == "prod_aerovent_singlet").first()
        assert p is not None
        p.price_paise = new_price
        db.commit()

        # Re-request quote: It MUST revalidate and reflect the new price!
        q2 = client.post(f"/api/carts/{cart_id}/quote", headers=headers)
        assert q2.status_code == 200
        data2 = q2.json()["data"]
        assert data2["items"][0]["unit_price_paise"] == new_price
        assert data2["subtotal_paise"] == new_price * 2
    finally:
        # Restore original price
        p = db.query(Product).filter(Product.id == "prod_aerovent_singlet").first()
        if p:
            p.price_paise = original_price
            db.commit()
        db.close()


def test_quote_inventory_validation():
    session_id = f"test_sess_inv_{uuid.uuid4().hex[:8]}"
    headers = {"X-Session-ID": session_id}

    cart_res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = cart_res.json()["data"]["id"]

    # Request an excessive quantity beyond physical stock for prod_swiftstride
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_swiftstride", "quantity": 9999},
        headers=headers,
    )

    # Request quote: Must return 200 with valid=false, item in_stock=false, and descriptive warnings
    q = client.post(f"/api/carts/{cart_id}/quote", headers=headers)
    assert q.status_code == 200
    data = q.json()["data"]
    assert data["valid"] is False
    assert len(data["items"]) == 1
    assert data["items"][0]["in_stock"] is False
    assert len(data["warnings"]) > 0
    assert "available" in data["warnings"][0].lower() or "stock" in data["warnings"][0].lower()


def test_quote_delivery_rules():
    session_id = f"test_sess_deliv_{uuid.uuid4().hex[:8]}"
    headers = {"X-Session-ID": session_id}

    cart_res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = cart_res.json()["data"]["id"]

    # Add small item below free delivery threshold of ₹2,000 (prod_fleet_socks is ₹699 = 69900 paise < 200000 paise)
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_fleet_socks", "quantity": 1},
        headers=headers,
    )

    # Quote below threshold charges standard delivery (15000 paise = ₹150)
    q_below = client.post(f"/api/carts/{cart_id}/quote", headers=headers)
    assert q_below.status_code == 200
    data_below = q_below.json()["data"]
    assert data_below["subtotal_paise"] == 69900
    assert data_below["delivery_paise"] == 15000
    assert data_below["total_paise"] == 69900 + 15000

    # Increase quantity so subtotal exceeds ₹2,000 (69900 * 3 = 209700 >= 200000)
    client.post(
        f"/api/carts/{cart_id}/items",
        json={"product_id": "prod_fleet_socks", "quantity": 2},
        headers=headers,
    )

    q_above = client.post(f"/api/carts/{cart_id}/quote", headers=headers)
    assert q_above.status_code == 200
    data_above = q_above.json()["data"]
    assert data_above["subtotal_paise"] == 209700
    assert data_above["delivery_paise"] == 0
    assert data_above["total_paise"] == 209700


def test_discovery_endpoints():
    # 1. Product availability
    avail_res = client.get("/api/products/prod_runpro_x2/availability")
    assert avail_res.status_code == 200
    avail = avail_res.json()["data"]
    assert avail["sku"] == "RUN-X2-BLK-42"
    assert avail["price_paise"] > 0
    assert avail["in_stock"] is True

    # 2. Related products via cross-sell policy
    rel_res = client.get("/api/products/prod_runpro_x2/related?limit=3")
    assert rel_res.status_code == 200
    related = rel_res.json()["data"]
    assert isinstance(related, list)
    assert len(related) > 0

    # 3. Offers
    offers_res = client.get("/api/offers")
    assert offers_res.status_code == 200
    offers_data = offers_res.json()["data"]
    assert len(offers_data["offers"]) >= 1
    assert "max_discount_percent" in offers_data

    # 4. Delivery estimate
    deliv_res = client.get("/api/delivery/estimate?subtotal_paise=50000")
    assert deliv_res.status_code == 200
    deliv = deliv_res.json()["data"]
    assert deliv["is_free"] is False
    assert deliv["delivery_paise"] == 15000

    deliv_free = client.get("/api/delivery/estimate?subtotal_paise=250000")
    assert deliv_free.status_code == 200
    assert deliv_free.json()["data"]["is_free"] is True
    assert deliv_free.json()["data"]["delivery_paise"] == 0
