# UI Registry — Agentic Commerce V2

Living registry. Update after each component is built.

## Rules

Before creating a component:
1. Search this registry for an equivalent.
2. Reuse the existing pattern.
3. If new, follow `ui-rules.md` and `ui-tokens.md`.
4. Add the component here after implementation.

## UI Primitives

| Component | Path | Pattern |
|---|---|---|
| Button | `src/components/ui/Button.tsx` | Accessible button with primary/secondary/outline/ghost/destructive variants and loading state |
| Badge | `src/components/ui/Badge.tsx` | Status pill with neutral/success/warning/error/accent/info tokens |
| Card | `src/components/ui/Card.tsx` | Surface card with subtle border, 16px radius, and subcomponents (Header, Title, Description, Content, Footer) |
| Input | `src/components/ui/Input.tsx` | Accessible input with label, helper, error message, and left/right icon slots |
| Table | `src/components/ui/Table.tsx` | Accessible table with muted uppercase headers, subtle hover, and compact row density |
| Select | `src/components/ui/Select.tsx` | Accessible dropdown select with label, helper, error message, and token focus ring |
| ImageUpload | `src/components/ui/ImageUpload.tsx` | Accessible drag-and-drop file picker with PNG/JPG/WebP validation, 5MB ceiling, instant preview, and replace/remove actions |

## Layout Components

| Component | Path | Pattern |
|---|---|---|
| AppShell | `src/components/layout/AppShell.tsx` | Top-level storefront shell with header, footer, cart drawer, and floating AI assistant trigger |
| AdminShell | `src/components/layout/AdminShell.tsx` | Control portal layout with 240px fixed desktop sidebar, mobile drawer, user badge, and storefront exit |
| StorefrontHeader | `src/components/layout/StorefrontHeader.tsx` | Top nav with branding, catalog links, search, cart counter, and subtle merchant portal switch |
| StorefrontFooter | `src/components/layout/StorefrontFooter.tsx` | Merchant footer with categories, architecture guarantee, and technology links |
| CartDrawer | `src/components/layout/CartDrawer.tsx` | Slide-over drawer with item quantity controls, quote summary, and checkout action |

## Storefront Components & Pages

| Component | Path | Pattern |
|---|---|---|
| Hero | `src/components/storefront/Hero.tsx` | Hero banner with value proposition, AI trigger, catalog CTA, and interactive AI kit preview card |
| FeaturedProducts | `src/components/storefront/FeaturedProducts.tsx` | 4-item showcase grid with live stock badge, INR price formatting, and instant add-to-cart |
| HowItWorks | `src/components/storefront/HowItWorks.tsx` | 3-step explanation of natural prompt -> authoritative quote -> explicit consent |
| TrustSection | `src/components/storefront/TrustSection.tsx` | 4 pillars of real-world trust (zero hallucination, human approval, Razorpay pipeline, MCP parity) |
| LandingPage | `src/components/storefront/LandingPage.tsx` | Marketing landing page assembling Hero, Featured, HowItWorks, and Trust sections |
| ProductCard | `src/components/storefront/ProductCard.tsx` | Reusable product card with image, category, stock badge, INR price, and instant add-to-cart |
| ProductGrid | `src/components/storefront/ProductGrid.tsx` | Responsive 3-column product grid with empty search fallback |
| ProductFilters | `src/components/storefront/ProductFilters.tsx` | Filter panel with category selector, budget slider, stock toggle, and reset action |
| ShopPage | `src/pages/client/ShopPage.tsx` | Complete catalog page with keyword search, sort selector, and sidebar filters |
| ProductDetailPage | `src/pages/client/ProductDetailPage.tsx` | Product showcase with specs table, quantity picker, and policy cross-sell pairing |

## Assistant Components

| Component | Path | Pattern |
|---|---|---|
| AssistantPanel | `src/components/assistant/AssistantPanel.tsx` | Live AI assistant wired to `POST /api/agent/chat` with TanStack Query, session/cart binding, and auto-scroll |
| ChatMessage | `src/components/assistant/ChatMessage.tsx` | Message bubble rendering text, tool activity, product recommendations, and approval cards |
| ProductRecommendation | `src/components/assistant/ProductRecommendation.tsx` | In-chat product card with live stock, image resolver, and TanStack Query cart mutation |
| ApprovalCard | `src/components/assistant/ApprovalCard.tsx` | Authoritative quote card displaying live subtotal/delivery/total with explicit approval CTA routing to `/checkout` |
| ToolActivity | `src/components/assistant/ToolActivity.tsx` | Status pill showing agent tool invocations (search, inventory, cart add, quote calculation) with details tooltip |

## Admin Components & Pages

| Component | Path | Pattern |
|---|---|---|
| AdminLogin | `src/pages/admin/AdminLogin.tsx` | SaaS mock login page with one-click demo credentials and storefront return link |
| AdminDashboard | `src/pages/admin/AdminDashboard.tsx` | 4 KPI cards, quick actions row, recent orders table snippet, and low-stock inventory watchlist |
| AdminCatalog | `src/pages/admin/AdminCatalog.tsx` | Filterable and searchable catalog table with status badges and SKU edit/delete actions |
| SkuForm | `src/components/admin/SkuForm.tsx` | Single reusable form for SKU creation (`/catalog/new`) and editing (`/catalog/:skuId/edit`) with live context sync |
| AdminOrders | `src/pages/admin/AdminOrders.tsx` | Filterable orders table with status badges, channel source, and inspection links |
| AdminOrderDetail | `src/pages/admin/AdminOrderDetail.tsx` | Detailed order view with customer info, line items, authoritative price breakdown, and visual audit trail timeline |
| AdminPolicies | `src/pages/admin/AdminPolicies.tsx` | Merchant selling policies editor (approval requirement, backorder rules, discount caps, delivery rules, cross-sells) |
| AdminChannels | `src/pages/admin/AdminChannels.tsx` | Multi-channel overview (Storefront + MCP Adapter) with expandable 10-tool registry inspector |

## Checkout / Orders

| Component | Path | Pattern |
|---|---|---|
| CartSummary | `src/components/checkout/CartSummary.tsx` | Interactive cart items table with free shipping progress bar and live quote breakdown |
| CartPage | `src/pages/client/CartPage.tsx` | Dedicated full-page cart experience with quote summary and checkout navigation |
| CheckoutForm | `src/components/checkout/CheckoutForm.tsx` | Contact/shipping inputs, demo autofill helper, and authoritative ApprovalCard CTA |
| CheckoutPage | `src/pages/client/CheckoutPage.tsx` | Assembled checkout review view with breadcrumbs and policy guardrails |
| OrderTimeline | `src/components/orders/OrderTimeline.tsx` | Multi-step visual order fulfillment and payment audit trail timeline |
| OrdersPage | `src/pages/client/OrdersPage.tsx` | Client order history list with status pills and tracking links |
| OrderDetailPage | `src/pages/client/OrderDetailPage.tsx` | Order confirmation view with fulfillment timeline, line items, and delivery address |
