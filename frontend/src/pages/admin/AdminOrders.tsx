import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Search, Eye } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Badge } from "../../components/ui/Badge";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";

export const AdminOrders: React.FC = () => {
  const { orders } = useMockCommerce();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredOrders = orders.filter((order) => {
    const matchesSearch =
      order.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Merchant Orders</h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Confirmed customer orders initiated via in-app shopping agent or external MCP buyer.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface rounded-2xl border border-border p-4 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search by order ID, customer name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="w-full sm:w-56">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Order Statuses</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="PAID">PAID</option>
            <option value="PENDING_PAYMENT">PENDING_PAYMENT</option>
          </Select>
        </div>

        <div className="text-xs text-text-muted sm:ml-auto">
          Showing {filteredOrders.length} of {orders.length} orders
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Order ID</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Date & Time</TableHead>
              <TableHead>Channel Source</TableHead>
              <TableHead>Amount (INR)</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredOrders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-12 text-text-secondary">
                  No orders found matching your criteria.
                </TableCell>
              </TableRow>
            ) : (
              filteredOrders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-mono text-xs font-bold text-text-primary">
                    {order.id}
                  </TableCell>
                  <TableCell>
                    <div className="font-semibold text-xs text-text-primary">{order.customer_name}</div>
                    <div className="text-[11px] text-text-secondary">{order.customer_email}</div>
                  </TableCell>
                  <TableCell className="text-xs text-text-secondary font-mono">
                    {new Date(order.created_at).toLocaleString("en-IN", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </TableCell>
                  <TableCell>
                    <span className="text-[11px] font-medium bg-surface-secondary text-text-dark px-2.5 py-0.5 rounded-full border border-border">
                      Storefront AI Agent
                    </span>
                  </TableCell>
                  <TableCell className="font-extrabold text-xs text-text-primary">
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
                  <TableCell className="text-right">
                    <Link
                      to={`/admin/orders/${order.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-accent hover:text-accent-dark transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View Details</span>
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default AdminOrders;
