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
from app.models.audit import AuditEvent
from app.services.audit import log_audit_event

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_inventory():
    """Ensure sufficient inventory for test runs."""
    with SessionLocal() as db:
        prod_shoes = db.query(Product).filter(Product.id == "prod_runpro_x2").first()
        if prod_shoes:
            prod_shoes.inventory_quantity = 50
        prod_socks = db.query(Product).filter(Product.id == "prod_fleet_socks").first()
        if prod_socks:
            prod_socks.inventory_quantity = 50
        db.commit()
    yield


def get_admin_token() -> str:
    """Logs in as seeded demo admin and returns bearer token."""
    res = client.post("/api/admin/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["data"]["token"]


def get_demo_merchant_id() -> str:
    """Retrieves the merchant ID belonging to the demo admin."""
    from app.models.admin_user import AdminUser
    with SessionLocal() as db:
        admin = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
        assert admin is not None
        return admin.merchant_id


def create_and_confirm_order(session_id: str, items: list) -> dict:
    """Helper to create a cart, add items, and complete verified payment."""
    # 1. Cart
    res = client.post("/api/carts", json={"session_id": session_id})
    cart_id = res.json()["data"]["id"]

    # 2. Add Items
    for item in items:
        client.post(
            f"/api/carts/{cart_id}/items",
            json={"product_id": item["product_id"], "quantity": item.get("quantity", 1)},
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
            "customer_name": "Analytics Tester",
            "customer_email": "analytics@example.com",
            "customer_phone": "+919876543210",
            "shipping_address": {
                "line1": "100 Tech Park",
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
            "currency": "INR",
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
        assert verify_res.status_code == 200, f"Payment verify failed: {verify_res.text}"

    return {
        "order_id": order_id,
        "amount_paise": quote["total_paise"],
        "cart_id": cart_id,
    }


def test_analytics_unauthorized():
    """Verify endpoint rejects unauthenticated requests."""
    res = client.get("/api/admin/analytics")
    assert res.status_code == 401


def test_analytics_baseline_structure():
    """Verify endpoint returns complete response schema without errors."""
    token = get_admin_token()
    res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]

    # Verify presence of all primary fields
    assert "gross_revenue_paise" in data
    assert "gross_revenue_inr" in data
    assert "confirmed_orders_count" in data
    assert "active_skus_count" in data
    assert "aov_paise" in data
    assert "aov_inr" in data
    assert "total_carts_created" in data
    assert "carts_with_items_count" in data
    assert "converted_carts_count" in data
    assert "cart_to_order_conversion_rate" in data
    assert "in_app_agent_turns_count" in data
    assert "external_ai_tool_calls_count" in data
    assert "cross_sell_acceptance_rate" in data
    assert "channel_breakdown" in data
    assert "daily_trends" in data

    # Verify channel keys
    channels = {c["channel"] for c in data["channel_breakdown"]}
    assert "direct_storefront" in channels
    assert "in_app_agent" in channels
    assert "external_ai" in channels


def test_analytics_storefront_order_updates_metrics():
    """Verify placing a direct storefront order updates revenue, order counts, and conversion rate."""
    token = get_admin_token()
    before_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    before = before_res.json()["data"]

    # Create new storefront session and confirmed order
    session_id = f"storefront_test_{uuid.uuid4().hex[:8]}"
    order_info = create_and_confirm_order(
        session_id=session_id,
        items=[{"product_id": "prod_runpro_x2", "quantity": 1}],
    )

    after_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    after = after_res.json()["data"]

    assert after["confirmed_orders_count"] == before["confirmed_orders_count"] + 1
    assert after["gross_revenue_paise"] == before["gross_revenue_paise"] + order_info["amount_paise"]
    assert after["gross_revenue_inr"] == round(after["gross_revenue_paise"] / 100.0, 2)
    assert after["converted_carts_count"] >= before["converted_carts_count"] + 1

    # Check direct storefront channel attribution
    storefront_ch = next(c for c in after["channel_breakdown"] if c["channel"] == "direct_storefront")
    assert storefront_ch["orders_count"] >= 1
    assert storefront_ch["revenue_paise"] >= order_info["amount_paise"]


def test_analytics_in_app_agent_attribution():
    """Verify orders originating from sessions with agent activity are attributed to In-App AI Agent."""
    token = get_admin_token()
    session_id = f"agent_test_{uuid.uuid4().hex[:8]}"

    # Log in-app agent chat audit event
    merchant_id = get_demo_merchant_id()
    with SessionLocal() as db:
        log_audit_event(
            db=db,
            actor_type="agent",
            action="agent_chat_turn",
            entity_type="cart",
            session_id=session_id,
            merchant_id=merchant_id,
            metadata={"user_prompt": "Find shoes"},
        )

    before_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    before_agent_ch = next(c for c in before_res.json()["data"]["channel_breakdown"] if c["channel"] == "in_app_agent")

    # Now place order in this agent session
    order_info = create_and_confirm_order(
        session_id=session_id,
        items=[{"product_id": "prod_runpro_x2", "quantity": 1}],
    )

    after_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    after = after_res.json()["data"]
    after_agent_ch = next(c for c in after["channel_breakdown"] if c["channel"] == "in_app_agent")

    assert after["in_app_agent_turns_count"] >= 1
    assert after_agent_ch["orders_count"] == before_agent_ch["orders_count"] + 1
    assert after_agent_ch["revenue_paise"] == before_agent_ch["revenue_paise"] + order_info["amount_paise"]


def test_analytics_external_ai_buyer_attribution():
    """Verify orders with external AI buyer sessions are attributed to External AI Buyer (MCP)."""
    token = get_admin_token()
    session_id = f"ext_buyer_{uuid.uuid4().hex[:8]}"

    # Log MCP tool execution
    merchant_id = get_demo_merchant_id()
    with SessionLocal() as db:
        log_audit_event(
            db=db,
            actor_type="external_ai_buyer",
            action="mcp_tool_called",
            entity_type="mcp_tool",
            session_id=session_id,
            merchant_id=merchant_id,
            metadata={"tool": "search_products"},
        )

    before_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    before_ext_ch = next(c for c in before_res.json()["data"]["channel_breakdown"] if c["channel"] == "external_ai")

    # Place order in external buyer session
    order_info = create_and_confirm_order(
        session_id=session_id,
        items=[{"product_id": "prod_runpro_x2", "quantity": 1}],
    )

    after_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    after = after_res.json()["data"]
    after_ext_ch = next(c for c in after["channel_breakdown"] if c["channel"] == "external_ai")

    assert after["external_ai_tool_calls_count"] >= 1
    assert after_ext_ch["orders_count"] == before_ext_ch["orders_count"] + 1
    assert after_ext_ch["revenue_paise"] == before_ext_ch["revenue_paise"] + order_info["amount_paise"]


def test_analytics_cross_sell_pairing_detection():
    """Verify an order containing both footwear and socks increases cross-sell acceptance."""
    token = get_admin_token()
    before_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    before = before_res.json()["data"]

    # Place order with shoes (footwear) AND socks (socks)
    session_id = f"cross_sell_test_{uuid.uuid4().hex[:8]}"
    create_and_confirm_order(
        session_id=session_id,
        items=[
            {"product_id": "prod_runpro_x2", "quantity": 1},    # Running Shoes
            {"product_id": "prod_fleet_socks", "quantity": 1},  # Running Socks
        ],
    )

    after_res = client.get(
        "/api/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    after = after_res.json()["data"]

    assert after["cross_sell_eligible_orders_count"] >= before["cross_sell_eligible_orders_count"] + 1
    assert after["cross_sell_accepted_orders_count"] >= before["cross_sell_accepted_orders_count"] + 1
    assert after["cross_sell_acceptance_rate"] > 0.0

    # Verify cross-sell rule summary lists the match
    shoes_socks_rule = next(
        (r for r in after["cross_sell_rules_summary"]
         if "shoe" in r["trigger_category"].lower() and "sock" in r["recommend_category"].lower()),
        None,
    )
    assert shoes_socks_rule is not None
    assert shoes_socks_rule["matches_count"] >= 1


def test_analytics_all_time_vs_30_days_window():
    """Verify days=30 excludes older orders while days=0 or omitted includes them."""
    from datetime import datetime, timedelta, timezone
    from app.models.order import MerchantOrder

    token = get_admin_token()

    # 1. Measure baseline
    all_time_res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    all_time_before = all_time_res.json()["data"]

    thirty_day_res = client.get("/api/admin/analytics?days=30", headers={"Authorization": f"Bearer {token}"})
    thirty_day_before = thirty_day_res.json()["data"]

    # 2. Insert an old order (45 days ago) directly into SQLite
    old_order_id = f"ord_old_{uuid.uuid4().hex[:8]}"
    old_amount = 77700  # ₹777.00
    old_time = datetime.now(timezone.utc) - timedelta(days=45)

    merchant_id = get_demo_merchant_id()
    with SessionLocal() as db:
        old_order = MerchantOrder(
            id=old_order_id,
            merchant_id=merchant_id,
            customer_name="Historical Customer",
            customer_email="old@example.com",
            customer_phone="+919876543210",
            shipping_address_json="{}",
            items_snapshot_json="[]",
            amount_paise=old_amount,
            currency="INR",
            status="CONFIRMED",
            created_at=old_time,
            confirmed_at=old_time,
        )
        db.add(old_order)
        db.commit()

    # 3. Query days=30 -> Must NOT include the 45-day-old order
    res_30 = client.get("/api/admin/analytics?days=30", headers={"Authorization": f"Bearer {token}"})
    data_30 = res_30.json()["data"]
    assert data_30["confirmed_orders_count"] == thirty_day_before["confirmed_orders_count"]
    assert data_30["gross_revenue_paise"] == thirty_day_before["gross_revenue_paise"]

    # 4. Query omitted days -> Must include the 45-day-old order (true all-time)
    res_omitted = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    data_omitted = res_omitted.json()["data"]
    assert data_omitted["confirmed_orders_count"] == all_time_before["confirmed_orders_count"] + 1
    assert data_omitted["gross_revenue_paise"] == all_time_before["gross_revenue_paise"] + old_amount

    # 5. Query days=0 -> Must also include the 45-day-old order (true all-time)
    res_zero = client.get("/api/admin/analytics?days=0", headers={"Authorization": f"Bearer {token}"})
    data_zero = res_zero.json()["data"]
    assert data_zero["confirmed_orders_count"] == all_time_before["confirmed_orders_count"] + 1
    assert data_zero["gross_revenue_paise"] == all_time_before["gross_revenue_paise"] + old_amount


def test_analytics_daily_ai_sessions_aggregated_from_audit_events():
    """Verify daily_trends.ai_sessions_count reflects actual distinct sessions from audit_events."""
    from datetime import datetime, timezone

    token = get_admin_token()
    today_str = datetime.now(timezone.utc).date().isoformat()
    merchant_id = get_demo_merchant_id()

    # Create two unique session IDs for today
    unique_agent_sess = f"test_daily_agent_{uuid.uuid4().hex[:8]}"
    unique_mcp_sess = f"test_daily_mcp_{uuid.uuid4().hex[:8]}"

    with SessionLocal() as db:
        # 1. In-app agent turn for unique_agent_sess
        log_audit_event(
            db=db,
            actor_type="agent",
            action="agent_chat_turn",
            entity_type="cart",
            session_id=unique_agent_sess,
            merchant_id=merchant_id,
            metadata={"user_prompt": "Hello assistant"},
        )
        # 2. Second turn in same session (should not increase distinct count)
        log_audit_event(
            db=db,
            actor_type="agent",
            action="agent_chat_turn",
            entity_type="cart",
            session_id=unique_agent_sess,
            merchant_id=merchant_id,
            metadata={"user_prompt": "Recommend kit"},
        )
        # 3. External AI buyer tool call for unique_mcp_sess
        log_audit_event(
            db=db,
            actor_type="external_ai_buyer",
            action="mcp_tool_called",
            entity_type="mcp_tool",
            session_id=unique_mcp_sess,
            merchant_id=merchant_id,
            metadata={"tool": "search_products"},
        )

    res = client.get("/api/admin/analytics?days=7", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    daily_trends = res.json()["data"]["daily_trends"]

    today_trend = next((d for d in daily_trends if d["date"] == today_str), None)
    assert today_trend is not None, f"Today ({today_str}) not found in daily trends"
    # Must have at least 2 distinct AI sessions recorded today
    assert today_trend["ai_sessions_count"] >= 2

