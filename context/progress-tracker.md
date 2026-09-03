# Progress Tracker — Agentic Commerce V2

## Current Status

**Phase:** 8 — Completed (Ready for Final Manual Testing & Review)
**Last completed:** 24 End-to-End Rehearsal (Phase 8)
**Next:** Final Manual Testing & Review

## Progress

### Phase 0 — Foundation
- [x] 00 Context + Repository
- [x] 01 Database Foundation

### Phase 1 — Frontend Shell
- [x] 02 Marketing / Storefront Landing
- [x] 03 Admin Portal UI
- [x] 04 Client Portal UI

### Phase 2 — Admin + Catalog
- [x] 05 Admin Authentication
- [x] 06 SKU CRUD
- [x] 07 Merchant Policies

### Phase 3 — Common Commerce Layer
- [x] 08 Product Discovery APIs
- [x] 09 Cart
- [x] 10 Final Quote

### Phase 4 — In-App Commerce Agent
- [x] 11 Agent Chat UI
- [x] 12 Agent Orchestration

### Phase 5 — Razorpay
- [x] 13 Checkout Creation
- [x] 14 Razorpay Checkout
- [x] 15 Verification + Webhooks

### Phase 6 — Orders + Admin
- [x] 16 Client Orders
- [x] 17 Admin Orders
- [x] 18 Audit Trail

### Phase 7 — MCP + External Buyer
- [x] 19 MCP Adapter
- [x] 20 External Buyer UI

### Phase 8 — Demo Polish
- [x] 21 Analytics
- [x] 22 Error States
- [x] 23 Final Demo Seed
- [x] 24 End-to-End Rehearsal

## Decisions

### 2026-09-02 — Stack Reset
- Frontend changed from Next.js to React + Vite.
- Backend changed to FastAPI.
- Database changed from InsForge to local SQLite.
- Supabase is not used.
- InsForge is not used.
- Separate Admin and Client portals are mandatory.

### 2026-09-02 — Data Authority
Backend + SQLite are authoritative for catalog, price, inventory, cart, quote, policies, orders and payment state.

### 2026-09-02 — Payment
Razorpay Test Mode is retained. Explicit purchase approval is mandatory.

### 2026-09-02 — Phase 0 Foundation Verified
- Backend: FastAPI + SQLite + SQLAlchemy 2.x + Alembic configured and passing tests.
- Database: 9 authoritative commerce entities migrated and seeded with RunCraft merchant, admin, 10 realistic running products, and merchant policies.
- Frontend: React 19 + Vite + Tailwind CSS v4 configured with design tokens, strict TypeScript domain types, and typed API client.
- Verification: End-to-end API health and product queries verified. Frontend builds cleanly.

### 2026-09-03 — Phase 2 Admin + Catalog Verified
- Admin Auth: Bcrypt password hashing/verification, 24h cryptographically signed Bearer session tokens, sessionStorage persistence, protected admin route guards.
- SKU CRUD: Full product CRUD in SQLite with thin routes and domain service layer (`catalog.py`).
- Image Upload: Multipart upload to local disk (`backend/data/uploads/products/`) served statically via FastAPI StaticFiles at `/static/uploads/...`.
- Soft Delete: `DELETE /api/admin/products/{id}` sets `active=False`, hiding products from storefront while retaining them in admin.
- Policies: Configurable guardrails, delivery rules, and editable cross-sell pairings (`trigger_category` -> `recommend_category`).
- Client Storefront: `ShopPage`, `FeaturedProducts`, and `ProductDetailPage` connected to real backend (`GET /api/products`) with TanStack Query.
- Verified Acceptance Criterion: Adding a new SKU in admin immediately surfaces it in the client storefront upon refresh.

### 2026-09-03 — Phase 3 Common Commerce Layer Verified
- Product Discovery APIs: Pure service functions in `discovery.py` for `check_price`, `check_inventory`, `get_related_products`, `get_offers`, and `estimate_delivery`. Exposed via `/api/products/{id}/availability`, `/api/products/{id}/related`, `/api/offers`, and `/api/delivery/estimate`.
- Cart Management: Idempotent get-or-create cart by `guest_session_id` persisted in `localStorage`. Full CRUD (`POST /api/carts/{id}/items`, `PATCH /api/carts/{id}/items/{item_id}`, `DELETE /api/carts/{id}/items/{item_id}`).
- Cart Ownership Security: Every cart access and mutation verifies ownership against `X-Session-ID` header; arbitrary access returns HTTP 403 Forbidden.
- Final Quote Engine: `POST /api/carts/{id}/quote` re-queries live `Product.price_paise` and physical inventory from SQLite. Evaluates merchant delivery rules (free shipping threshold) and out-of-stock policies.
- Verified Acceptance Criterion: Changing a SKU price in SQLite after it was added to a cart is immediately reflected in the final quote subtotal and line price, ignoring the original snapshot price.
- Frontend Migration: Connected `ProductCard`, `ProductDetailPage`, `CartDrawer`, `CartPage`, `CartSummary`, and `StorefrontHeader` to real backend cart and quote endpoints via TanStack Query. Built cleanly with 0 TypeScript/build errors.

### 2026-09-03 — Phase 4 In-App AI Agent Verified
- Agent LLM Integration: Google Gemini integration (`app/integrations/gemini.py`) using `google-genai` (2.8.0) and `gemini-2.5-flash` with registered function declarations.
- Deterministic Fallback: Robust rule-based fallback orchestrator (`app/services/agent_fallback.py`) executing real Phase 3 commerce services against live SQLite data when `GEMINI_API_KEY` is absent, invalid, or failing.
- Tool Execution Engine: Pure adapter service (`app/services/agent_tools.py`) wrapping catalog search, live inventory verification, policy-driven related products, cart mutation, and authoritative quotes. Records structured `ToolActivityItem` status.
- Direct REST Endpoints: Exposed `POST /api/agent/chat` and direct test routes `POST /api/agent/tools/*` enforcing session cart ownership (`X-Session-ID`).
- Session & Cart Binding: AI assistant uses the exact same `guest_session_id` and `cart_id` as storefront. Changes made by the agent immediately sync with storefront header badge and `CartDrawer`.
- Audit Logging: Recorded `audit_events` row on each agent chat turn with tools executed and quote total.
- Approval Boundary: Stops before payment. Presents authoritative quote on `ApprovalCard`. Clicking "Approve & Checkout" navigates to `/checkout` without initiating payment or creating orders.
- Frontend Migration: Rewired `AssistantPanel`, `ChatMessage`, `ProductRecommendation`, and `ApprovalCard` to live TanStack Query mutations. Built cleanly with 0 errors.
- Verified Acceptance Criterion: "Build me a beginner running kit under ₹8,000" selects RunPro X2 road shoe + anti-blister technical socks, verifies inventory, adds them to cart, calculates authoritative quote of ₹6,198 (under ₹8,000 limit), and requests explicit user approval.
- Automated Tests: 10 dedicated Phase 4 test cases and 21 total suite test cases passing with 100% success.

### 2026-09-03 — Phase 5 Razorpay Checkout & Payment Verified
- Razorpay Integration Wrapper: Clean isolation layer (`app/integrations/razorpay.py`) using official `razorpay` Python SDK, handling order creation, provider payment status verification, and HMAC-SHA256 signature checks. Secrets never leave backend.
- Authoritative Checkout Initiation: `POST /api/carts/{cart_id}/checkout` revalidates live SQLite prices and inventory against `approved_total_paise`. Rejects stale quotes with HTTP 409 Conflict and updated quote total. Creates/reuses `MerchantOrder` (status: `PENDING_PAYMENT`).
- Immutable Order Snapshot: Preserves purchased product identity, SKU, name, quantity, unit price, and line total in `items_snapshot_json`, protecting historical integrity.
- Server-Side Verification: `POST /api/payments/razorpay/verify` cryptographically verifies signature using server-stored `razorpay_order_id`, and authoritatively checks that provider payment status is `captured`.
- Idempotency & Inventory Safety: Decrements physical inventory and marks cart `converted` exactly once upon transitioning to `PAID`/`CONFIRMED`. Re-verification or retries return success idempotently without double decrement.
- Webhook Handler: `POST /api/webhooks/razorpay` verifies signature on raw body, checks `X-Razorpay-Event-Id` uniqueness against `processed_webhook_events` table, and safely reconciles out-of-order events without downgrading confirmed orders.
- Session Isolation: `GET /api/orders/{order_id}` enforces strict session ownership.
- Official Razorpay Web Modal: Frontend `CheckoutForm.tsx` loads official `checkout.js`, initializes `window.Razorpay` with RunCraft branding, passes checkout data, handles modal callback, and routes to `/orders/{orderId}` upon verified backend response.
- Automated Tests: 19 dedicated Phase 5 test cases and 40 total test suite cases passing with 100% success.

### 2026-09-03 — Phase 6 Order Management, Fulfillment & Audit Verified
- Alembic Migration: Added tracking columns (`processing_at`, `shipped_at`, `delivered_at`, `cancelled_at`, `cancellation_reason`, `carrier`, `tracking_number`) via `0003_phase6_fulfillment_and_tracking.py` without destructive reset.
- Guest Order History: Added `GET /api/orders` enforcing strict guest session boundary via `X-Session-ID`; orders from Session A are completely hidden from Session B.
- Admin Order Management: Exposed `GET /api/admin/orders` (with text search and status filter), `GET /api/admin/orders/{id}`, and `GET /api/admin/orders/{id}/audit`.
- State Machine & Fulfillment Lifecycle: Supported `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` with atomic conditional execution (`UPDATE ... WHERE id = :id AND status IN (:expected_statuses)`). Zero inventory decrement during fulfillment.
- Idempotency & Race Safety: Duplicate same-status fulfillment requests return cleanly with HTTP 200 without modifying timestamps or duplicating audit events. Conflicting status transitions return HTTP 409.
- Admin Cancellation: Allowed exclusively for `CONFIRMED` or `PROCESSING` orders with mandatory cancellation reason. Physical inventory is untouched (no auto-restock in MVP) and no fake refund is issued.
- Explicit Payment vs Fulfillment Semantics: Payment state (`PAID`, `PENDING_PAYMENT`) and fulfillment state (`CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`) are separated cleanly in schemas and UI.
- TanStack Query UI: Connected `AdminOrders.tsx`, `AdminOrderDetail.tsx`, `OrdersPage.tsx`, and `OrderDetailPage.tsx` to live backend data with real-time audit trail and timeline steps.
- Automated Verification: 23 dedicated Phase 6 tests and 63 total suite tests passing with 100% success. Frontend production build compiled cleanly with 0 errors.

### 2026-09-03 — Phase 7 Model Context Protocol (MCP) & External AI Buyer Verified
- Official MCP Python SDK v2: Pinned `mcp>=2.1.1,<3.0.0` and `mcp-types>=2.1.1,<3.0.0` with modern `MCPServer("runcraft-commerce")`.
- Streamable HTTP Transport: Mounted `/mcp` onto FastAPI using `create_streamable_http_app()` with async session manager task group initialized in FastAPI lifespan.
- Standard I/O (stdio) Transport: Created runnable CLI entrypoint `python -m app.mcp.server` sharing the exact same tool declarations for Claude Desktop and Cursor.
- Thin Adapter Architecture: Implemented 13 commerce tools (`search_products`, `get_product`, `check_inventory`, `get_delivery_estimate`, `get_offers`, `create_cart`, `add_to_cart`, `remove_from_cart`, `get_cart`, `get_final_quote`, `create_checkout`, `get_order`, `get_order_status`) delegating 100% of logic to existing Phase 3–6 services.
- Strict Human Approval Boundary: Enforced that an external AI tool call can never autonomously confirm orders or mark payments as paid. `create_checkout` verifies `approved_total_paise` against live SQLite prices, creates orders in `PENDING_PAYMENT`, and requires human Razorpay signature verification to confirm.
- Session Isolation: Blocked cross-session cart access and order inspection with HTTP 403 Forbidden.
- Audit Trail: Logged all external AI tool calls to `audit_events` with `actor_type="external_ai_buyer"`.
- External AI Buyer UI: Created `ExternalBuyerPage.tsx` at `/external-buyer` demonstrating the complete Demo 3 journey: natural language request, live tool execution trace, structured recommendations, authoritative quote card, explicit human approval CTA, Razorpay Test modal launch, and order status retrieval.
- Automated Verification: 9 dedicated Phase 7 MCP tests and 72 total suite tests passing with 100% success. Frontend production build compiled in 5.74s with 0 errors.
 
### 2026-09-03 — Phase 8 Task 21 Admin Analytics Verified
- Authoritative Backend Analytics Service: Created `app/services/analytics.py` computing gross confirmed revenue, confirmed orders, active SKUs, AOV, cart creation & conversion funnels, in-app agent chat turns/sessions, external AI MCP tool executions/sessions, cross-sell policy basket attachment, and daily trends directly from SQLite.
- Channel Attribution Engine: Authoritatively distinguished buyer journeys (`direct_storefront`, `in_app_agent`, `external_ai`) by correlating confirmed order cart session IDs with `audit_events` ledger without mutating base schemas.
- Policy Cross-Sell Analysis: Evaluated live confirmed order line items against `merchant_policies.cross_sell_rules_json`, measuring basket co-occurrence of trigger and recommend categories (e.g. Running Shoes -> Running Socks).
- REST Route: Exposed `GET /api/admin/analytics` secured with admin Bearer token and supporting dynamic `days` window filtering.
- Complete Mock Data Elimination: Overhauled `AdminDashboard.tsx`, entirely removing `useMockCommerce()` and hardcoded placeholder metrics. Connected live queries with TanStack Query.
- Dashboard Enhancements: Added 7-day / 30-day / All-time pill filter, conversion funnel step cards, AI telemetry counters, channel revenue share cards, live recent orders table, and low stock inventory watchlist with loading skeletons and error resilience.
- Automated Verification: 6 dedicated Task 21 tests and 84 total backend test suite tests passing with 100% success. Frontend production build compiled in 3.86s with 0 errors.

### 2026-09-03 — Phase 8 Task 22 Error States & Messaging Verified
- Standard UI Primitives: Created lightweight, zero-dependency `Toast.tsx` notification system (`ToastProvider`, `useToast()`) with info/success/warning/error variants and auto-dismiss timers, mounted globally in `App.tsx`. Created reusable `EmptyState.tsx` adhering to `ui-rules.md`.
- Storefront & Cart Stock Boundaries: In `MockCommerceContext.tsx` and `CartDrawer.tsx`, surfaced out-of-stock and inventory threshold boundaries directly. Added inline red badge (`Out of stock — please remove`) and yellow badge (`Only X available in warehouse`) on line items. Disabled checkout CTA with an amber warning when out-of-stock items remain in cart.
- Stale Quote Detection & Interactive Recovery: In `CheckoutForm.tsx`, detected HTTP 409 and price/quote mismatches during checkout initiation. Displayed an authoritative warning banner with an interactive "Refresh Quote & Review Total" CTA that synchronizes the form with server-revalidated prices without reloading.
- Payment Dismissal & Gateway Feedback: Handled Razorpay modal `ondismiss` by presenting non-intrusive reassuring info feedback: "Payment window was closed. Your cart and shipping details are preserved — click 'Approve & Pay' whenever you are ready."
- Order Payment Status Real-Time Polling: In `OrderDetailPage.tsx`, added amber banner for orders in `PENDING_PAYMENT` with auto-polling every 3 seconds and a manual "Check Status Now" CTA, ensuring clear status separation from confirmed fulfillment.
- In-App Agent & External Buyer Guardrails: Enhanced `agent_fallback.py` and `ExternalBuyerPage.tsx` with friendly catalog scope guidance when users ask for non-running items (laptops, tennis, etc.) or set impossible budgets (< ₹2,999), stopping before checkout without hallucinating or crashing.
- Design Token Compliance: Verified all error alerts, toasts, and status notices strictly use design tokens (`error`, `error-light`, `error-foreground`, `warning`, `warning-light`, `info`, `surface`, `border`).
- Automated Verification: Added 7 dedicated error state regression tests in `test_error_states.py`. Full test suite of 93 backend tests passing with 100% success in 34.31s. Frontend built with Vite with 0 errors in 3.79s.

### 2026-09-03 — Phase 8 Task 23 Deterministic Final Demo Seed Verified
- Canonical Product Catalog: Maintained 10 deterministic RunCraft products (`RUN-X2-BLK-42`, `SWIFT-STRIDE-BLU-41`, `CARB-RACE-NEON-42`, etc.) with ample physical stock (50–100 units), tags, attributes, and high-resolution assets.
- Clean Idempotency & Reset: Built repeatable seeding engine supporting safe repeated runs and clean `--reset` mode to clear transient test clutter.
- Realistic Multi-Channel Baseline: Seeded 5 confirmed/fulfilled baseline orders, active/abandoned carts, and audit events across `direct_storefront`, `in_app_agent`, and `external_ai` channels with realistic time distributions.
- Fulfillment Demonstration Ready: Seeded order `ord_demo_conf_01` in `CONFIRMED` status, ready for instant live demonstration of the fulfillment state machine on stage.
- Immediate Authoritative Analytics: Baseline seed immediately delivers non-zero, genuine analytics: ₹36,190.00 revenue, 5 orders, ₹7,238.00 AOV, 71.4% conversion rate, and 2 cross-sell attachments.
- Automated Tests: 6 dedicated seed tests in `tests/test_demo_seed.py` passing with 100% success.

### 2026-09-03 — Phase 8 Task 24 End-to-End Rehearsal Verified
- Programmatic Rehearsal Engine: Created `app/demo/rehearsal.py` validating all 11 stages (A through K): Storefront shopping, In-app agent, External AI Buyer + MCP, Human approval boundary, Razorpay checkout creation, Payment signature verification, Admin fulfillment state machine, Customer tracking & session boundary, Audit trail ledger, Real-time analytics, and Error/recovery scenarios.
- Zero-Regression Rehearsal Pytest: Wrapped runner into `tests/test_rehearsal.py` passing in 5.23s.
- Rehearsal Checklist & Presenter Guide: Created `context/rehearsal-checklist.md` with explicit URLs, clicks, inputs, expected UI outputs, and failure checkpoints for the hackathon demo.

## Notes

Update this file after every completed build-plan item.
