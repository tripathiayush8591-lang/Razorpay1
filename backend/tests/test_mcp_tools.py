import asyncio
import json
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.main import app
from app.mcp.server import mcp_server
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.audit import AuditEvent

client = TestClient(app)


def test_mcp_tools_registration():
    """Verify that all 13 tools are registered on the MCPServer instance."""
    tools = asyncio.run(mcp_server.list_tools())
    tool_names = {t.name for t in tools}
    expected = {
        "search_products",
        "get_product",
        "check_inventory",
        "get_delivery_estimate",
        "get_offers",
        "create_cart",
        "add_to_cart",
        "remove_from_cart",
        "get_cart",
        "get_final_quote",
        "create_checkout",
        "get_order",
        "get_order_status",
    }
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"
    assert len(tools) == 13


def test_mcp_api_tools_endpoint():
    """Verify GET /api/mcp/tools returns all 13 tools with schemas."""
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    tools = data["data"]
    assert len(tools) == 13
    tool_names = [t["name"] for t in tools]
    assert "search_products" in tool_names
    assert "create_checkout" in tool_names
    assert "get_final_quote" in tool_names


def test_mcp_search_and_product_lookup():
    """Test search_products and get_product MCP tools."""
    # 1. Search without filters
    res = asyncio.run(mcp_server.call_tool("search_products", {}))
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["count"] > 0
    first_prod = data["products"][0]
    first_id = first_prod["id"]

    # 2. Search with category filter
    res_cat = asyncio.run(mcp_server.call_tool("search_products", {"category": first_prod["category"]}))
    assert not res_cat.is_error
    cat_data = json.loads(res_cat.content[0].text)
    assert all(p["category"] == first_prod["category"] for p in cat_data["products"])

    # 3. Get single product
    res_single = asyncio.run(mcp_server.call_tool("get_product", {"product_id": first_id}))
    assert not res_single.is_error
    prod_data = json.loads(res_single.content[0].text)
    assert prod_data["id"] == first_id

    # 4. Inactive/nonexistent product error handling
    res_bad = asyncio.run(mcp_server.call_tool("get_product", {"product_id": "prod_nonexistent"}))
    assert not res_bad.is_error
    bad_data = json.loads(res_bad.content[0].text)
    assert bad_data.get("is_error") is True
    assert bad_data["error"]["status_code"] == 404


def test_mcp_inventory_and_delivery():
    """Test check_inventory and get_delivery_estimate tools."""
    with SessionLocal() as db:
        prod = db.scalar(select(Product).where(Product.active == True, Product.inventory_quantity > 0))
        assert prod is not None
        prod_id = prod.id

    # Sufficient stock
    res_stock = asyncio.run(mcp_server.call_tool("check_inventory", {"product_id": prod_id, "quantity": 1}))
    assert not res_stock.is_error
    stock_data = json.loads(res_stock.content[0].text)
    assert stock_data["has_sufficient_stock"] is True

    # Excess stock request
    res_excess = asyncio.run(mcp_server.call_tool("check_inventory", {"product_id": prod_id, "quantity": 9999}))
    assert not res_excess.is_error
    excess_data = json.loads(res_excess.content[0].text)
    assert excess_data["has_sufficient_stock"] is False

    # Delivery estimate: above threshold (free)
    res_del_free = asyncio.run(mcp_server.call_tool("get_delivery_estimate", {"postal_code": "560001", "cart_subtotal_paise": 250000}))
    assert not res_del_free.is_error
    del_data_free = json.loads(res_del_free.content[0].text)
    assert del_data_free["is_free"] is True
    assert del_data_free["delivery_paise"] == 0

    # Delivery estimate: below threshold (paid)
    res_del_paid = asyncio.run(mcp_server.call_tool("get_delivery_estimate", {"postal_code": "560001", "cart_subtotal_paise": 100000}))
    assert not res_del_paid.is_error
    del_data_paid = json.loads(res_del_paid.content[0].text)
    assert del_data_paid["is_free"] is False
    assert del_data_paid["delivery_paise"] == 15000


def test_mcp_cart_operations_and_isolation():
    """Test create_cart, add_to_cart, get_cart, remove_from_cart and session isolation."""
    session_a = "ext_buyer_session_alpha"
    session_b = "ext_buyer_session_beta"

    # Create cart for Session A
    res_cart = asyncio.run(mcp_server.call_tool("create_cart", {"session_id": session_a}))
    assert not res_cart.is_error
    cart_a = json.loads(res_cart.content[0].text)
    cart_id = cart_a["id"]
    assert cart_a["session_id"] == session_a

    with SessionLocal() as db:
        prod = db.scalar(select(Product).where(Product.active == True, Product.inventory_quantity > 5))
        assert prod is not None
        prod_id = prod.id

    # Add item to Session A cart
    res_add = asyncio.run(mcp_server.call_tool("add_to_cart", {
        "session_id": session_a,
        "cart_id": cart_id,
        "product_id": prod_id,
        "quantity": 2,
    }))
    assert not res_add.is_error
    add_data = json.loads(res_add.content[0].text)
    assert len(add_data["items"]) >= 1
    item_id = add_data["items"][0]["id"]

    # Security Isolation: Session B attempts to read Session A cart
    res_sneak = asyncio.run(mcp_server.call_tool("get_cart", {
        "session_id": session_b,
        "cart_id": cart_id,
    }))
    assert not res_sneak.is_error
    sneak_data = json.loads(res_sneak.content[0].text)
    assert sneak_data.get("is_error") is True
    assert sneak_data["error"]["status_code"] == 403

    # Security Isolation: Session B attempts to mutate Session A cart
    res_tamper = asyncio.run(mcp_server.call_tool("remove_from_cart", {
        "session_id": session_b,
        "cart_id": cart_id,
        "item_id": item_id,
    }))
    tamper_data = json.loads(res_tamper.content[0].text)
    assert tamper_data.get("is_error") is True
    assert tamper_data["error"]["status_code"] == 403

    # Session A successfully removes item
    res_remove = asyncio.run(mcp_server.call_tool("remove_from_cart", {
        "session_id": session_a,
        "cart_id": cart_id,
        "item_id": item_id,
    }))
    assert not res_remove.is_error
    remove_data = json.loads(res_remove.content[0].text)
    assert len(remove_data["items"]) == 0


def test_mcp_authoritative_quote_revalidation():
    """Verify that get_final_quote recalculates live prices directly from SQLite."""
    session_id = "ext_buyer_quote_test"
    res_cart = asyncio.run(mcp_server.call_tool("create_cart", {"session_id": session_id}))
    cart = json.loads(res_cart.content[0].text)
    cart_id = cart["id"]

    with SessionLocal() as db:
        prod = db.scalar(select(Product).where(Product.active == True, Product.inventory_quantity > 5))
        assert prod is not None
        prod_id = prod.id
        original_price = prod.price_paise

    # Add item
    asyncio.run(mcp_server.call_tool("add_to_cart", {
        "session_id": session_id,
        "cart_id": cart_id,
        "product_id": prod_id,
        "quantity": 1,
    }))

    # Quote 1
    res_q1 = asyncio.run(mcp_server.call_tool("get_final_quote", {
        "session_id": session_id,
        "cart_id": cart_id,
    }))
    q1 = json.loads(res_q1.content[0].text)
    assert q1["items"][0]["unit_price_paise"] == original_price

    # Admin updates price directly in SQLite
    new_price = original_price + 50000  # increase by ₹500
    with SessionLocal() as db:
        p = db.scalar(select(Product).where(Product.id == prod_id))
        p.price_paise = new_price
        db.commit()

    # Quote 2 must immediately reflect new price
    res_q2 = asyncio.run(mcp_server.call_tool("get_final_quote", {
        "session_id": session_id,
        "cart_id": cart_id,
    }))
    q2 = json.loads(res_q2.content[0].text)
    assert q2["items"][0]["unit_price_paise"] == new_price
    assert q2["total_paise"] >= new_price

    # Restore price
    with SessionLocal() as db:
        p = db.scalar(select(Product).where(Product.id == prod_id))
        p.price_paise = original_price
        db.commit()


def test_mcp_checkout_approval_and_order_flow():
    """Verify the explicit approval check, checkout creation, and order tracking flow."""
    session_id = "ext_buyer_checkout_test"
    res_cart = asyncio.run(mcp_server.call_tool("create_cart", {"session_id": session_id}))
    cart_id = json.loads(res_cart.content[0].text)["id"]

    with SessionLocal() as db:
        prod = db.scalar(select(Product).where(Product.active == True, Product.inventory_quantity > 5))
        assert prod is not None
        prod_id = prod.id

    asyncio.run(mcp_server.call_tool("add_to_cart", {
        "session_id": session_id,
        "cart_id": cart_id,
        "product_id": prod_id,
        "quantity": 1,
    }))

    # Get authoritative quote
    res_quote = asyncio.run(mcp_server.call_tool("get_final_quote", {
        "session_id": session_id,
        "cart_id": cart_id,
    }))
    quote = json.loads(res_quote.content[0].text)
    authoritative_total = quote["total_paise"]

    shipping_payload = {
        "line1": "123 MCP Lane",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560001",
        "country": "India",
    }

    # 1. Attempt checkout with tampered approved_total_paise
    res_tampered = asyncio.run(mcp_server.call_tool("create_checkout", {
        "session_id": session_id,
        "cart_id": cart_id,
        "approved_total_paise": authoritative_total - 10000,  # underpaying by ₹100
        "customer_name": "Autonomous Agent",
        "customer_email": "agent@external.ai",
        "customer_phone": "+919876543210",
        "shipping_address": shipping_payload,
    }))
    tampered_data = json.loads(res_tampered.content[0].text)
    assert tampered_data.get("is_error") is True
    assert tampered_data["error"]["status_code"] == 409  # Conflict!

    # 2. Valid checkout with exact approved_total_paise
    res_checkout = asyncio.run(mcp_server.call_tool("create_checkout", {
        "session_id": session_id,
        "cart_id": cart_id,
        "approved_total_paise": authoritative_total,
        "customer_name": "Autonomous Agent",
        "customer_email": "agent@external.ai",
        "customer_phone": "+919876543210",
        "shipping_address": shipping_payload,
    }))
    assert not res_checkout.is_error
    checkout_data = json.loads(res_checkout.content[0].text)
    order_id = checkout_data["merchant_order_id"]
    assert checkout_data["payment_status"] == "PENDING_PAYMENT"
    assert "razorpay_order_id" in checkout_data
    assert checkout_data["razorpay_order_id"].startswith("order_")

    # 3. Poll order status via MCP
    res_status = asyncio.run(mcp_server.call_tool("get_order_status", {
        "session_id": session_id,
        "order_id": order_id,
    }))
    assert not res_status.is_error
    status_data = json.loads(res_status.content[0].text)
    assert status_data["order_id"] == order_id
    assert status_data["payment_status"] == "PENDING_PAYMENT"

    # 4. Security Isolation: Session B attempts to inspect Session A order
    res_order_leak = asyncio.run(mcp_server.call_tool("get_order", {
        "session_id": "other_session_stranger",
        "order_id": order_id,
    }))
    leak_data = json.loads(res_order_leak.content[0].text)
    assert leak_data.get("is_error") is True
    assert leak_data["error"]["status_code"] == 403


def test_mcp_execute_api_route():
    """Test the POST /api/mcp/execute test/demo route."""
    req_body = {
        "tool_name": "search_products",
        "arguments": {"category": "Road Running"},
    }
    response = client.post("/api/mcp/execute", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["tool_name"] == "search_products"
    assert data["data"]["is_error"] is False
    assert "products" in data["data"]["result"]


def test_mcp_audit_logging():
    """Verify that MCP tool calls create authoritative audit_events records."""
    with SessionLocal() as db:
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.actor_type == "external_ai_buyer",
                AuditEvent.action == "mcp_tool_called",
            )
        )
        events = db.scalars(stmt).all()
        assert len(events) > 0
        tools_logged = {e.entity_id for e in events}
        assert "create_cart" in tools_logged or "search_products" in tools_logged
