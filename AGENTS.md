# Agentic Commerce — AI Build Instructions

## Mission

Build the Agentic Commerce MVP described in `context/project-overview.md` and `context/architecture.md`.

The application is a hackathon demo. It must be visually polished, technically coherent, locally runnable, and capable of demonstrating both:
1. Human shopper → Merchant Storefront → In-app Agent → Commerce Layer → Razorpay → Order
2. External AI Buyer → MCP → Commerce Layer → Razorpay → Order

## Mandatory Reading Order

Before implementing any feature, read:
1. `context/project-overview.md`
2. `context/architecture.md`
3. `context/build-plan.md`
4. `context/ui-rules.md`
5. `context/ui-tokens.md`
6. `context/code-standards.md`

Read `context/library-docs.md` before using a third-party library.

## Non-negotiable Architecture Rules

- Frontend: React + Vite + TypeScript.
- Backend: FastAPI + Python.
- Database: local SQLite. Do not add Supabase or InsForge.
- Backend owns authoritative catalog, price, inventory, carts, quotes, orders, policies and payment state.
- Browser localStorage is only for non-authoritative client state such as UI preferences, guest cart cache, and demo session hints.
- Never put authoritative price, stock, quote totals, payment status, or merchant rules only in React/localStorage/LLM context.
- MCP is an adapter over commerce services. Business logic must remain in the commerce service layer.
- Razorpay secrets are server-side only.
- Payment requires explicit user approval.
- An order becomes confirmed only after verified payment.
- Webhook processing must be idempotent.
- Guest checkout is supported for the external AI journey.

## Build Discipline

- Build UI with realistic mock data first.
- Verify the page visually before wiring backend logic.
- Complete one feature end-to-end before starting the next.
- Keep scope limited to the current build-plan item.
- Prefer simple readable code over clever abstractions.
- Every feature must have a visible/testable acceptance criterion.
- Never silently invent backend behavior that is not documented.

## Demo Priority

The highest-priority demo path is:

Admin creates SKU
→ Client storefront sees SKU
→ Client asks in-app agent for a product
→ Agent searches real backend catalog
→ Agent adds product to backend cart
→ Final quote revalidates price/stock/policies
→ User explicitly approves
→ FastAPI creates Razorpay Test Mode order
→ React opens Razorpay Checkout
→ Backend verifies payment/webhook
→ Merchant order becomes CONFIRMED
→ Client sees order tracking.

Second priority:
External AI Buyer → MCP tools → same commerce APIs → same quote/payment/order flow.

## Do Not Build

Do not introduce:
- Supabase
- InsForge
- Next.js
- a second backend framework
- microservices
- Kubernetes
- Redis unless explicitly required later
- full ACP/UCP/AP2/UAP/x402 implementations
- real-money payment
- autonomous payment without approval
- multi-merchant negotiation
- production-grade multi-tenant infrastructure
