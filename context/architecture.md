# Architecture — Agentic Commerce V2

## Architecture Decision

Use a deliberately simple two-application architecture:

```text
┌──────────────────────────────────────────────────────────┐
│                    React + Vite                          │
│                                                          │
│  Admin Portal              Client Storefront              │
│  Catalog / Orders          Shop / Agent / Cart / Orders  │
└───────────────────────┬──────────────────────────────────┘
                        │ REST + JSON
                        ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                          │
│ API Layer                                                │
│   ↓                                                      │
│ Commerce Services                                        │
│   Catalog | Cart | Quote | Policy | Orders | Checkout    │
│   ↓                                                      │
│ Agent Services                                           │
│   In-app Agent | External Buyer | MCP Adapter            │
│   ↓                                                      │
│ Integrations                                             │
│   OpenAI | Razorpay | optional Browser/API services      │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                     SQLite database
```

## Stack

### Frontend

- React 19
- Vite
- TypeScript strict
- React Router
- Tailwind CSS v4
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod
- Lucide React icons
- Recharts for lightweight admin analytics

### Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- SQLite
- httpx
- official OpenAI Python SDK
- MCP Python SDK
- Razorpay Python SDK or signed REST requests

### Development

- `npm` for frontend
- `uv` or `pip` + virtual environment for backend
- `.env` for secrets
- SQLite file stored under `backend/data/`

## Why SQLite

This is a hackathon demo. SQLite removes cloud database setup and avoids unnecessary infrastructure while still giving the backend real persistent storage.

SQLite is authoritative for:
- products/SKUs
- carts
- cart items
- merchant policies
- orders
- payment attempts
- audit events

localStorage is NOT authoritative for those values.

## Authentication Strategy

For the demo, keep authentication simple.

Admin:
- Demo credentials configured through environment variables.
- Backend issues a short-lived demo session token or uses a simple signed session mechanism.
- Never store admin password in frontend source.

Client:
- Guest shopping is supported.
- A lightweight client session ID can be stored in localStorage.
- Backend associates carts/orders with the guest session and verified checkout contact.

Do not build a large OAuth system for the hackathon unless later required.

## Data Model

### merchants
- id
- name
- slug
- created_at

### admin_users
- id
- merchant_id
- email
- password_hash
- role
- created_at

### products
- id
- merchant_id
- sku
- name
- category
- short_description
- description
- price_paise
- inventory_quantity
- image_url
- tags_json
- attributes_json
- active
- created_at
- updated_at

### merchant_policies
- id
- merchant_id
- max_discount_percent
- allow_out_of_stock
- require_purchase_approval
- cross_sell_rules_json
- delivery_rules_json
- updated_at

### carts
- id
- merchant_id
- session_id
- status
- currency
- created_at
- updated_at

### cart_items
- id
- cart_id
- product_id
- quantity
- unit_price_paise_snapshot
- created_at
- updated_at

### merchant_orders
- id
- merchant_id
- cart_id
- customer_name
- customer_email
- customer_phone
- shipping_address_json
- amount_paise
- currency
- status
- razorpay_order_id
- approved_at
- paid_at
- confirmed_at
- created_at
- updated_at

### payment_attempts
- id
- merchant_order_id
- razorpay_order_id
- razorpay_payment_id
- status
- signature_verified
- raw_event_reference
- created_at

### audit_events
- id
- merchant_id
- session_id
- actor_type
- action
- entity_type
- entity_id
- metadata_json
- created_at

## Commerce Service Boundary

The following functions are backend services, not frontend logic:

- search_products
- get_product
- check_price
- check_inventory
- get_delivery_estimate
- get_related_products
- get_offers
- create_cart
- add_to_cart
- remove_from_cart
- get_cart
- get_final_quote
- create_checkout
- get_order
- get_order_status

## REST API

### Admin

- `POST /api/admin/login`
- `GET /api/admin/me`
- `GET /api/admin/products`
- `POST /api/admin/products`
- `GET /api/admin/products/{product_id}`
- `PATCH /api/admin/products/{product_id}`
- `DELETE /api/admin/products/{product_id}`
- `GET /api/admin/orders`
- `GET /api/admin/orders/{order_id}`
- `GET /api/admin/policies`
- `PUT /api/admin/policies`
- `GET /api/admin/analytics`

### Client Commerce

- `GET /api/products`
- `GET /api/products/{product_id}`
- `POST /api/carts`
- `GET /api/carts/{cart_id}`
- `POST /api/carts/{cart_id}/items`
- `DELETE /api/carts/{cart_id}/items/{item_id}`
- `POST /api/carts/{cart_id}/quote`
- `POST /api/carts/{cart_id}/checkout`
- `GET /api/orders/{order_id}`
- `GET /api/orders/{order_id}/status`

### Agent

- `POST /api/agent/chat`
- `POST /api/agent/tools/search-products`
- `POST /api/agent/tools/get-product`
- `POST /api/agent/tools/add-to-cart`
- `POST /api/agent/tools/remove-from-cart`
- `POST /api/agent/tools/get-final-quote`

### Razorpay

- `POST /api/payments/razorpay/create-order`
- `POST /api/payments/razorpay/verify`
- `POST /api/webhooks/razorpay`

### MCP

- `/mcp`

MCP tools call the same commerce service functions used by REST.

## MCP Rule

Correct:

```text
MCP tool
   ↓
Commerce service
   ↓
SQLite
```

Incorrect:

```text
MCP tool
   ↓
custom business logic
   ↓
SQLite
```

The adapter must stay thin.

## Payment State Machine

```text
PENDING_PAYMENT
       ↓ verified payment
PAID
       ↓ confirmation logic
CONFIRMED
       ↓
FULFILLMENT
```

Failure:

```text
PENDING_PAYMENT
       ↓ payment.failed
PENDING_PAYMENT
       ↓ retry
same merchant order
```

Never create a second merchant order just because a payment attempt failed.

## Razorpay Security

- Key secret stays on FastAPI.
- Amount is calculated by backend.
- Frontend receives only public key ID and Razorpay order ID.
- Verify checkout signature server-side.
- Verify webhook signature.
- Treat verified webhook/API status as payment source of truth.
