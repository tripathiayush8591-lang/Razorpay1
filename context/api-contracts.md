# API Contracts — Agentic Commerce V2

All API contracts below are illustrative implementation contracts. Keep response shapes stable once implementation starts.

## Common Response

Success:

```json
{
  "success": true,
  "data": {}
}
```

Failure:

```json
{
  "success": false,
  "error": {
    "code": "STRING_CODE",
    "message": "Human readable message"
  }
}
```

## Product

```json
{
  "id": "prod_001",
  "sku": "RUN-X2-BLK-42",
  "name": "RunPro X2",
  "category": "Running Shoes",
  "short_description": "Lightweight road running shoes for beginners.",
  "description": "Full product description.",
  "price_paise": 549900,
  "inventory_quantity": 12,
  "image_url": "https://...",
  "tags": ["running", "beginner", "road"],
  "attributes": {
    "color": "Black",
    "size": "42"
  },
  "active": true
}
```

## Search

`GET /api/products?q=running&category=shoes&max_price_paise=600000`

Returns products from the backend catalog only.

## Cart

`POST /api/carts`

```json
{
  "session_id": "guest_session_123"
}
```

`POST /api/carts/{cart_id}/items`

```json
{
  "product_id": "prod_001",
  "quantity": 1
}
```

## Quote

`POST /api/carts/{cart_id}/quote`

Returns:

```json
{
  "cart_id": "cart_001",
  "items": [],
  "subtotal_paise": 589800,
  "discount_paise": 0,
  "delivery_paise": 0,
  "total_paise": 589800,
  "currency": "INR",
  "valid": true,
  "warnings": []
}
```

The total must be calculated server-side.

## Checkout

`POST /api/carts/{cart_id}/checkout`

Request:

```json
{
  "customer_name": "Demo Buyer",
  "customer_email": "buyer@example.com",
  "customer_phone": "9999999999",
  "shipping_address": {
    "line1": "Demo Address",
    "city": "Kanpur",
    "state": "Uttar Pradesh",
    "postal_code": "208001",
    "country": "IN"
  },
  "approved_total_paise": 589800
}
```

The backend must ignore the client amount for calculation and compare it against the freshly generated quote.

Response:

```json
{
  "success": true,
  "data": {
    "merchant_order_id": "order_abc123",
    "razorpay_order_id": "order_MNOP123456",
    "razorpay_key_id": "rzp_test_xxxxxx",
    "amount_paise": 589800,
    "currency": "INR",
    "customer_name": "Demo Buyer",
    "customer_email": "buyer@example.com",
    "customer_phone": "9999999999"
  }
}
```

## Payment Verification

`POST /api/payments/razorpay/verify`

Headers:
- `X-Session-ID: guest_session_123`

Request:

```json
{
  "merchant_order_id": "order_abc123",
  "razorpay_order_id": "order_MNOP123456",
  "razorpay_payment_id": "pay_QRST789012",
  "razorpay_signature": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "order_id": "order_abc123",
    "status": "CONFIRMED",
    "amount_paise": 589800,
    "currency": "INR",
    "paid_at": "2026-09-03T02:30:00Z",
    "confirmed_at": "2026-09-03T02:30:00Z"
  }
}
```

## Webhooks

`POST /api/webhooks/razorpay`

Headers:
- `X-Razorpay-Signature: <hmac-sha256-signature>`
- `X-Razorpay-Event-Id: <event-id>`

Request: Raw body bytes of Razorpay webhook event (`order.paid`, `payment.captured`, `payment.failed`).

Response:

```json
{
  "success": true,
  "data": {
    "received": true,
    "event": "payment.captured",
    "status": "processed"
  }
}
```

## Agent Chat

`POST /api/agent/chat`

```json
{
  "session_id": "guest_session_123",
  "message": "Build me a running kit under ₹8000",
  "cart_id": "cart_001"
}
```

Response contains:
- assistant message
- recommended products
- cart state if changed
- tool activity summary
- approval state if quote is ready

The model never directly returns an authoritative payment amount.

## Orders (Guest Shopper)

### List Guest Orders
`GET /api/orders`

Headers:
- `X-Session-ID: <session_id>`

Returns orders belonging to the requester's guest session.

### Get Guest Order Detail
`GET /api/orders/{order_id}`

Headers:
- `X-Session-ID: <session_id>` (or `Authorization: Bearer <admin_token>`)

Returns:
- `id`, `customer_name`, `customer_email`, `customer_phone`, `shipping_address`
- `items`: immutable line items snapshot
- `amount_paise`, `currency`
- `status`: fulfillment status (`CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`)
- `payment_status`: authoritative payment state (`PAID`, `PENDING_PAYMENT`, `FAILED`)
- `payment_details`: provider metadata
- `fulfillment`: timestamps, carrier, tracking number, cancellation info
- `created_at`, `updated_at`

## Admin Orders & Fulfillment

### List Admin Orders
`GET /api/admin/orders?q={query}&status={status}&limit={limit}&offset={offset}`

Headers:
- `Authorization: Bearer <admin_token>`

Returns:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "order_abc123",
        "customer_name": "Runner One",
        "customer_email": "runner@example.com",
        "customer_phone": "+919876543210",
        "amount_paise": 549900,
        "currency": "INR",
        "status": "CONFIRMED",
        "payment_status": "PAID",
        "items_count": 1,
        "razorpay_order_id": "order_xxx",
        "created_at": "2026-09-03T10:00:00Z"
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

### Get Admin Order Detail
`GET /api/admin/orders/{order_id}`

Headers:
- `Authorization: Bearer <admin_token>`

Returns full order response including immutable items snapshot, customer information, payment details, and fulfillment timestamps.

### Update Order Fulfillment Status
`POST /api/admin/orders/{order_id}/fulfillment`

Headers:
- `Authorization: Bearer <admin_token>`

Request:
```json
{
  "status": "PROCESSING | SHIPPED | DELIVERED | CANCELLED",
  "carrier": "RunCraft Express",
  "tracking_number": "BLR-98421",
  "cancellation_reason": "Optional for non-cancel, mandatory if CANCELLED"
}
```

State transitions are executed atomically with conditional SQL. Idempotent same-status requests safely return HTTP 200 without duplicate audit events or timestamp overwriting. Invalid transitions return HTTP 409 Conflict.

### Get Admin Order Audit Trail
`GET /api/admin/orders/{order_id}/audit`

Headers:
- `Authorization: Bearer <admin_token>`

Returns chronological list of authoritative audit events for this specific order (`payment_verified`, `order_confirmed`, `order_processing_started`, `order_shipped`, `order_delivered`, `order_cancelled`).


## MCP Tools

Expose equivalent structured tools:

```text
search_products
get_product
check_price
check_inventory
get_delivery_estimate
get_related_products
get_offers
create_cart
add_to_cart
remove_from_cart
get_cart
get_final_quote
create_checkout
get_order
get_order_status
```

MCP tools must reuse commerce services.
