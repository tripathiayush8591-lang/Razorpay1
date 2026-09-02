# UI Rules — Agentic Commerce V2

## Design Direction

Modern AI-commerce product: clean, premium, minimal, high information density without looking like an enterprise ERP.

The client storefront should feel like a polished modern commerce site.
The admin should feel like a compact SaaS control center.
The assistant should feel native to the shopping experience rather than a generic chatbot.

## Typography

Use Inter throughout.

Hierarchy:
- Display: 48–64px, weight 600–700
- Page title: 28–36px, weight 600
- Section title: 18–22px, weight 600
- Body: 14–16px, weight 400–500
- Muted: 12–14px, weight 400

## Layout

- Max content width: 1440px.
- Desktop page padding: 32px.
- Section gap: 24–48px.
- Use responsive grids.
- Admin may use a sidebar because it is a control portal.
- Client storefront uses a top navigation/header.
- Avoid unnecessary full-screen panels.

## Cards

Default:
- white/surface background
- subtle border
- 14–16px radius
- restrained shadow
- 20–24px padding

Do not fill entire cards with strong accent colors.

## Buttons

Primary:
- accent background
- white text
- medium weight
- 8–10px radius

Secondary:
- white/surface
- border
- primary text

Destructive:
- error token

## Inputs

- white/surface
- 1px border
- 8px radius
- 10–12px horizontal padding
- visible focus ring

## Product Cards

Show:
- image
- product name
- category
- price
- inventory/availability when useful
- primary action

Do not overload product cards with technical metadata.

## Agent UI

Agent messages should be compact and readable.

Product recommendations should use cards inside the conversation.

When tools execute, show subtle status:
- Searching catalog
- Checking availability
- Building cart
- Rechecking final price

Do not expose raw JSON/tool payloads to the shopper.

## Approval UI

The approval card is a high-importance component.

Show:
- products
- quantities
- subtotal
- discount
- delivery
- total
- “Approve ₹X” CTA

Make it visually obvious that clicking approval authorizes payment.

## Admin

Admin navigation:
- Overview
- Catalog
- Orders
- Agent Policies
- Channels

Catalog table:
- SKU
- Product
- Price
- Stock
- Status
- Updated
- Actions

Use filters/search where helpful.

## Tables

- No zebra striping.
- Hover state is subtle.
- Headers are muted uppercase.
- Keep rows compact but readable.

## Empty States

Every empty section needs:
- short explanation
- optional icon
- logical CTA

## Responsive

Desktop-first because the hackathon demo is desktop, but do not break at tablet width.

## Accessibility

- Keyboard focus visible.
- Buttons must have meaningful labels.
- Images require alt text.
- Form labels must be associated with controls.
- Do not rely on color alone for status.
