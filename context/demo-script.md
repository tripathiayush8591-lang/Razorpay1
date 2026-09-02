# Hackathon Demo Script — Agentic Commerce

## Demo Setup

Seed:
- one merchant: RunStore
- 8–12 products
- realistic running/shopping categories
- cross-sell rule: shoes → socks
- max discount: 10%
- out-of-stock selling disabled
- purchase approval required

Use Razorpay Test Mode.

## Demo 1 — Merchant Admin

1. Open Admin Portal.
2. Show Catalog.
3. Add SKU:
   - SKU: RUN-BOTTLE-001
   - Name: RunFlow Insulated Bottle
   - Price: ₹499
   - Stock: 25
4. Save.
5. Switch to Client Portal.
6. Show the new product without changing frontend code.

Narrative:
“The merchant controls its catalog. The AI does not own product truth.”

## Demo 2 — In-App Agent

User:
“Build me a beginner running kit under ₹8,000.”

Agent:
- extracts budget/use case
- searches catalog
- recommends shoes
- recommends socks
- optionally suggests bottle

User:
“Remove the bottle and add the socks.”

Agent modifies backend cart.

Then show final quote:
- item prices
- delivery
- total
- explicit approval button

Narrative:
“The model can recommend and act, but the commerce layer rechecks what is actually available and what the merchant allows.”

Click:
`Approve ₹X`

Razorpay Test Checkout opens.

Complete test payment.

Show:
`Payment verified → Order confirmed`

## Demo 3 — External AI Buyer

Open External Buyer demo.

User:
“Find me beginner running shoes under ₹6,000.”

Show:
- MCP connection
- tool discovery
- structured product results

Select product.

External buyer calls:
- create_cart
- add_to_cart
- get_final_quote

Show approval.

Proceed to Razorpay.

After payment:
External buyer retrieves order status.

Narrative:
“The same merchant is now consumable by an AI outside its own storefront, without duplicating the merchant's commerce logic.”

## Judge Takeaway

End with these three points:

1. One catalog and commerce layer.
2. Multiple AI buying channels.
3. Merchant-controlled truth + explicit human payment approval.

## Do Not Spend Demo Time On

- database internals
- source code
- complicated authentication
- deployment infrastructure
- future ACP/UCP details

Focus on:
Catalog → AI discovery → authoritative quote → approval → Razorpay → confirmed order.
