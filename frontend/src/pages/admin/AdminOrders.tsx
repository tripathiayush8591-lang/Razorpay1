import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Eye, RefreshCw, Package } from "lucide-react";
import { apiClient } from "../../lib/api/client";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";
import type { OrderStatus, PaymentStatus } from "../../types/domain";

export const AdminOrders: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: response, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["admin", "orders", { q: searchQuery, status: statusFilter }],
    queryFn: () =>
      apiClient.getAdminOrders({
        q: searchQuery.trim() || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      }),
  });

  const orders = response?.data?.items || [];
  const total = response?.data?.total || 0;

  const getPaymentBadge = (status: PaymentStatus) => {
    switch (status) {
      case "PAID":
        return <Badge variant="success">PAID</Badge>;
      case "FAILED":
        return <Badge variant="error">FAILED</Badge>;
      default:
        return <Badge variant="warning">PENDING</Badge>;
    }
  };

  const getFulfillmentBadge = (status: OrderStatus) => {
    switch (status) {
      case "CONFIRMED":
        return <Badge variant="accent">CONFIRMED</Badge>;
      case "PROCESSING":
        return <Badge variant="info">PROCESSING</Badge>;
      case "SHIPPED":
        return <Badge variant="neutral">SHIPPED</Badge>;
      case "DELIVERED":
        return <Badge variant="success">DELIVERED</Badge>;
      case "CANCELLED":
        return <Badge variant="error">CANCELLED</Badge>;
      default:
        return <Badge variant="warning">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Merchant Orders</h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Authoritative customer purchases, payment confirmations, and warehouse fulfillment workflows.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface rounded-2xl border border-border p-4 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search by order ID, customer name, email..."
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
            <option value="all">All Fulfillment Statuses</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="PROCESSING">PROCESSING</option>
            <option value="SHIPPED">SHIPPED</option>
            <option value="DELIVERED">DELIVERED</option>
            <option value="CANCELLED">CANCELLED</option>
            <option value="PENDING_PAYMENT">PENDING_PAYMENT</option>
          </Select>
        </div>

        <div className="text-xs text-text-muted sm:ml-auto">
          Showing {orders.length} of {total} orders
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-7 h-7 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-text-secondary">Loading merchant orders...</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Date & Time</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Amount (INR)</TableHead>
                <TableHead>Payment</TableHead>
                <TableHead>Fulfillment</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-text-secondary">
                    <div className="max-w-xs mx-auto space-y-2">
                      <Package className="w-8 h-8 text-text-muted mx-auto" />
                      <p className="font-semibold text-xs text-text-primary">No orders found</p>
                      <p className="text-[11px] text-text-secondary">
                        Try adjusting your search query or status filter.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((order) => (
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
                    <TableCell className="text-xs text-text-secondary">
                      {order.items_count} item{order.items_count !== 1 ? "s" : ""}
                    </TableCell>
                    <TableCell className="font-extrabold text-xs text-text-primary">
                      ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      {getPaymentBadge(order.payment_status)}
                    </TableCell>
                    <TableCell>
                      {getFulfillmentBadge(order.status)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link
                        to={`/admin/orders/${order.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-accent hover:text-accent-dark transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Manage</span>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default AdminOrders;
