import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  DollarSign,
  ShoppingBag,
  Package,
  TrendingUp,
  Plus,
  Sliders,
  Network,
  ExternalLink,
  ArrowRight,
  AlertTriangle,
  Bot,
  Cpu,
  Layers,
  RefreshCw,
  Clock,
  ArrowUpRight,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";

export const AdminDashboard: React.FC = () => {
  const [selectedDays, setSelectedDays] = useState<number | undefined>(30);

  // Authoritative Analytics Query from SQLite
  const {
    data: analyticsResponse,
    isLoading: isAnalyticsLoading,
    isError: isAnalyticsError,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ["admin-analytics", selectedDays],
    queryFn: () => apiClient.getAdminAnalytics({ days: selectedDays }),
  });

  // Authoritative Product Catalog Query
  const { data: catalogResponse, isLoading: isCatalogLoading } = useQuery({
    queryKey: ["admin-products"],
    queryFn: () => apiClient.getAdminProducts({ active_only: false }),
  });

  // Authoritative Recent Orders Query
  const {
    data: ordersResponse,
    isLoading: isOrdersLoading,
  } = useQuery({
    queryKey: ["admin-orders-recent"],
    queryFn: () => apiClient.getAdminOrders({ limit: 5 }),
  });

  const analytics = analyticsResponse?.data;
  const products = catalogResponse?.data || [];
  const recentOrders = ordersResponse?.data?.items || [];
  const lowStockProducts = products.filter((p) => p.inventory_quantity <= 15 && p.active);

  const kpis = [
    {
      label: "Gross Confirmed Revenue",
      value: analytics ? `₹${analytics.gross_revenue_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—",
      subtext: analytics ? `AOV: ₹${analytics.aov_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "Calculating...",
      icon: <DollarSign className="w-5 h-5 text-accent" />,
    },
    {
      label: "Confirmed Orders",
      value: analytics ? analytics.confirmed_orders_count.toString() : "—",
      subtext: analytics ? `${analytics.cart_to_order_conversion_rate}% cart conversion` : "Calculating...",
      icon: <ShoppingBag className="w-5 h-5 text-success" />,
    },
    {
      label: "Active Catalog SKUs",
      value: analytics ? analytics.active_skus_count.toString() : "—",
      subtext: `${products.length} total in SQLite`,
      icon: <Package className="w-5 h-5 text-info" />,
    },
    {
      label: "AI Cross-Sell Rate",
      value: analytics ? `${analytics.cross_sell_acceptance_rate}%` : "—",
      subtext: analytics ? `${analytics.cross_sell_accepted_orders_count} of ${analytics.cross_sell_eligible_orders_count} eligible baskets` : "Calculating...",
      icon: <TrendingUp className="w-5 h-5 text-warning" />,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Merchant Control Center</h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Real-time authoritative analytics for catalog inventory, customer orders, and AI buying channels.
          </p>
        </div>

        {/* Time Window Tabs & Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Time Filter Pill Selector */}
          <div className="flex items-center bg-surface-secondary p-1 rounded-xl border border-border mr-1">
            <button
              onClick={() => setSelectedDays(7)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
                selectedDays === 7 ? "bg-surface text-accent shadow-xs" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setSelectedDays(30)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
                selectedDays === 30 ? "bg-surface text-accent shadow-xs" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setSelectedDays(undefined)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
                selectedDays === undefined ? "bg-surface text-accent shadow-xs" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              All Time
            </button>
          </div>

          <Link to="/admin/catalog/new">
            <Button variant="primary" size="sm" icon={<Plus className="w-3.5 h-3.5" />}>
              Add SKU
            </Button>
          </Link>
          <Link to="/admin/policies">
            <Button variant="outline" size="sm" icon={<Sliders className="w-3.5 h-3.5" />}>
              Policies
            </Button>
          </Link>
          <Link to="/admin/channels">
            <Button variant="outline" size="sm" icon={<Network className="w-3.5 h-3.5" />}>
              Channels
            </Button>
          </Link>
          <Link to="/" target="_blank">
            <Button variant="ghost" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
              Storefront
            </Button>
          </Link>
        </div>
      </div>

      {/* Error Alert */}
      {isAnalyticsError && (
        <div className="p-4 rounded-2xl bg-error-light border border-error/20 flex items-center justify-between text-error-foreground">
          <div className="flex items-center gap-2 text-xs font-medium">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Failed to load live analytics telemetry from backend.</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => refetchAnalytics()} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Retry
          </Button>
        </div>
      )}

      {/* Topline KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isAnalyticsLoading || isCatalogLoading ? (
          [1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-surface rounded-2xl border border-border p-5 h-28 animate-pulse flex flex-col justify-between">
              <div className="h-4 w-24 bg-surface-secondary rounded" />
              <div className="h-7 w-32 bg-surface-secondary rounded" />
            </div>
          ))
        ) : (
          kpis.map((kpi, idx) => (
            <div
              key={idx}
              className="bg-surface rounded-2xl border border-border p-5 shadow-xs flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-text-secondary">{kpi.label}</span>
                <div className="w-9 h-9 rounded-xl bg-surface-secondary flex items-center justify-center border border-border">
                  {kpi.icon}
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-extrabold text-text-primary">{kpi.value}</div>
                <div className="text-[11px] font-medium text-text-muted mt-1">{kpi.subtext}</div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Conversion Funnel & Channel Attribution Row */}
      {analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Carts & Conversion Funnel (6 cols) */}
          <div className="lg:col-span-6 bg-surface rounded-2xl border border-border p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-accent" />
                  <h2 className="text-sm font-bold text-text-primary">Commerce Conversion Funnel</h2>
                </div>
                <span className="text-xs font-semibold text-success bg-success-light px-2.5 py-0.5 rounded-full border border-success/20">
                  {analytics.cart_to_order_conversion_rate}% Conversion
                </span>
              </div>

              <div className="mt-5 space-y-4">
                {/* Funnel Steps */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-text-secondary">Carts Created</span>
                    <span className="text-text-primary font-bold">{analytics.total_carts_created}</span>
                  </div>
                  <div className="w-full bg-surface-secondary rounded-full h-2 overflow-hidden border border-border">
                    <div className="bg-text-secondary h-full rounded-full" style={{ width: "100%" }} />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-text-secondary">Carts With Items Added</span>
                    <span className="text-text-primary font-bold">
                      {analytics.carts_with_items_count}{" "}
                      <span className="text-[10px] text-text-muted">
                        ({analytics.total_carts_created > 0 ? Math.round((analytics.carts_with_items_count / analytics.total_carts_created) * 100) : 0}%)
                      </span>
                    </span>
                  </div>
                  <div className="w-full bg-surface-secondary rounded-full h-2 overflow-hidden border border-border">
                    <div
                      className="bg-accent h-full rounded-full"
                      style={{
                        width: `${analytics.total_carts_created > 0 ? Math.min(100, Math.round((analytics.carts_with_items_count / analytics.total_carts_created) * 100)) : 0}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-text-secondary">Confirmed & Paid Orders</span>
                    <span className="text-text-primary font-bold">
                      {analytics.confirmed_orders_count}{" "}
                      <span className="text-[10px] text-success font-semibold">
                        ({analytics.carts_with_items_count > 0 ? Math.round((analytics.confirmed_orders_count / analytics.carts_with_items_count) * 100) : 0}%)
                      </span>
                    </span>
                  </div>
                  <div className="w-full bg-surface-secondary rounded-full h-2 overflow-hidden border border-border">
                    <div
                      className="bg-success h-full rounded-full"
                      style={{
                        width: `${analytics.carts_with_items_count > 0 ? Math.min(100, Math.round((analytics.confirmed_orders_count / analytics.carts_with_items_count) * 100)) : 0}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-border flex items-center justify-between text-xs text-text-muted">
              <span>Abandoned Carts: <strong className="text-warning">{analytics.abandoned_carts_count}</strong></span>
              <span>Overall Rate: <strong className="text-text-primary">{analytics.overall_conversion_rate}%</strong></span>
            </div>
          </div>

          {/* AI Channels & Attribution (6 cols) */}
          <div className="lg:col-span-6 bg-surface rounded-2xl border border-border p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-info" />
                  <h2 className="text-sm font-bold text-text-primary">AI Buying Channels & Telemetry</h2>
                </div>
                <span className="text-xs font-semibold text-info bg-info-light px-2.5 py-0.5 rounded-full border border-info/20">
                  {analytics.total_ai_sessions_count} AI Sessions
                </span>
              </div>

              {/* AI Interaction Split */}
              <div className="grid grid-cols-2 gap-3 mt-4">
                <div className="p-3 rounded-xl bg-surface-secondary border border-border">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary">
                    <Bot className="w-3.5 h-3.5 text-accent" />
                    <span>In-App Assistant</span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-xl font-extrabold text-text-primary">{analytics.in_app_agent_turns_count}</span>
                    <span className="text-[11px] text-text-muted">chat turns</span>
                  </div>
                  <div className="text-[10px] text-text-muted mt-0.5">{analytics.in_app_agent_sessions_count} shopper sessions</div>
                </div>

                <div className="p-3 rounded-xl bg-surface-secondary border border-border">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary">
                    <Cpu className="w-3.5 h-3.5 text-success" />
                    <span>External AI (MCP)</span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-xl font-extrabold text-text-primary">{analytics.external_ai_tool_calls_count}</span>
                    <span className="text-[11px] text-text-muted">tool calls</span>
                  </div>
                  <div className="text-[10px] text-text-muted mt-0.5">{analytics.external_ai_sessions_count} buyer sessions</div>
                </div>
              </div>

              {/* Channel Revenue Attribution */}
              <div className="mt-4 space-y-2">
                <span className="text-xs font-semibold text-text-secondary">Channel Revenue Share</span>
                <div className="space-y-1.5">
                  {analytics.channel_breakdown.map((ch) => (
                    <div key={ch.channel} className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-surface-secondary">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          ch.channel === "in_app_agent" ? "bg-accent" : ch.channel === "external_ai" ? "bg-success" : "bg-text-muted"
                        }`} />
                        <span className="font-medium text-text-primary">{ch.channel_label}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-text-primary">
                          ₹{ch.revenue_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                        <span className="text-xs text-text-muted w-10 text-right">{ch.share_percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Policy cross-sell detail footnote */}
            {analytics.cross_sell_rules_summary.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-text-muted">
                <span>Top Cross-Sell Pairing:</span>
                <span className="font-medium text-accent">
                  {analytics.cross_sell_rules_summary[0].trigger_category} → {analytics.cross_sell_rules_summary[0].recommend_category} (
                  {analytics.cross_sell_rules_summary[0].matches_count} orders)
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Two Column Layout: Recent Orders & Inventory Watchlist */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Recent Orders (8 cols) */}
        <div className="lg:col-span-8 bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-text-primary">Recent Orders</h2>
              <p className="text-xs text-text-secondary mt-0.5">Authoritative confirmed customer orders from SQLite</p>
            </div>
            <Link
              to="/admin/orders"
              className="text-xs font-semibold text-accent hover:text-accent-dark transition inline-flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {isOrdersLoading ? (
            <div className="p-8 text-center text-xs text-text-muted flex items-center justify-center gap-2">
              <Clock className="w-4 h-4 animate-spin text-accent" />
              <span>Loading recent orders...</span>
            </div>
          ) : recentOrders.length === 0 ? (
            <div className="p-10 text-center">
              <p className="text-xs text-text-muted">No confirmed orders recorded yet.</p>
              <p className="text-[11px] text-text-muted mt-1">Complete a checkout in the storefront or external buyer to see live orders.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentOrders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-mono font-medium text-text-dark text-xs">{order.id}</TableCell>
                    <TableCell>
                      <div className="font-semibold text-text-primary text-xs">{order.customer_name}</div>
                      <div className="text-[11px] text-text-secondary">{order.customer_email}</div>
                    </TableCell>
                    <TableCell className="font-bold text-text-primary text-xs">
                      ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          order.status === "CONFIRMED"
                            ? "accent"
                            : order.status === "DELIVERED"
                            ? "success"
                            : order.status === "SHIPPED"
                            ? "info"
                            : order.status === "PROCESSING"
                            ? "warning"
                            : "neutral"
                        }
                      >
                        {order.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/admin/orders/${order.id}`}
                        className="text-xs font-medium text-accent hover:underline inline-flex items-center gap-0.5"
                      >
                        <span>Inspect</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        {/* Low Stock Inventory Watchlist (4 cols) */}
        <div className="lg:col-span-4 bg-surface rounded-2xl border border-border shadow-xs p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-warning" />
                <h2 className="text-sm font-bold text-text-primary">Inventory Watchlist</h2>
              </div>
              <span className="text-[10px] font-semibold text-warning bg-warning-light px-2 py-0.5 rounded-full border border-warning/20">
                {lowStockProducts.length} Items
              </span>
            </div>

            <div className="space-y-3">
              {isCatalogLoading ? (
                <div className="py-6 text-center text-xs text-text-muted animate-pulse">Loading stock levels...</div>
              ) : lowStockProducts.length === 0 ? (
                <p className="text-xs text-text-muted py-4 text-center">All inventory levels are healthy.</p>
              ) : (
                lowStockProducts.map((p) => (
                  <div
                    key={p.id}
                    className="p-3 rounded-xl bg-surface-secondary border border-border flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-text-primary truncate">{p.name}</p>
                      <p className="text-[10px] font-mono text-text-muted mt-0.5">{p.sku}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-bold text-warning block">
                        {p.inventory_quantity} left
                      </span>
                      <Link
                        to={`/admin/catalog/${p.id}/edit`}
                        className="text-[10px] text-accent hover:underline"
                      >
                        Restock
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border">
            <Link to="/admin/catalog">
              <Button variant="outline" size="sm" className="w-full text-xs">
                Manage Full Inventory
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;

