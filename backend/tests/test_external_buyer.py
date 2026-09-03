import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_external_buyer_turn_over_mcp():
    """Verify External Buyer executes an autonomous turn via MCP Streamable HTTP."""
    session_id = "test_ext_buyer_integration_sess"
    req_body = {
        "message": "Find beginner running shoes under ₹6,000 and prepare my quote for checkout",
        "session_id": session_id,
        "history": [],
    }

    with TestClient(app) as client:
        response = client.post("/api/external-buyer/chat", json=req_body)
    assert response.status_code == 200, f"Error: {response.text}"

    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # 1. Verify Provider and Message
    assert data["provider"] in ("gemini", "mcp_fallback")
    assert len(data["message"]) > 0

    # 2. Verify Real MCP Tool Calls Recorded
    assert len(data["mcp_calls"]) >= 3
    tool_names = [call["tool_name"] for call in data["mcp_calls"]]
    assert "search_products" in tool_names
    assert "create_cart" in tool_names
    assert "get_final_quote" in tool_names

    # 3. Explicit Approval Boundary: create_checkout MUST NEVER be called by the agent!
    assert "create_checkout" not in tool_names
    assert data["approval_required"] is True

    # 4. Authoritative Quote Returned
    assert data["quote"] is not None
    assert data["quote"]["valid"] is True
    assert data["quote"]["total_paise"] > 0
    assert len(data["quote"]["items"]) >= 1

    # 5. Concise Action Summaries
    assert len(data["tool_activity"]) >= 3
    for act in data["tool_activity"]:
        assert act["status"] in ("completed", "failed")
        assert len(act["activity"]) > 0

    # 6. Recommendations
    assert len(data["recommendations"]) >= 1


def test_external_buyer_session_isolation_and_approval_flow():
    """Verify session isolation and explicit human approval flow after external buyer turn."""
    session_a = "buyer_sess_alpha"
    session_b = "buyer_sess_beta"

    # Step 1: Session A runs buyer turn to get cart and quote
    with TestClient(app) as client:
        chat_res = client.post("/api/external-buyer/chat", json={
            "message": "Find beginner running shoes under ₹6,000 and assemble my cart with a final quote",
            "session_id": session_a,
            "history": [],
        })
        assert chat_res.status_code == 200
        chat_data = chat_res.json()["data"]
        cart_id = chat_data["cart_id"]
        quote = chat_data["quote"]
        authoritative_total = quote["total_paise"]

        # Step 2: Session B attempts to access Session A cart via MCP -> 403 Forbidden
        tamper_res = client.post("/api/mcp/execute", json={
            "tool_name": "get_cart",
            "arguments": {"session_id": session_b, "cart_id": cart_id},
        })
        assert tamper_res.status_code == 200
        assert tamper_res.json()["data"]["result"]["is_error"] is True
        assert tamper_res.json()["data"]["result"]["error"]["status_code"] == 403

        # Step 3: Explicit Human Approval with tampered amount -> 409 Conflict
        bad_approval = client.post("/api/mcp/execute", json={
            "tool_name": "create_checkout",
            "arguments": {
                "session_id": session_a,
                "cart_id": cart_id,
                "approved_total_paise": authoritative_total - 5000,
                "customer_name": "Aarav Sharma",
                "customer_email": "aarav@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "42 MG Road",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560001",
                    "country": "India",
                },
            },
        })
        assert bad_approval.status_code == 200
        assert bad_approval.json()["data"]["result"]["is_error"] is True
        assert bad_approval.json()["data"]["result"]["error"]["status_code"] == 409

        # Step 4: Valid Human Approval with exact authoritative total -> Order created in PENDING_PAYMENT
        valid_approval = client.post("/api/mcp/execute", json={
            "tool_name": "create_checkout",
            "arguments": {
                "session_id": session_a,
                "cart_id": cart_id,
                "approved_total_paise": authoritative_total,
                "customer_name": "Aarav Sharma",
                "customer_email": "aarav@example.com",
                "customer_phone": "+919876543210",
                "shipping_address": {
                    "line1": "42 MG Road",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560001",
                    "country": "India",
                },
            },
        })
        assert valid_approval.status_code == 200
        valid_data = valid_approval.json()["data"]["result"]
        assert valid_data["payment_status"] == "PENDING_PAYMENT"
        assert valid_data["razorpay_order_id"].startswith("order_")


def test_catalog_search_relevance_running_shoes():
    """Verify catalog search relevance prioritizes name/category matches over description-only matches."""
    from app.db.session import SessionLocal
    from app.services.catalog import list_products

    with SessionLocal() as db:
        # Generic query: 'running'
        running_prods = list_products(db, q="running", max_price_paise=600000)
        assert len(running_prods) >= 3

        # First item must have 'Running' in name or category, NOT be a massage roller
        top_item = running_prods[0]
        assert top_item.id != "prod_massage_roller", "Massage roller must not rank first for 'running'"
        assert "running" in top_item.name.lower() or "running" in top_item.category.lower()

        # Specific query: 'running shoes'
        shoe_prods = list_products(db, q="running shoes")
        shoe_ids = [p.id for p in shoe_prods]
        assert "prod_massage_roller" not in shoe_ids, "Massage ball must not match 'running shoes'"
        assert "prod_swiftstride" in shoe_ids or "prod_runpro_x2" in shoe_ids

        # Specific query: 'running socks'
        sock_prods = list_products(db, q="running socks")
        sock_ids = [p.id for p in sock_prods]
        assert "prod_fleet_socks" in sock_ids


def test_external_buyer_deterministic_fallback_running_kit_semantics():
    """Verify fallback parses user constraints (budget, shoes, socks) instead of hardcoding a single item."""
    from unittest.mock import patch

    import uuid
    session_id = f"test_fallback_{uuid.uuid4().hex[:8]}"

    with patch("app.services.external_buyer.is_gemini_available", return_value=False):
        with TestClient(app) as client:
            res = client.post("/api/external-buyer/chat", json={
                "message": "Build me a beginner running kit under ₹8,000 with running shoes and socks.",
                "session_id": session_id,
                "history": [],
            })
            assert res.status_code == 200
            data = res.json()["data"]

            assert data["provider"] == "mcp_fallback"
            assert data["approval_required"] is True
            assert data["quote"] is not None

            # Verify quote items
            quote = data["quote"]
            item_names = [it["name"] for it in quote["items"]]

            # Must contain shoes and socks
            has_shoes = any("trainer" in n.lower() or "runner" in n.lower() or "shoe" in n.lower() for n in item_names)
            has_socks = any("sock" in n.lower() for n in item_names)
            assert has_shoes, f"Kit must contain running shoes, got: {item_names}"
            assert has_socks, f"Kit must contain socks, got: {item_names}"

            # Must NOT contain massage ball
            assert not any("massage" in n.lower() for n in item_names), f"Kit must not contain massage ball, got: {item_names}"

            # Total must be within budget (<= ₹8,000 = 800,000 paise)
            assert quote["total_paise"] <= 800000


def test_external_buyer_gemini_429_model_retry():
    """Verify external buyer retries with gemini-2.5-flash-lite when primary model hits 429."""
    from unittest.mock import patch, AsyncMock
    from app.services.external_buyer import ExternalBuyerService
    from app.schemas.external_buyer import ExternalBuyerChatRequest

    models_called = []

    async def fake_run_gemini(mcp_session, message, history, model_name=None):
        models_called.append(model_name)
        if model_name == "gemini-2.5-flash":
            raise Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for gemini-2.5-flash")
        return "I found your shoes and socks via gemini-2.5-flash-lite"

    service = ExternalBuyerService(session_id="test_retry_sess")
    req = ExternalBuyerChatRequest(
        message="Find running shoes under ₹6,000",
        session_id="test_retry_sess",
        history=[],
    )

    with patch("app.services.external_buyer.is_gemini_available", return_value=True), \
         patch.object(ExternalBuyerService, "_run_gemini_buyer", side_effect=fake_run_gemini):
        with TestClient(app):
            import anyio
            res = anyio.run(service.execute_turn, req, app)
            assert res.provider == "gemini"
            assert "gemini-2.5-flash" in models_called
            assert "gemini-2.5-flash-lite" in models_called

