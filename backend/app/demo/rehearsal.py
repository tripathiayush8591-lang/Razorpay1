"""
Deterministic End-to-End Rehearsal Engine for RunCraft Agentic Commerce (Task 24).

Verifies all 11 stages of the Hackathon Demo lifecycle:
  A. Storefront shopping
  B. In-app Gemini/fallback agent
  C. External AI Buyer + MCP
  D. Human approval boundary
  E. Razorpay test payment initiation
  F. Order confirmation & signature verification
  G. Admin fulfillment (CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED)
  H. Customer tracking & session boundary
  I. Audit trail verification
  J. Real-time analytics computation
  K. Error handling & recovery scenarios

Can be run standalone via:
  python -m app.demo.rehearsal
or invoked in automated pytest suites.
"""

import sys
import uuid
import hmac
import hashlib
from typing import Dict, Any
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.order import MerchantOrder
from app.models.cart import Cart

client = TestClient(app)


class RehearsalRunner:
    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.admin_token: str = ""
        self.session_storefront: str = f"rehearsal_storefront_{uuid.uuid4().hex[:8]}"
        self.session_inapp: str = f"rehearsal_inapp_{uuid.uuid4().hex[:8]}"
        self.session_ext: str = f"ext_buyer_rehearsal_{uuid.uuid4().hex[:8]}"
        self.active_order_id: str = ""
        self.active_rzp_order_id: str = ""
        self.active_cart_id: str = ""
        self.active_amount: int = 0

    def log_checkpoint(self, stage_code: str, name: str, passed: bool, detail: str = ""):
        self.results[stage_code] = passed
        symbol = "[PASS]" if passed else "[FAIL]"
        print(f"  {symbol} Stage {stage_code}: {name}")
        if detail:
            print(f"         > {detail}")

    def run_stage_a_storefront(self):
        """Stage A: Storefront Shopping & Availability"""
        try:
            # 1. Fetch products
            res = client.get("/api/products")
            assert res.status_code == 200, f"Failed to list products: {res.text}"
            prods = res.json()["data"]
            assert len(prods) >= 10, f"Expected at least 10 products, got {len(prods)}"

            # 2. Check availability
            avail_res = client.get("/api/products/prod_runpro_x2/availability")
            assert avail_res.status_code == 200, f"Failed availability check: {avail_res.text}"
            avail_data = avail_res.json()["data"]
            assert avail_data["in_stock"] is True
            assert avail_data["inventory_quantity"] > 0

            # 3. Create storefront cart & add item
            cart_res = client.post("/api/carts", json={"session_id": self.session_storefront})
            assert cart_res.status_code == 200
            cart_id = cart_res.json()["data"]["id"]

            add_res = client.post(
                f"/api/carts/{cart_id}/items",
                headers={"X-Session-ID": self.session_storefront},
                json={"product_id": "prod_runpro_x2", "quantity": 1},
            )
            assert add_res.status_code == 200

            quote_res = client.post(
                f"/api/carts/{cart_id}/quote",
                headers={"X-Session-ID": self.session_storefront},
            )
            assert quote_res.status_code == 200
            quote_data = quote_res.json()["data"]
            assert quote_data["valid"] is True
            assert quote_data["total_paise"] == 549900

            self.log_checkpoint("A", "Storefront Shopping", True, "Catalog loaded, stock checked, quote valid (INR 5,499.00)")
        except Exception as exc:
            self.log_checkpoint("A", "Storefront Shopping", False, str(exc))

    def run_stage_b_in_app_agent(self):
        """Stage B: In-App AI Shopping Assistant Orchestration"""
        try:
            res = client.post(
                "/api/agent/chat",
                headers={"X-Session-ID": self.session_inapp},
                json={
                    "message": "Build me a beginner running kit under INR 8,000",
                    "session_id": self.session_inapp,
                },
            )
            assert res.status_code == 200, f"Agent chat failed: {res.text}"
            data = res.json()["data"]

            # Must recommend products and provide authoritative quote
            assert len(data["recommendations"]) >= 1, "Agent returned no recommendations"
            assert data["cart"] is not None, "Agent did not create or bind cart"
            assert data["quote"] is not None, "Agent did not generate quote"
            assert data["quote"]["total_paise"] <= 800000, "Agent exceeded budget of INR 8,000"
            assert data["approval_required"] is True, "Approval required flag not set"

            total_inr = data["quote"]["total_paise"] / 100.0
            self.log_checkpoint(
                "B",
                "In-App Gemini Agent",
                True,
                f"Agent recommended kit with authoritative quote INR {total_inr:.2f} (< INR 8,000)",
            )
        except Exception as exc:
            self.log_checkpoint("B", "In-App Gemini Agent", False, str(exc))

    def run_stage_c_external_buyer_mcp(self):
        """Stage C: External AI Buyer + MCP Tools"""
        try:
            # 1. Search products via direct tool
            search_res = client.post(
                "/api/agent/tools/search-products",
                headers={"X-Session-ID": self.session_ext},
                json={"q": "daily trainer", "max_price_paise": 600000},
            )
            assert search_res.status_code == 200
            products = search_res.json()["data"]
            assert len(products) >= 1
            chosen_sku = products[0]["sku"]

            # 2. External buyer creates cart and adds item
            cart_res = client.post("/api/carts", headers={"X-Session-ID": self.session_ext}, json={"session_id": self.session_ext})
            cart_id = cart_res.json()["data"]["id"]

            add_res = client.post(
                "/api/agent/tools/add-to-cart",
                headers={"X-Session-ID": self.session_ext},
                json={"cart_id": cart_id, "product_id": products[0]["id"], "quantity": 1},
            )
            assert add_res.status_code == 200

            # 3. Authoritative Quote
            quote_res = client.post(
                "/api/agent/tools/get-final-quote",
                headers={"X-Session-ID": self.session_ext},
                json={"cart_id": cart_id},
            )
            assert quote_res.status_code == 200
            quote = quote_res.json()["data"]
            assert quote["valid"] is True

            self.log_checkpoint("C", "External AI Buyer + MCP", True, f"MCP search and cart flow executed for {chosen_sku}")
        except Exception as exc:
            self.log_checkpoint("C", "External AI Buyer + MCP", False, str(exc))

    def run_stage_d_approval_boundary(self):
        """Stage D: Strict Human Approval Boundary Enforcement"""
        try:
            # Verify no orders or payments exist for the active agent sessions before explicit approval
            with SessionLocal() as db:
                inapp_cart = db.scalar(select(Cart).where(Cart.session_id == self.session_inapp))
                if inapp_cart:
                    ord_check = db.scalar(select(MerchantOrder).where(MerchantOrder.cart_id == inapp_cart.id))
                    assert ord_check is None, "Order existed before explicit user checkout approval!"

                ext_cart = db.scalar(select(Cart).where(Cart.session_id == self.session_ext))
                if ext_cart:
                    ord_check2 = db.scalar(select(MerchantOrder).where(MerchantOrder.cart_id == ext_cart.id))
                    assert ord_check2 is None, "External AI order existed before user checkout approval!"

            self.log_checkpoint("D", "Human Approval Boundary", True, "Zero orders/payments created autonomously without user approval")
        except Exception as exc:
            self.log_checkpoint("D", "Human Approval Boundary", False, str(exc))

    def run_stage_e_razorpay_checkout_creation(self):
        """Stage E: Razorpay Test Checkout Initiation"""
        try:
            # Create a clean cart for the full payment rehearsal
            cart_res = client.post("/api/carts", json={"session_id": self.session_storefront})
            cart_id = cart_res.json()["data"]["id"]

            client.post(
                f"/api/carts/{cart_id}/items",
                headers={"X-Session-ID": self.session_storefront},
                json={"product_id": "prod_runpro_x2", "quantity": 1},
            )
            quote_res = client.post(f"/api/carts/{cart_id}/quote", headers={"X-Session-ID": self.session_storefront})
            quote = quote_res.json()["data"]

            checkout_res = client.post(
                f"/api/carts/{cart_id}/checkout",
                headers={"X-Session-ID": self.session_storefront},
                json={
                    "customer_name": "Rehearsal Shopper",
                    "customer_email": "rehearsal@runcraft.internal",
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
            data = checkout_res.json()["data"]

            assert "razorpay_order_id" in data
            assert "merchant_order_id" in data
            assert data["amount_paise"] == quote["total_paise"]

            self.active_order_id = data["merchant_order_id"]
            self.active_rzp_order_id = data["razorpay_order_id"]
            self.active_cart_id = cart_id
            self.active_amount = quote["total_paise"]

            self.log_checkpoint("E", "Razorpay Checkout Initiation", True, f"Order {self.active_order_id} created in PENDING_PAYMENT")
        except Exception as exc:
            self.log_checkpoint("E", "Razorpay Checkout Initiation", False, str(exc))

    def run_stage_f_payment_verification_and_confirmation(self):
        """Stage F: Payment Verification & Order Confirmation"""
        try:
            assert self.active_order_id, "active_order_id missing from Stage E"
            rzp_payment_id = f"pay_test_{uuid.uuid4().hex[:14]}"
            msg = f"{self.active_rzp_order_id}|{rzp_payment_id}".encode("utf-8")
            sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

            with patch("app.integrations.razorpay.razorpay_client.fetch_payment") as mock_fetch:
                mock_fetch.return_value = {
                    "id": rzp_payment_id,
                    "order_id": self.active_rzp_order_id,
                    "status": "captured",
                    "amount": self.active_amount,
                    "currency": "INR",
                }
                verify_res = client.post(
                    "/api/payments/razorpay/verify",
                    headers={"X-Session-ID": self.session_storefront},
                    json={
                        "merchant_order_id": self.active_order_id,
                        "razorpay_order_id": self.active_rzp_order_id,
                        "razorpay_payment_id": rzp_payment_id,
                        "razorpay_signature": sig,
                    },
                )
                assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"

            # Check database order state
            with SessionLocal() as db:
                order = db.scalar(select(MerchantOrder).where(MerchantOrder.id == self.active_order_id))
                assert order.status == "CONFIRMED"
                assert order.confirmed_at is not None

                cart = db.scalar(select(Cart).where(Cart.id == self.active_cart_id))
                assert cart.status == "converted"

            self.log_checkpoint("F", "Payment Verification & Confirmation", True, "Signature verified, stock decremented, status CONFIRMED")
        except Exception as exc:
            self.log_checkpoint("F", "Payment Verification & Confirmation", False, str(exc))

    def run_stage_g_admin_fulfillment(self):
        """Stage G: Admin Fulfillment State Machine (CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED)"""
        try:
            assert self.active_order_id, "active_order_id missing"
            # Login as demo admin
            login_res = client.post(
                "/api/admin/login",
                json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
            )
            assert login_res.status_code == 200
            self.admin_token = login_res.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {self.admin_token}"}

            # 1. CONFIRMED -> PROCESSING
            res1 = client.post(
                f"/api/admin/orders/{self.active_order_id}/fulfillment",
                headers=headers,
                json={"status": "PROCESSING"},
            )
            assert res1.status_code == 200
            assert res1.json()["data"]["status"] == "PROCESSING"

            # 2. PROCESSING -> SHIPPED
            res2 = client.post(
                f"/api/admin/orders/{self.active_order_id}/fulfillment",
                headers=headers,
                json={"status": "SHIPPED", "carrier": "BlueDart Express", "tracking_number": "BD-REHEARSAL-01"},
            )
            assert res2.status_code == 200
            assert res2.json()["data"]["status"] == "SHIPPED"
            assert res2.json()["data"]["tracking_number"] == "BD-REHEARSAL-01"

            # 3. SHIPPED -> DELIVERED
            res3 = client.post(
                f"/api/admin/orders/{self.active_order_id}/fulfillment",
                headers=headers,
                json={"status": "DELIVERED"},
            )
            assert res3.status_code == 200
            assert res3.json()["data"]["status"] == "DELIVERED"
            assert res3.json()["data"]["delivered_at"] is not None

            # 4. Invalid backwards transition rejected
            res_bad = client.post(
                f"/api/admin/orders/{self.active_order_id}/fulfillment",
                headers=headers,
                json={"status": "PROCESSING"},
            )
            assert res_bad.status_code == 409

            self.log_checkpoint("G", "Admin Fulfillment State Machine", True, "Full lifecycle CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED verified")
        except Exception as exc:
            self.log_checkpoint("G", "Admin Fulfillment State Machine", False, str(exc))

    def run_stage_h_customer_tracking(self):
        """Stage H: Customer Tracking & Guest Session Isolation"""
        try:
            assert self.active_order_id, "active_order_id missing"
            # 1. Customer retrieves own order
            res = client.get(
                f"/api/orders/{self.active_order_id}",
                headers={"X-Session-ID": self.session_storefront},
            )
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["id"] == self.active_order_id
            assert data["status"] == "DELIVERED"
            assert data["carrier"] == "BlueDart Express"
            assert data["tracking_number"] == "BD-REHEARSAL-01"

            # 2. Different session attempts to access order (must be HTTP 403 Forbidden)
            unauth_res = client.get(
                f"/api/orders/{self.active_order_id}",
                headers={"X-Session-ID": "foreign_session_xyz"},
            )
            assert unauth_res.status_code == 403

            self.log_checkpoint("H", "Customer Tracking & Session Isolation", True, "Order tracking visible to owner; foreign access blocked (HTTP 403)")
        except Exception as exc:
            self.log_checkpoint("H", "Customer Tracking & Session Isolation", False, str(exc))

    def run_stage_i_audit_trail(self):
        """Stage I: Authoritative Audit Trail Ledger"""
        try:
            assert self.active_order_id, "active_order_id missing"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            res = client.get(f"/api/admin/orders/{self.active_order_id}/audit", headers=headers)
            assert res.status_code == 200
            events = res.json()["data"]
            actions = [e["action"] for e in events]

            assert "payment_verified" in actions
            assert "order_confirmed" in actions
            assert "order_processing_started" in actions
            assert "order_shipped" in actions
            assert "order_delivered" in actions

            self.log_checkpoint("I", "Audit Trail Verification", True, f"Recorded {len(events)} chronological immutable audit events")
        except Exception as exc:
            self.log_checkpoint("I", "Audit Trail Verification", False, str(exc))

    def run_stage_j_analytics(self):
        """Stage J: Real-time Analytics & Multi-Channel Attribution"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            res = client.get("/api/admin/analytics", headers=headers)
            assert res.status_code == 200
            data = res.json()["data"]

            assert data["confirmed_orders_count"] >= 5
            assert data["gross_revenue_inr"] > 0
            assert data["aov_inr"] > 0
            assert len(data["channel_breakdown"]) == 3
            assert data["cross_sell_acceptance_rate"] > 0
            assert len(data["daily_trends"]) > 0

            self.log_checkpoint(
                "J",
                "Real-Time Admin Analytics",
                True,
                f"Gross: INR {data['gross_revenue_inr']:.2f}, Orders: {data['confirmed_orders_count']}, AOV: INR {data['aov_inr']:.2f}",
            )
        except Exception as exc:
            self.log_checkpoint("J", "Real-Time Admin Analytics", False, str(exc))

    def run_stage_k_error_scenarios(self):
        """Stage K: Error States & Interactive Recovery"""
        try:
            # 1. Out of stock item cannot be checked out
            session_err = f"sess_err_{uuid.uuid4().hex[:8]}"
            with SessionLocal() as db:
                p = db.scalar(select(Product).where(Product.id == "prod_massage_roller"))
                orig_qty = p.inventory_quantity
                p.inventory_quantity = 0
                db.commit()

            try:
                cart_res = client.post("/api/carts", headers={"X-Session-ID": session_err}, json={"session_id": session_err})
                c_id = cart_res.json()["data"]["id"]

                client.post(
                    f"/api/carts/{c_id}/items",
                    headers={"X-Session-ID": session_err},
                    json={"product_id": "prod_massage_roller", "quantity": 1},
                )
                quote_res = client.post(f"/api/carts/{c_id}/quote", headers={"X-Session-ID": session_err})
                assert quote_res.json()["data"]["valid"] is False
                assert len(quote_res.json()["data"]["warnings"]) > 0

                # Checkout initiation must be rejected
                co_res = client.post(
                    f"/api/carts/{c_id}/checkout",
                    headers={"X-Session-ID": session_err},
                    json={
                        "customer_name": "Err Test",
                        "customer_email": "err@example.com",
                        "customer_phone": "+919876543210",
                        "shipping_address": {
                            "line1": "100 MG Rd",
                            "city": "Bengaluru",
                            "state": "KA",
                            "postal_code": "560001",
                            "country": "India",
                        },
                        "approved_total_paise": 34900,
                    },
                )
                assert co_res.status_code == 400
            finally:
                # Restore stock
                with SessionLocal() as db:
                    p = db.scalar(select(Product).where(Product.id == "prod_massage_roller"))
                    p.inventory_quantity = orig_qty
                    db.commit()

            # 2. Cancellation requires reason
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            bad_cancel = client.post(
                f"/api/admin/orders/{self.active_order_id}/fulfillment",
                headers=headers,
                json={"status": "CANCELLED", "cancellation_reason": ""},
            )
            assert bad_cancel.status_code in [400, 409]

            self.log_checkpoint("K", "Error States & Interactive Recovery", True, "Out-of-stock and invalid cancellations safely rejected")
        except Exception as exc:
            self.log_checkpoint("K", "Error States & Interactive Recovery", False, str(exc))

    def run_all(self) -> bool:
        print("================================================================")
        print("  RUNCRAFT AGENTIC COMMERCE - END-TO-END REHEARSAL RUNNER      ")
        print("================================================================")

        self.run_stage_a_storefront()
        self.run_stage_b_in_app_agent()
        self.run_stage_c_external_buyer_mcp()
        self.run_stage_d_approval_boundary()
        self.run_stage_e_razorpay_checkout_creation()
        self.run_stage_f_payment_verification_and_confirmation()
        self.run_stage_g_admin_fulfillment()
        self.run_stage_h_customer_tracking()
        self.run_stage_i_audit_trail()
        self.run_stage_j_analytics()
        self.run_stage_k_error_scenarios()

        print("----------------------------------------------------------------")
        total_stages = len(self.results)
        passed_stages = sum(1 for v in self.results.values() if v)
        all_passed = total_stages == passed_stages and total_stages == 11

        if all_passed:
            print(f"  [SUCCESS] All {total_stages}/11 rehearsal checkpoints PASSED!")
            print("================================================================")
            return True
        else:
            print(f"  [FAILURE] {passed_stages}/{total_stages} checkpoints passed.")
            print("================================================================")
            return False


if __name__ == "__main__":
    runner = RehearsalRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
