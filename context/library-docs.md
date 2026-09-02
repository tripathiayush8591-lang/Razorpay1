# Library Docs — Agentic Commerce V2

Read this file before using a listed library.

## React + Vite

Use Vite for local frontend development and production builds.

Rules:
- Keep frontend independent from FastAPI.
- Use environment variable `VITE_API_BASE_URL`.
- Do not put secrets in Vite environment variables.

## React Router

Use route-level separation for:
- admin
- client
- assistant
- checkout
- orders

Protected admin pages should redirect unauthenticated users to `/admin/login`.

## TanStack Query

Use for:
- product catalog queries
- product details
- cart queries
- order queries
- admin orders
- analytics

After mutations, invalidate the smallest relevant query.

Do not use TanStack Query as a replacement for backend business logic.

## React Hook Form + Zod

Use for:
- admin SKU form
- policy form
- checkout customer details

Validation should exist in both frontend and backend. Frontend validation is UX; backend validation is authoritative.

## Tailwind CSS v4

Tokens live in `src/styles/globals.css` using `@theme`.

Do not create a `tailwind.config.ts` only to define project colors.

## shadcn/ui

Use for primitives:
- Button
- Input
- Select
- Dialog
- Dropdown
- Tabs
- Table
- Badge
- Card
- Toast
- Tooltip

Customize through project tokens, not random one-off colors.

## Lucide React

Use icons consistently. Avoid mixing icon libraries.

## Recharts

Use only for simple admin charts:
- revenue
- orders
- conversion
- channel split

Do not make analytics the main product story.

## FastAPI

Use:
- APIRouter
- Pydantic request/response models
- dependency injection
- HTTPException only at the API boundary
- service functions for business logic

Keep routes thin.

## SQLAlchemy 2.x

Use typed SQLAlchemy models and sessions.

Rules:
- Money is integer paise.
- Use transactions around cart/order/payment state transitions.
- Do not expose ORM objects directly to clients.

## Alembic

All schema changes go through migrations.

The demo database may be recreated from scratch, but schema history must remain reproducible.

## Google Gemini (LLM Provider)

Use `google-genai` Python SDK (model: `gemini-2.5-flash`).

Rules:
- Keep model calls behind `integrations/gemini.py`.
- Register tools using function calling syntax; all tools delegate to `services/agent_tools.py`.
- Never trust model output for authoritative prices, inventory, or cart totals.
- All actions execute against the live Phase 3 commerce layer.
- Must provide a seamless deterministic fallback (`services/agent_fallback.py`) when `GEMINI_API_KEY` is missing or failing, ensuring 100% demo reliability.
- Stop before payment: require explicit user approval via `ApprovalCard`.

## MCP

Expose MCP tools through a thin adapter.

Tools must delegate to the same commerce services used by REST.

Do not implement alternate pricing/cart/order logic inside MCP.

## Razorpay

Rules:
- Server creates Razorpay Orders.
- Amount is in paise.
- Secret remains server-side.
- Verify checkout signature server-side.
- Verify webhook signature.
- Treat verified payment state as authoritative.
- Make webhook processing idempotent.
