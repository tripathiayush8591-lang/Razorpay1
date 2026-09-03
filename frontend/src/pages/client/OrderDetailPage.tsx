import React from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  ArrowLeft,
  MapPin,
  User,
  Sparkles,
  ShoppingBag,
  AlertCircle,
  Truck,
  XCircle,
  RefreshCw,
  Clock,
} from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import OrderTimeline from "../../components/orders/OrderTimeline";
import { apiClient } from "../../lib/api/client";
import type { OrderStatus, PaymentStatus } from "../../types/domain";

export const OrderDetailPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const { setIsAssistantOpen } = useMockCommerce();

  // Query backend authoritative order
  const {
    data: backendOrderResponse,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: ["order", orderId],
    queryFn: async () => {
      if (!orderId) return null;
      return await apiClient.getOrder(orderId);
    },
    enabled: !!orderId,
    refetchInterval: (query) => {
      const ord = query.state.data?.data;
      if (ord && (ord.status === "PENDING_PAYMENT" || ord.payment_status === "PENDING_PAYMENT")) {
        return 3000;
      }
      return false;
    },
  });

  const order = backendOrderResponse?.data;

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-text-secondary font-medium">Loading verified order details...</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-md mx-auto space-y-4 my-8">
        <AlertCircle className="w-10 h-10 text-error mx-auto" />
        <h2 className="text-base font-bold text-text-primary">Order Not Found or Restricted</h2>
        <p className="text-xs text-text-secondary">
          This order does not belong to your active guest session or does not exist.
        </p>
        <div className="pt-2">
          <Link to="/orders">
            <Button variant="outline" size="sm">
              Back to My Orders
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const items = order.items || [];
  const isCancelled = order.status === "CANCELLED";

  const getPaymentBadge = (status?: PaymentStatus) => {
    switch (status) {
      case "PAID":
        return <Badge variant="success">PAID</Badge>;
      case "FAILED":
        return <Badge variant="error">PAYMENT FAILED</Badge>;
      default:
        return <Badge variant="warning">PENDING PAYMENT</Badge>;
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
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/orders"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-text-primary transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Order History</span>
        </Link>
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
          <span className="text-xs font-mono text-text-muted">Order: {order.id}</span>
        </div>
      </div>

      {/* Confirmation / Status Banner */}
      {isCancelled ? (
        <div className="bg-error/10 border border-error/30 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-xs">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-error text-surface flex items-center justify-center shrink-0 shadow-sm">
              <XCircle className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-extrabold text-text-primary">
                  Order Cancelled
                </h1>
                {getFulfillmentBadge(order.status)}
              </div>
              <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                Fulfillment for this order was cancelled by the merchant.
                {order.cancellation_reason && (
                  <span className="block font-medium text-text-primary mt-1">
                    Reason: {order.cancellation_reason}
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="sm:text-right shrink-0">
            {getPaymentBadge(order.payment_status)}
          </div>
        </div>
      ) : order.status === "PENDING_PAYMENT" || order.payment_status === "PENDING_PAYMENT" ? (
        <div className="bg-warning-light border border-warning/30 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-xs animate-in fade-in duration-200">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-warning text-surface flex items-center justify-center shrink-0 shadow-sm">
              <Clock className="w-7 h-7 animate-pulse" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-extrabold text-text-primary">
                  Payment Awaiting Confirmation
                </h1>
                <Badge variant="warning">AWAITING WEBHOOK</Badge>
              </div>
              <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                Your order has been recorded and is awaiting verified payment signature or webhook confirmation from Razorpay.
                This page polls automatically every 3 seconds.
              </p>
              <div className="pt-2 flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                  disabled={isFetching}
                  icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />}
                >
                  Check Status Now
                </Button>
                <span className="text-[11px] text-text-muted">Auto-polling active</span>
              </div>
            </div>
          </div>
          <div className="sm:text-right shrink-0">
            {getPaymentBadge(order.payment_status)}
          </div>
        </div>
      ) : (
        <div className="bg-success-light border border-success/30 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-xs">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-success text-surface flex items-center justify-center shrink-0 shadow-sm">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-extrabold text-text-primary">
                  {order.status === "DELIVERED"
                    ? "Package Delivered!"
                    : order.status === "SHIPPED"
                    ? "Order Shipped & In Transit!"
                    : order.status === "PROCESSING"
                    ? "Order Being Prepared!"
                    : "Order Confirmed!"}
                </h1>
                {getFulfillmentBadge(order.status)}
              </div>
              <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                Thank you, <strong className="text-text-primary">{order.customer_name}</strong>. Your test payment was verified server-side and your order is managed authoritatively.
              </p>
              {order.carrier && (
                <div className="flex items-center gap-2 pt-1 text-xs text-text-primary font-medium">
                  <Truck className="w-4 h-4 text-accent" />
                  <span>Courier: {order.carrier}</span>
                  {order.tracking_number && (
                    <span className="font-mono bg-surface px-2 py-0.5 rounded border border-border">
                      {order.tracking_number}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="sm:text-right shrink-0 space-y-1">
            <div className="flex items-center justify-end gap-1.5">
              {getPaymentBadge(order.payment_status)}
            </div>
            <span className="font-mono text-[11px] text-text-muted bg-surface/80 px-2 py-0.5 rounded border border-border inline-block">
              {order.razorpay_order_id || "Razorpay Test"}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Line Items & Customer Details (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Purchased Items Card (Immutable Snapshot) */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Purchased Equipment
              </h2>
              <span className="text-[10px] text-text-muted font-mono bg-surface-secondary px-2 py-0.5 rounded-full border border-border">
                Immutable Snapshot
              </span>
            </div>

            <div className="divide-y divide-border">
              {items.map((item, idx) => (
                <div key={idx} className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-12 h-12 rounded-xl bg-surface-tertiary border border-border flex items-center justify-center text-text-muted shrink-0">
                      <ShoppingBag className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-text-primary truncate">{item.name}</p>
                      <p className="text-[10px] font-mono text-text-muted">
                        SKU: {item.sku} • Qty: {item.quantity}
                      </p>
                    </div>
                  </div>

                  <span className="text-xs font-extrabold text-text-primary shrink-0 font-mono">
                    ₹{(item.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
            </div>

            {/* Authoritative Total */}
            <div className="pt-4 border-t border-border flex justify-between items-baseline">
              <span className="text-xs font-bold text-text-secondary">Authoritative Total Paid</span>
              <span className="text-xl font-black text-accent font-mono">
                ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Delivery & Contact Card */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-2">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <User className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Contact</h3>
              </div>
              <div className="space-y-0.5 text-xs">
                <p className="font-semibold text-text-primary">{order.customer_name}</p>
                <p className="text-text-secondary">{order.customer_email}</p>
                <p className="text-text-secondary font-mono">{order.customer_phone}</p>
              </div>
            </div>

            <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-2">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <MapPin className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Destination</h3>
              </div>
              <div className="space-y-0.5 text-xs text-text-secondary">
                <p className="font-medium text-text-primary">{order.shipping_address?.line1}</p>
                <p>
                  {order.shipping_address?.city}, {order.shipping_address?.state}
                </p>
                <p>
                  {order.shipping_address?.postal_code}, {order.shipping_address?.country}
                </p>
              </div>
            </div>
          </div>

          {/* AI Assistant Banner */}
          <div className="p-4 rounded-xl bg-accent-muted border border-accent/20 flex items-start gap-3 text-xs">
            <Sparkles className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-text-primary block">Need help with your order?</span>
              <p className="text-text-secondary leading-relaxed">
                Ask our in-app shopping assistant for pacing tips, shoe break-in schedules, or matching accessories.
              </p>
              <button
                onClick={() => setIsAssistantOpen(true)}
                className="text-xs font-bold text-accent hover:underline inline-block pt-0.5 cursor-pointer"
              >
                Open Assistant Chat →
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Live Status & Timeline (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <OrderTimeline
            status={order.status}
            confirmedAt={order.confirmed_at}
            processingAt={order.processing_at}
            shippedAt={order.shipped_at}
            deliveredAt={order.delivered_at}
            cancelledAt={order.cancelled_at}
            cancellationReason={order.cancellation_reason}
            carrier={order.carrier}
            trackingNumber={order.tracking_number}
          />

          <div className="flex flex-col gap-2.5">
            <Link to="/shop">
              <Button variant="primary" size="md" className="w-full">
                Continue Shopping
              </Button>
            </Link>
            <Link to="/">
              <Button variant="outline" size="sm" className="w-full">
                Return to Home
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailPage;
