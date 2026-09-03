# End-to-End Rehearsal Checklist — RunCraft Agentic Commerce

This document is the definitive, step-by-step rehearsal guide for testing and demonstrating the RunCraft Agentic Commerce MVP. It defines exact URLs, actions, expected system outputs, and failure checkpoints across all 11 stages.

---

## 0. Pre-Flight Demo Reset

Before beginning a demo session or rehearsal run, reset the database to a clean, deterministic baseline:

```bash
# In backend/ directory:
.\.venv\Scripts\python.exe -m app.db.seed --reset
```

### Expected Baseline State:
- **Merchant:** RunCraft Athletics (`merch_runcraft_demo`)
- **Admin:** `admin@runcraft.internal` / `demosecret123`
- **Catalog:** 10 canonical running products with 50–100 units in physical inventory.
- **Policies:** Max discount 15%, approval required, out-of-stock disabled, cross-sell (Shoes → Socks).
- **Baseline Orders:** 5 orders (1 `CONFIRMED`, 1 `PROCESSING`, 1 `SHIPPED`, 2 `DELIVERED`).
- **Baseline Analytics:** ₹36,190.00 gross revenue, 5 confirmed orders, ₹7,238.00 AOV, 71.4% conversion rate.

---

## Demo Flow Matrix

| Stage | Name | Target Interface | Primary Narrative / Checkpoint |
|---|---|---|---|
| **A** | Storefront Shopping | Client Portal (`/` & `/shop`) | Human browsing, real-time availability, authoritative cart & quote |
| **B** | In-App AI Assistant | Client Portal (`/shop` Drawer) | Conversational kit building, tool trace, budget adherence |
| **C** | External AI Buyer + MCP | `/external-buyer` | Consuming merchant catalog via MCP without duplicating logic |
| **D** | Human Approval Boundary | AI Assistant & External Buyer | Zero autonomous order/payment creation; explicit user approval |
| **E** | Razorpay Test Checkout | `/checkout` & External Buyer | Server-side order creation, live price revalidation, modal launch |
| **F** | Order Confirmation | Checkout Modal & Webhook | Server cryptographic signature verification, single stock decrement |
| **G** | Admin Fulfillment | `/admin/orders` | `CONFIRMED` → `PROCESSING` → `SHIPPED` → `DELIVERED` lifecycle |
| **H** | Customer Tracking | `/orders/{orderId}` & `/orders` | Real-time timeline, carrier/tracking details, guest session isolation |
| **I** | Audit Trail Ledger | `/admin/orders/{orderId}` | Chronological immutable log of all actor events & tool calls |
| **J** | Real-Time Analytics | `/admin/dashboard` | Multi-channel attribution, conversion funnel, cross-sell analysis |
| **K** | Error Recovery | Catalog, Cart, Checkout | Out-of-stock badges, 409 stale quote recovery, friendly guardrails |

---

## Detailed Rehearsal Checklist

### Stage A: Storefront Shopping
1. **Navigate to:** `http://localhost:5173/`
   - **Check:** Brand header displays "RunCraft Athletics", cart icon badge starts at `0`.
   - **Check:** Featured products carousel/grid renders with prices in ₹ and high-resolution running gear imagery.
2. **Navigate to:** `http://localhost:5173/shop`
   - **Action:** Filter by category "Running Shoes".
   - **Check:** Displays *RunPro X2 Road Runner* (₹5,499), *SwiftStride Daily Trainer* (₹3,999), and *Carbon Race Elite 3* (₹14,999).
3. **Action:** Click *RunPro X2 Road Runner*.
   - **Check:** Product detail page loads. Shows in-stock badge, EU size attributes, and description.
4. **Action:** Click **Add to Cart**.
   - **Check:** Cart drawer opens immediately. Shows 1 item, subtotal ₹5,499.00, free shipping applied (> ₹2,000 threshold), and total ₹5,499.00.
   - **Check:** Storefront header cart badge increments to `1`.
   - **Failure Checkpoint:** If badge does not increment, verify `localStorage['guest_session_id']` and TanStack Query cache invalidation.

---

### Stage B: In-App Gemini Agent
1. **Action:** On `http://localhost:5173/`, click the floating AI Assistant button or "Shop with AI".
2. **Action:** In the chat input, submit:
   ```text
   Build me a beginner running kit under ₹8,000
   ```
3. **Check:**
   - Agent tool activity indicator surfaces real execution: `search_products`, `check_inventory`, `add_to_cart`, `get_final_quote`.
   - Agent recommends *RunPro X2 Road Runner* (₹5,499) and *FleetStride Anti-Blister Socks* (₹699).
   - Agent displays an authoritative `ApprovalCard` with:
     * Line items: Shoes + Socks
     * Subtotal: ₹6,198.00
     * Delivery: Free
     * Total: ₹6,198.00 (under ₹8,000 budget!)
     * Prominent CTA: **Approve & Checkout**
   - Cart drawer and header badge immediately reflect 2 items (synced to the shared `guest_session_id`).
   - **Failure Checkpoint:** If Gemini API rate limits (429), verify that the deterministic rule-based fallback smoothly steps in without crashing or displaying raw error text.

---

### Stage C: External AI Buyer + MCP
1. **Navigate to:** `http://localhost:5173/external-buyer`
2. **Check:** Screen shows MCP Server Connection status: `CONNECTED (streamable_http / mcp)`.
3. **Action:** In the prompt box, submit:
   ```text
   Find me beginner running shoes under ₹6,000
   ```
4. **Check:**
   - External buyer trace logs tool discovery: 13 commerce tools available.
   - External buyer executes `search_products(q="running shoes", max_price_paise=600000)`.
   - Returns *SwiftStride Daily Trainer* (₹3,999) and *RunPro X2 Road Runner* (₹5,499).
5. **Action:** Click **Buy with External AI** on *SwiftStride Daily Trainer*.
   - **Check:** External buyer calls `create_cart`, `add_to_cart`, and `get_final_quote`.
   - Authoritative quote card appears with subtotal ₹3,999.00, delivery ₹0.00 (over threshold), total ₹3,999.00.
   - **Failure Checkpoint:** Verify external buyer session ID begins with `ext_buyer_` and cannot query or modify the in-app storefront cart.

---

### Stage D: Human Approval Boundary
1. **Inspection Checkpoint:**
   - Neither the In-App Agent (Stage B) nor the External AI Buyer (Stage C) have initiated a transaction or confirmed an order.
   - Both interfaces are paused at the explicit human approval boundary.
   - The user must explicitly review the quote and click **Approve & Pay**.

---

### Stage E: Razorpay Test Checkout Initiation
1. **Action:** In the storefront checkout page (`/checkout`) or external buyer approval card, click **Approve & Pay ₹X**.
2. **Backend Execution:**
   - Frontend calls `POST /api/carts/{id}/checkout` passing `approved_total_paise`.
   - Backend re-validates live catalog prices and stock against the approved total.
   - Backend creates/reuses a `MerchantOrder` in `PENDING_PAYMENT` and calls Razorpay API to generate a test order.
3. **Check:**
   - Official Razorpay Test Mode checkout modal launches over the application.
   - Modal displays "RunCraft Athletics" branding and exact approved amount in ₹.
   - **Failure Checkpoint:** If modal fails to load, check browser console for `window.Razorpay` script injection or test key configuration.

---

### Stage F: Payment Verification & Order Confirmation
1. **Action:** In Razorpay Test modal:
   - Select **Netbanking** → **State Bank of India (Success)** or **Cards** → **Success**.
   - Click **Pay ₹X**.
2. **Backend Execution:**
   - Client receives `razorpay_payment_id` and HMAC signature from Razorpay.
   - Client submits `POST /api/payments/razorpay/verify`.
   - Server cryptographically validates HMAC signature against `settings.RAZORPAY_KEY_SECRET`.
   - Server queries Razorpay API to ensure status is `captured`.
   - Server atomically decrements physical inventory in SQLite.
   - Server marks cart `converted` and order `CONFIRMED`.
3. **Check:**
   - Storefront navigates automatically to `/orders/{orderId}`.
   - Green banner displays: "Order Confirmed! Thank you for your purchase."
   - Payment status displays `PAID (Razorpay)`.
   - Order fulfillment timeline displays step 1: `Order Confirmed`.
   - Cart drawer empties and header badge resets to `0`.
   - **Failure Checkpoint:** Refreshing `/orders/{orderId}` must not re-trigger inventory decrements or duplicate the order.

---

### Stage G: Admin Order Fulfillment
1. **Navigate to:** `http://localhost:5173/admin/orders`
2. **Action:** Log in with `admin@runcraft.internal` / `demosecret123`.
3. **Check:** Orders table displays the newly confirmed order and the seeded baseline order (`ord_demo_conf_01`).
4. **Action:** Click on the `CONFIRMED` order to open detail view.
5. **Action:** Click **Mark as Processing**.
   - **Check:** Order badge immediately changes to amber `PROCESSING`. Timeline marks step 2 complete.
6. **Action:** Click **Mark as Shipped**.
   - In modal, enter Carrier: `BlueDart Express`, Tracking #: `BD-LIVE-9012`.
   - **Check:** Order badge changes to blue `SHIPPED`. Carrier and tracking number appear in fulfillment details.
7. **Action:** Click **Mark as Delivered**.
   - **Check:** Order badge changes to green `DELIVERED`. Delivered timestamp is recorded.
   - **Failure Checkpoint:** Verify that clicking fulfillment buttons does not decrement inventory (inventory was already decremented during payment verification).

---

### Stage H: Customer Tracking & Session Isolation
1. **Navigate to:** Customer tracking URL: `http://localhost:5173/orders/{orderId}`
   - **Check:** Customer sees live updated status: `DELIVERED` with carrier `BlueDart Express` and tracking number `BD-LIVE-9012`.
2. **Session Isolation Verification:**
   - Open a private/incognito window (new `guest_session_id`).
   - Navigate to `http://localhost:5173/orders`.
   - **Check:** Order history is completely blank. The order placed in Session A is completely invisible to Session B.
   - Navigate directly to `http://localhost:5173/orders/{orderId}`.
   - **Check:** Displays a clear "Access Denied / Forbidden" error alert.

---

### Stage I: Authoritative Audit Trail
1. **Navigate to:** Admin order detail: `http://localhost:5173/admin/orders/{orderId}`
2. **Check:** Audit Trail ledger at bottom of screen displays chronological records:
   - `payment_verified` (actor: `shopper`, amount in paise)
   - `order_confirmed` (actor: `system`, items count)
   - `order_processing_started` (actor: `admin`)
   - `order_shipped` (actor: `admin`, carrier info)
   - `order_delivered` (actor: `admin`)

---

### Stage J: Real-Time Admin Analytics
1. **Navigate to:** `http://localhost:5173/admin/dashboard`
2. **Check:**
   - **Topline Cards:** Gross revenue has increased by the newly placed order amount. Confirmed orders counter incremented by 1.
   - **Funnel Metrics:** Carts created, converted, and conversion rate updated live.
   - **Channel Attribution Cards:** Shows revenue share across:
     * `Direct Storefront`
     * `In-App AI Agent`
     * `External AI Buyer (MCP)`
   - **Cross-Sell Performance:** Shows matches for `Running Shoes` → `Running Socks`.
   - **Daily Trends Chart:** Active bars showing daily distribution.

---

### Stage K: Error Recovery Scenarios
1. **Out of Stock Guardrail:**
   - In Admin Catalog (`/admin/catalog`), edit *Deep Tissue Lacrosse Massage Ball* to stock `0`.
   - In Storefront, open cart drawer with the ball: displays red warning badge *"Out of stock — please remove"*.
   - Checkout CTA is disabled with an amber warning until item is removed.
2. **Stale Quote Detection:**
   - User initiates checkout with an item.
   - Admin changes price in catalog before user clicks pay.
   - User clicks pay: backend returns `409 Conflict`.
   - Frontend shows amber alert: *"Price has changed. Review new total."* with an interactive **Refresh Quote** button.
3. **Payment Modal Dismissal:**
   - Open Razorpay modal and close it without paying.
   - Frontend displays friendly blue notice: *"Payment window was closed. Your cart and shipping details are preserved — click 'Approve & Pay' whenever you are ready."* Cart remains intact.

---

## Automated Verification Commands

Run these commands before any live presentation:

```bash
# 1. Reset database to clean deterministic state
.\.venv\Scripts\python.exe -m app.db.seed --reset

# 2. Run automated rehearsal script (verifies all 11 stages programmatically)
.\.venv\Scripts\python.exe -m app.demo.rehearsal

# 3. Run full automated backend test suite
.\.venv\Scripts\python.exe -m pytest

# 4. Verify frontend build
cd ../frontend
npm run build
```
