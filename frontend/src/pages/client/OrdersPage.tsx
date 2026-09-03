import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Package, Calendar, RefreshCw } from "lucide-react";
import { apiClient } from "../../lib/api/client";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import type { OrderStatus, PaymentStatus } from "../../types/domain";

export const OrdersPage: React.FC = () => {
  const { data: response, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["orders"],
    queryFn: () => apiClient.getOrders(),
  });

  const orders = response?.data || [];

  const getStatusBadge = (orderStatus: OrderStatus, paymentStatus?: PaymentStatus) => {
    switch (orderStatus) {
      case "DELIVERED":
        return <Badge variant="success">DELIVERED</Badge>;
      case "SHIPPED":
        return <Badge variant="neutral">SHIPPED</Badge>;
      case "PROCESSING":
        return <Badge variant="info">PROCESSING</Badge>;
      case "CONFIRMED":
        return <Badge variant="accent">CONFIRMED</Badge>;
      case "CANCELLED":
        return <Badge variant="error">CANCELLED</Badge>;
      default:
        return paymentStatus === "PAID" ? (
          <Badge variant="success">PAID</Badge>
        ) : (
          <Badge variant="warning">{orderStatus}</Badge>
        );
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary">Order History & Tracking</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Review your confirmed gear purchases, payment receipts, and delivery updates.
          </p>
        </div>
        <div>
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

      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-text-secondary">Loading your order history...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-md mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-surface-secondary flex items-center justify-center text-text-muted mx-auto border border-border">
            <Package className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-text-primary">No orders placed yet</h3>
          <p className="text-xs text-text-secondary">
            Once you approve an order and complete checkout, your confirmed purchase receipt will appear here.
          </p>
          <div className="pt-2">
            <Link to="/shop">
              <Button variant="primary" size="md">
                Start Shopping
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-surface rounded-2xl border border-border p-5 sm:p-6 shadow-xs hover:border-border-strong transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-text-primary">{order.id}</span>
                  {getStatusBadge(order.status, order.payment_status)}
                </div>

                <div className="flex items-center gap-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-text-muted" />
                    {new Date(order.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                  <span>•</span>
                  <span>Recipient: {order.customer_name}</span>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 pt-3 sm:pt-0 border-t sm:border-t-0 border-border">
                <div className="text-left sm:text-right">
                  <span className="text-[10px] text-text-muted uppercase block leading-none">Total</span>
                  <span className="text-base font-extrabold text-text-primary mt-1 block font-mono">
                    ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <Link to={`/orders/${order.id}`}>
                  <Button variant="outline" size="sm" icon={<ArrowRight className="w-3.5 h-3.5" />}>
                    Track Details
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OrdersPage;
