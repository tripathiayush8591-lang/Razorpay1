import React, { useState } from "react";
import {
  Globe,
  Bot,
  ChevronDown,
  ChevronUp,
  Terminal,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Link } from "react-router-dom";

export const AdminChannels: React.FC = () => {
  const [toolsExpanded, setToolsExpanded] = useState(true);

  const mcpTools = [
    {
      name: "search_products",
      description: "Search authoritative SQLite catalog by keyword, category, and price range.",
      input: "{ query: string, category?: string, max_price_paise?: number }",
    },
    {
      name: "get_product",
      description: "Fetch comprehensive SKU specifications, size/fit attributes, and tags.",
      input: "{ product_id: string }",
    },
    {
      name: "check_inventory",
      description: "Validate real-time stock levels in warehouse before adding to cart.",
      input: "{ product_id: string, requested_quantity: number }",
    },
    {
      name: "get_delivery_estimate",
      description: "Compute shipping fees and delivery estimates based on merchant rules and postal code.",
      input: "{ postal_code: string, cart_subtotal_paise?: number }",
    },
    {
      name: "get_offers",
      description: "Retrieve merchant promotional policies, free delivery thresholds, and discount caps.",
      input: "{}",
    },
    {
      name: "create_cart",
      description: "Initialize an authoritative server-owned cart for guest or registered buyer.",
      input: "{ session_id?: string }",
    },
    {
      name: "add_to_cart",
      description: "Add validated SKU to backend cart with price snapshot.",
      input: "{ cart_id: string, product_id: string, quantity: number }",
    },
    {
      name: "get_cart",
      description: "Retrieve cart items, quantities, and current line amounts.",
      input: "{ cart_id: string }",
    },
    {
      name: "get_final_quote",
      description: "Re-evaluate authoritative price, delivery threshold, discounts, and inventory.",
      input: "{ cart_id: string }",
    },
    {
      name: "create_checkout",
      description: "Create merchant order and initiate Razorpay Test Mode transaction.",
      input: "{ cart_id: string, customer_info: object }",
    },
    {
      name: "get_order",
      description: "Retrieve confirmed merchant order details and shipping record.",
      input: "{ order_id: string }",
    },
    {
      name: "get_order_status",
      description: "Poll real-time payment status and fulfillment progress.",
      input: "{ order_id: string }",
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Connected Commerce Channels</h1>
        <p className="text-xs text-text-secondary mt-0.5">
          Inspect external AI buyer protocol integrations and customer storefront endpoints.
        </p>
      </div>

      {/* Architecture Parity Callout */}
      <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-accent-light text-accent-dark flex items-center justify-center shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-text-primary">Universal Commerce Service Boundary</h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            Both the in-app storefront agent and the external AI buyer reach the exact same FastAPI commerce service layer. 
            No separate pricing or custom rules are defined inside the MCP adapter.
          </p>
        </div>
      </div>

      {/* Channel Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Channel 1: Customer Storefront */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center text-accent-foreground">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-text-primary">Customer Web Storefront</h3>
                  <p className="text-[10px] text-text-secondary">Human shopper + in-app assistant</p>
                </div>
              </div>
              <Badge variant="success">Active</Badge>
            </div>

            <div className="mt-4 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Protocol:</span>
                <span className="font-mono text-text-primary">React 19 / REST API</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Live Catalog Sync:</span>
                <span className="text-success font-semibold">Enabled (10 SKUs)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Payment Mode:</span>
                <span className="text-text-primary font-mono">Razorpay Checkout Standard</span>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <Link to="/" target="_blank">
              <Button variant="outline" size="sm" className="w-full text-xs" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                Open Customer Storefront
              </Button>
            </Link>
          </div>
        </div>

        {/* Channel 2: External AI Buyer via MCP */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-info-light text-info-foreground flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-text-primary">External AI Buyer (MCP)</h3>
                  <p className="text-[10px] text-text-secondary">Model Context Protocol Adapter</p>
                </div>
              </div>
              <Badge variant="accent">Ready</Badge>
            </div>

            <div className="mt-4 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Endpoint URI:</span>
                <span className="font-mono text-text-primary">/mcp</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Transport:</span>
                <span className="font-mono text-text-primary">Streamable HTTP (/mcp) + stdio</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-text-secondary">Exposed Tools:</span>
                <span className="text-accent font-semibold">{mcpTools.length} Commerce Tools</span>
              </div>
            </div>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row gap-2">
            <Link to="/external-buyer" className="flex-1">
              <Button variant="outline" size="sm" className="w-full text-xs" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                Launch Buyer Demo
              </Button>
            </Link>
            <Button
              variant="secondary"
              size="sm"
              className="flex-1 text-xs"
              onClick={() => setToolsExpanded(!toolsExpanded)}
              icon={toolsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            >
              {toolsExpanded ? "Hide Tools" : "Inspect Tools"}
            </Button>
          </div>
        </div>
      </div>

      {/* Exposed Tools Accordion */}
      {toolsExpanded && (
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-accent" />
              <h2 className="text-sm font-bold text-text-primary">
                Model Context Protocol (MCP) — Exposed Tool Registry
              </h2>
            </div>
            <span className="text-[11px] text-text-muted font-mono">{mcpTools.length} Endpoints</span>
          </div>

          <div className="divide-y divide-border">
            {mcpTools.map((tool) => (
              <div key={tool.name} className="py-3.5 first:pt-0 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-accent">
                    {tool.name}()
                  </span>
                  <span className="text-[10px] font-medium text-success bg-success-light px-2 py-0.2 rounded-full border border-success/20">
                    Validated
                  </span>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">{tool.description}</p>
                <div className="pt-1">
                  <code className="text-[11px] font-mono text-text-dark bg-surface-secondary px-2 py-0.5 rounded border border-border">
                    {tool.input}
                  </code>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminChannels;
