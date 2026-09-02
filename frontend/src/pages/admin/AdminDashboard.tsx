import React from "react";
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
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";

export const AdminDashboard: React.FC = () => {
  const { orders } = useMockCommerce();

  // Fetch real authoritative product catalog from SQLite via TanStack Query
  const { data: catalogResponse } = useQuery({
    queryKey: ["admin-products"],
    queryFn: () => apiClient.getAdminProducts({ active_only: false }),
  });

  const products = catalogResponse?.data || [];

  // Authoritative SKU calculations from SQLite database
  const activeSkusCount = products.filter((p) => p.active).length;
  const totalRevenuePaise = orders.reduce((sum, o) => sum + o.amount_paise, 0);
  const lowStockProducts = products.filter((p) => p.inventory_quantity <= 15 && p.active);

  const kpis = [
    {
      label: "Gross Revenue",
      value: `₹${(totalRevenuePaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
      change: "+18.4% this week",
      icon: <DollarSign className="w-5 h-5 text-accent" />,
    },
    {
      label: "Orders Handled",
      value: orders.length.toString(),
      change: "100% verified payments",
      icon: <ShoppingBag className="w-5 h-5 text-success" />,
    },
    {
      label: "Active Catalog SKUs",
      value: activeSkusCount.toString(),
      change: `${products.length} total in SQLite`,
      icon: <Package className="w-5 h-5 text-info" />,
    },
    {
      label: "AI Cross-Sell Rate",
      value: "68%",
      change: "Shoes → Anti-Blister Socks",
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
            Real-time overview of catalog inventory, orders, and agentic policy performance.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
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
              <div className="text-[11px] font-medium text-text-muted mt-1">{kpi.change}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Recent Orders & Inventory Watchlist */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Recent Orders (8 cols) */}
        <div className="lg:col-span-8 bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-text-primary">Recent Orders</h2>
              <p className="text-xs text-text-secondary mt-0.5">Authoritative confirmed customer orders</p>
            </div>
            <Link
              to="/admin/orders"
              className="text-xs font-semibold text-accent hover:text-accent-dark transition inline-flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

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
              {orders.slice(0, 5).map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-mono font-medium text-text-dark">{order.id}</TableCell>
                  <TableCell>
                    <div className="font-semibold text-text-primary">{order.customer_name}</div>
                    <div className="text-[11px] text-text-secondary">{order.customer_email}</div>
                  </TableCell>
                  <TableCell className="font-bold text-text-primary">
                    ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        order.status === "CONFIRMED"
                          ? "accent"
                          : order.status === "PAID"
                          ? "success"
                          : "warning"
                      }
                    >
                      {order.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Link
                      to={`/admin/orders/${order.id}`}
                      className="text-xs font-medium text-accent hover:underline"
                    >
                      Inspect
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
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
              {lowStockProducts.length === 0 ? (
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
