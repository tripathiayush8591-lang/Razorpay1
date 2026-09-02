# Project Overview — Agentic Commerce MVP V2

## Product

Agentic Commerce is an AI-native commerce platform that lets a merchant expose its catalog and commerce capabilities once, then sell through:
1. a merchant website with an embedded shopping agent
2. an external AI buyer connected through MCP.

The PRD explicitly defines the common commerce layer as the source of truth for product discovery, price, inventory, merchant policies, cart, final quote, checkout and orders.

## Core Principle

> Agents decide what to do. The commerce layer decides what is true and what is allowed.

Price, stock, cart totals, merchant rules and payment status must never live only inside an LLM prompt.

## Personas

### Admin / Merchant

The admin operates the merchant side:
- Add and edit SKUs.
- Set price and inventory.
- Manage product metadata.
- Configure agent selling policies.
- View orders.
- View simple commerce analytics.
- Inspect enabled channels.

### Client / Shopper

The client uses the merchant storefront:
- Browse products.
- Search/filter products.
- Chat with the in-app shopping agent.
- Receive product recommendations.
- Add/remove items through the agent.
- Review authoritative final quote.
- Explicitly approve purchase.
- Complete Razorpay Test Mode payment.
- Track orders.

### External AI Buyer

A separate demo client that:
- Connects to the merchant MCP server.
- Discovers available commerce tools.
- Searches products.
- Creates/manages a guest cart.
- Gets an authoritative quote.
- Requests explicit purchase approval.
- Starts merchant checkout.
- Retrieves the resulting order.

## Required Journeys

### Journey A — Human + Merchant Agent

Example:
“Build me a beginner running kit under ₹8,000.”

Expected flow:
1. Agent extracts constraints.
2. Agent calls commerce tools.
3. Commerce layer searches actual catalog and inventory.
4. Agent recommends products.
5. Shopper asks to add/remove/replace items.
6. Backend owns the cart.
7. `get_final_quote()` revalidates price, inventory, promotions, delivery and policies.
8. UI shows an explicit approval step.
9. No payment action happens before approval.
10. FastAPI creates Razorpay Test Mode order.
11. React launches Razorpay Checkout.
12. Backend verifies the checkout signature.
13. Webhook is verified and handled idempotently.
14. Merchant order moves from PENDING_PAYMENT → PAID → CONFIRMED.
15. Client can retrieve order status.

### Journey B — External AI Buyer

Example:
“Find beginner running shoes under ₹6,000.”

Expected flow:
1. External buyer connects to MCP.
2. It discovers `search_products`.
3. Merchant returns structured product information.
4. External buyer creates a guest cart.
5. Merchant owns the cart.
6. External buyer requests final quote.
7. User approves purchase.
8. Merchant backend creates Razorpay transaction.
9. Checkout is completed.
10. Payment is verified.
11. External buyer retrieves the order.

Guest checkout does not require a merchant account.

## Admin Portal

Routes:
- `/admin/login`
- `/admin/dashboard`
- `/admin/catalog`
- `/admin/catalog/new`
- `/admin/catalog/:skuId/edit`
- `/admin/orders`
- `/admin/orders/:orderId`
- `/admin/policies`
- `/admin/channels`

The admin must be able to add a SKU and immediately see it in the client storefront.

## Client Portal

Routes:
- `/`
- `/shop`
- `/product/:productId`
- `/assistant`
- `/cart`
- `/checkout`
- `/orders`
- `/orders/:orderId`

The client portal is a modern storefront, not a generic dashboard.

## SKU Minimum Fields

- SKU code
- Product name
- Category
- Short description
- Full description
- Price in INR
- Inventory quantity
- Image URL
- Active/inactive
- Tags
- Optional attributes/specifications

## Merchant Policies

MVP policies:
- Maximum discount percentage
- Allow/disallow selling out-of-stock items
- Cross-sell mappings, e.g. shoes → socks
- Require explicit purchase approval
- Optional delivery rules

Policies are configured by admin but enforced by backend services.

## Out of Scope

- Real money payments
- Autonomous payment without approval
- Full ACP/UCP integration
- ChatGPT/Gemini/Claude production distribution
- Multi-merchant shopping
- Agent-to-agent negotiation
- Returns/refunds workflow
- Subscriptions
- Loyalty
- Production identity infrastructure
- Mobile app
- Complex fulfillment integrations

## Success Criteria

- Admin can add a SKU without editing code.
- Newly added SKU appears in client catalog.
- In-app agent uses backend catalog rather than hardcoded product knowledge.
- External buyer uses MCP and reaches the same commerce APIs.
- Both channels return the same authoritative price and inventory.
- Quote is recalculated before approval.
- No payment starts before explicit approval.
- Razorpay Test Mode checkout works.
- Invalid payment cannot confirm an order.
- Payment retry does not create duplicate merchant orders.
- Critical actions are auditable.
- The demo is easy to run locally.
