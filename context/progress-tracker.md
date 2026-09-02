# Progress Tracker — Agentic Commerce V2

## Current Status

**Phase:** 5 — Complete
**Last completed:** 15 Verification + Webhooks (Phase 5)
**Next:** 16 Client Orders (Phase 6)

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
- [ ] 16 Client Orders
- [ ] 17 Admin Orders
- [ ] 18 Audit Trail

### Phase 7 — MCP + External Buyer
- [ ] 19 MCP Adapter
- [ ] 20 External Buyer UI

### Phase 8 — Demo Polish
- [ ] 21 Analytics
- [ ] 22 Error States
- [ ] 23 Final Demo Seed
- [ ] 24 End-to-End Rehearsal

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

## Notes

Update this file after every completed build-plan item.
