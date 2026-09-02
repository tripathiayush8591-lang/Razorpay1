# Build Plan — Agentic Commerce V2

## Core Principle

Build the visible UI first with realistic mock data. Verify the UX. Then connect the backend. Every phase must produce something demonstrable.

## Phase 0 — Project Foundation

### 00 Context + Repository
- Create `/frontend`
- Create `/backend`
- Create `/context`
- Add `.env.example`
- Add README with local setup
- Add CORS configuration
- Add SQLite initialization
- Add frontend API client
- Add shared TypeScript domain types

Acceptance:
- React runs.
- FastAPI runs.
- Frontend can call `/api/health`.

### 01 Database Foundation
- SQLAlchemy models
- Alembic migration
- Seed merchant
- Seed demo admin
- Seed 8–12 realistic products/SKUs
- Seed merchant policies

Acceptance:
- Fresh database can be created from one documented command.
- Seed data appears in API response.

## Phase 1 — Modern Frontend Shell

### 02 Marketing / Storefront Landing
Build a polished merchant-facing landing page:
- navbar
- merchant branding
- hero
- featured products
- “Shop with AI” CTA
- how agentic shopping works
- trust/payment section
- footer

Acceptance:
- Visually polished at desktop and tablet widths.
- No backend dependency.

### 03 Admin Portal UI
Build:
- admin login
- admin dashboard
- catalog table
- add SKU form
- edit SKU form
- orders table
- policy settings
- channels page

Use mock data first.

Acceptance:
- Admin can navigate all major screens.
- Add/edit forms are complete visually.

### 04 Client Portal UI
Build:
- product grid
- product detail
- search/filter
- cart drawer/page
- checkout review
- order confirmation
- order tracking
- AI shopping assistant

Use mock data first.

Acceptance:
- Complete client journey can be clicked through without backend.

## Phase 2 — Admin + Catalog

### 05 Admin Authentication
- Login endpoint
- Demo admin session
- Protected admin routes

### 06 SKU CRUD
- GET products
- POST product
- PATCH product
- DELETE/deactivate product
- Validation

Acceptance:
Admin adds:
`RUN-X2-BLK-42`
and it appears in the client catalog after refresh.

### 07 Merchant Policies
Admin configures:
- max discount
- out-of-stock rule
- purchase approval requirement
- cross-sell rules
- delivery rules

Acceptance:
Policy changes affect quote/service behavior.

## Phase 3 — Common Commerce Layer

### 08 Product Discovery APIs
Implement:
- search_products
- get_product
- check_price
- check_inventory
- get_related_products
- get_offers
- delivery estimate

### 09 Cart
Implement:
- create_cart
- add_to_cart
- remove_from_cart
- get_cart

Backend owns cart state.

### 10 Final Quote
Implement authoritative:
- current product price
- inventory
- discount
- delivery
- cross-sell/policy validation
- total

Acceptance:
Changing a SKU price after it was added to cart is reflected in the final quote.

## Phase 4 — In-App Commerce Agent

### 11 Agent Chat UI
Build polished conversational UI:
- user messages
- agent messages
- product recommendation cards
- tool activity indicators
- cart summary
- approval card

### 12 Agent Orchestration
Agent must:
- understand constraints
- call commerce services
- recommend products
- add/remove cart items
- request final quote
- stop before payment until explicit approval

Acceptance:
“Build me a beginner running kit under ₹8,000” produces a useful cart using seeded products.

## Phase 5 — Razorpay

### 13 Checkout Creation
- Create merchant order
- Persist approved amount
- Create Razorpay Test Mode order server-side
- Return checkout payload

### 14 Razorpay Checkout
- Load Razorpay Checkout on client
- Complete test payment

### 15 Verification + Webhooks
- Verify checkout signature
- Verify webhook signature
- Handle `order.paid`, `payment.captured`, `payment.failed`
- Make webhook handler idempotent

Acceptance:
Successful payment creates one confirmed merchant order.
Failed payment retains cart and does not duplicate merchant order.

## Phase 6 — Order Tracking + Admin

### 16 Client Orders
- order confirmation
- order history
- order detail
- status timeline

### 17 Admin Orders
- order list
- order detail
- status
- payment state
- source/channel
- customer information

### 18 Audit Trail
Record:
- agent tool calls
- quote generation
- purchase approval
- checkout creation
- payment verification
- order confirmation

## Phase 7 — MCP + External AI Buyer

### 19 MCP Adapter
Expose:
- search_products
- get_product
- check_inventory
- create_cart
- add_to_cart
- get_cart
- get_final_quote
- create_checkout
- get_order
- get_order_status

All call existing commerce services.

### 20 External Buyer UI
Separate demo page/application area:
- natural-language request
- tool discovery
- agent reasoning summary
- products
- guest cart
- quote
- approval
- checkout
- order result

Acceptance:
External buyer completes the same commerce journey through MCP.

## Phase 8 — Demo Polish

### 21 Analytics
Admin:
- conversations
- carts
- orders
- revenue
- AOV
- cross-sell acceptance

### 22 Error States
Cover:
- empty catalog
- out of stock
- quote changed
- payment failed
- webhook delayed
- product unavailable
- agent cannot fulfill request

### 23 Final Demo Seed
Create deterministic seed data for the exact hackathon demo.

### 24 End-to-End Rehearsal
Run both journeys from a clean database.

## Phase Exit Rule

Do not start the next phase until:
- feature is visible
- happy path works
- failure state is handled
- no console errors
- context files are updated
