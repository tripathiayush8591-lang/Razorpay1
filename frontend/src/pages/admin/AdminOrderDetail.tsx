import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  User,
  MapPin,
  Clock,
  Lock,
  Package,
  Truck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ShoppingBag,
  RefreshCw,
} from "lucide-react";
import { apiClient, ApiErrorClass } from "../../lib/api/client";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Input } from "../../components/ui/Input";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";
import type { FulfillmentUpdateRequest, OrderStatus, PaymentStatus } from "../../types/domain";

export const AdminOrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const queryClient = useQueryClient();

  // Shipping form inputs
  const [carrier, setCarrier] = useState("RunCraft Express");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [showShipForm, setShowShipForm] = useState(false);

  // Cancellation form inputs
  const [cancellationReason, setCancellationReason] = useState("");
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // 1. Fetch Order Details
  const {
    data: orderResponse,
    isLoading: isOrderLoading,
    isFetching: isOrderFetching,
    refetch: refetchOrder,
  } = useQuery({
    queryKey: ["admin", "order", orderId],
    queryFn: () => apiClient.getAdminOrder(orderId!),
    enabled: !!orderId,
  });

  // 2. Fetch Order Audit Events
  const {
    data: auditResponse,
    isLoading: isAuditLoading,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ["admin", "order", orderId, "audit"],
    queryFn: () => apiClient.getAdminOrderAudit(orderId!),
    enabled: !!orderId,
  });

  const order = orderResponse?.data;
  const auditEvents = auditResponse?.data || [];

  // 3. Fulfillment Transition Mutation
  const fulfillmentMutation = useMutation({
    mutationFn: (payload: FulfillmentUpdateRequest) =>
      apiClient.updateAdminFulfillment(orderId!, payload),
    onSuccess: () => {
      setActionError(null);
      setShowShipForm(false);
      setShowCancelModal(false);
      setCancellationReason("");
      queryClient.invalidateQueries({ queryKey: ["admin", "order", orderId] });
      queryClient.invalidateQueries({ queryKey: ["admin", "order", orderId, "audit"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] });
    },
    onError: (err: unknown) => {
      if (err instanceof ApiErrorClass) {
        setActionError(err.message);
      } else {
        setActionError("Failed to update fulfillment state. Please try again.");
      }
    },
  });

  if (isOrderLoading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-text-secondary">Loading authoritative order record...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-8 text-center space-y-4 max-w-md mx-auto">
        <AlertCircle className="w-10 h-10 text-error mx-auto" />
        <h2 className="text-base font-bold text-text-primary">Order Not Found</h2>
        <p className="text-xs text-text-secondary">
          The requested order does not exist or has been removed from the merchant catalog.
        </p>
        <Link to="/admin/orders">
          <Button variant="outline" size="sm">
            Back to Orders
          </Button>
        </Link>
      </div>
    );
  }

  const items = order.items || [];
  const subtotalPaise = items.reduce((sum, it) => sum + it.total_paise, 0);
  const deliveryPaise = Math.max(0, order.amount_paise - subtotalPaise);

  const getPaymentBadge = (status?: PaymentStatus) => {
    switch (status) {
      case "PAID":
        return <Badge variant="success">PAID</Badge>;
      case "FAILED":
        return <Badge variant="error">FAILED</Badge>;
      default:
        return <Badge variant="warning">PENDING_PAYMENT</Badge>;
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

  const formatActionName = (action: string) => {
    return action
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/admin/orders"
            className="p-2 rounded-xl bg-surface border border-border text-text-secondary hover:text-text-primary transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl font-bold text-text-primary">Order {order.id}</h1>
              {getPaymentBadge(order.payment_status)}
              {getFulfillmentBadge(order.status)}
            </div>
            <p className="text-xs text-text-secondary mt-0.5 font-mono">
              Created on {new Date(order.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchOrder();
              refetchAudit();
            }}
            disabled={isOrderFetching}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isOrderFetching ? "animate-spin" : ""}`} />}
          >
            Refresh
          </Button>
          <Link to="/admin/orders">
            <Button variant="outline" size="sm">
              All Orders
            </Button>
          </Link>
        </div>
      </div>

      {/* Action Error Banner */}
      {actionError && (
        <div className="p-4 rounded-xl bg-error/10 border border-error/20 flex items-start gap-3 text-xs text-error">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold">Fulfillment Action Failed</p>
            <p>{actionError}</p>
          </div>
        </div>
      )}

      {/* Cancellation Notice Banner if Cancelled */}
      {order.status === "CANCELLED" && (
        <div className="p-4 rounded-xl bg-error-light border border-error/30 flex items-start gap-3 text-xs">
          <XCircle className="w-5 h-5 text-error shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-bold text-text-primary">Fulfillment Cancelled</p>
            <p className="text-text-secondary">
              Reason: <strong>{order.cancellation_reason || "No reason specified"}</strong>
            </p>
            <p className="text-[11px] text-text-muted mt-1">
              Note: Under the Phase 6 MVP policy, payment was captured and inventory remains allocated. Refund and restocking workflows will be processed in a future phase.
            </p>
          </div>
        </div>
      )}

      {/* Fulfillment Workflow Action Bar */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold text-text-primary">Fulfillment Workflow</h2>
          <p className="text-xs text-text-secondary">
            Advance the order through warehouse preparation, carrier dispatch, and confirmed delivery.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {order.status === "CONFIRMED" && (
            <>
              <Button
                variant="primary"
                size="sm"
                disabled={fulfillmentMutation.isPending}
                onClick={() => fulfillmentMutation.mutate({ status: "PROCESSING" })}
                icon={<Package className="w-3.5 h-3.5" />}
              >
                Mark as Processing
              </Button>
              <Button
                variant="destructive"
                size="sm"
                disabled={fulfillmentMutation.isPending}
                onClick={() => setShowCancelModal(true)}
              >
                Cancel Order
              </Button>
            </>
          )}

          {order.status === "PROCESSING" && (
            <>
              {!showShipForm ? (
                <Button
                  variant="primary"
                  size="sm"
                  disabled={fulfillmentMutation.isPending}
                  onClick={() => {
                    setTrackingNumber(`BLR-${Math.floor(10000 + Math.random() * 90000)}`);
                    setShowShipForm(true);
                  }}
                  icon={<Truck className="w-3.5 h-3.5" />}
                >
                  Mark as Shipped
                </Button>
              ) : null}
              <Button
                variant="destructive"
                size="sm"
                disabled={fulfillmentMutation.isPending}
                onClick={() => setShowCancelModal(true)}
              >
                Cancel Order
              </Button>
            </>
          )}

          {order.status === "SHIPPED" && (
            <Button
              variant="primary"
              size="sm"
              disabled={fulfillmentMutation.isPending}
              onClick={() => fulfillmentMutation.mutate({ status: "DELIVERED" })}
              icon={<CheckCircle2 className="w-3.5 h-3.5" />}
            >
              Mark as Delivered
            </Button>
          )}

          {order.status === "DELIVERED" && (
            <div className="flex items-center gap-1.5 text-xs text-success font-semibold bg-success-light px-3 py-1.5 rounded-lg border border-success/30">
              <CheckCircle2 className="w-4 h-4" />
              <span>Fulfilled & Delivered</span>
            </div>
          )}

          {order.status === "CANCELLED" && (
            <div className="flex items-center gap-1.5 text-xs text-error font-semibold bg-error-light px-3 py-1.5 rounded-lg border border-error/30">
              <XCircle className="w-4 h-4" />
              <span>Cancelled</span>
            </div>
          )}
        </div>
      </div>

      {/* Inline Shipping Form */}
      {showShipForm && order.status === "PROCESSING" && (
        <div className="bg-surface rounded-2xl border border-accent/40 p-5 shadow-sm space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Truck className="w-4 h-4 text-accent" />
              <span>Dispatch Shipment Information</span>
            </h3>
            <button
              onClick={() => setShowShipForm(false)}
              className="text-xs text-text-muted hover:text-text-primary"
            >
              Cancel
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-text-secondary block mb-1">Carrier Name</label>
              <Input
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
                placeholder="e.g. BlueDart, Delhivery, RunCraft Fleet"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-text-secondary block mb-1">Tracking Number</label>
              <Input
                value={trackingNumber}
                onChange={(e) => setTrackingNumber(e.target.value)}
                placeholder="e.g. BLR-98421"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setShowShipForm(false)}>
              Discard
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={fulfillmentMutation.isPending}
              onClick={() =>
                fulfillmentMutation.mutate({
                  status: "SHIPPED",
                  carrier: carrier.trim() || undefined,
                  tracking_number: trackingNumber.trim() || undefined,
                })
              }
            >
              {fulfillmentMutation.isPending ? "Updating..." : "Confirm & Dispatch"}
            </Button>
          </div>
        </div>
      )}

      {/* Cancellation Modal / Card */}
      {showCancelModal && (
        <div className="bg-surface rounded-2xl border border-error/40 p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-error pb-3 border-b border-border">
            <AlertCircle className="w-5 h-5" />
            <h3 className="text-sm font-bold text-text-primary">Cancel Order Fulfillment</h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Please provide an administrative reason for cancelling this order. Under the Phase 6 MVP policy, no automatic Razorpay refund will be initiated and inventory remains allocated.
          </p>
          <div>
            <label className="text-xs font-bold text-text-secondary block mb-1">
              Cancellation Reason <span className="text-error">*</span>
            </label>
            <Input
              value={cancellationReason}
              onChange={(e) => setCancellationReason(e.target.value)}
              placeholder="e.g. Customer requested cancellation before dispatch"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setShowCancelModal(false)}>
              Back
            </Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={!cancellationReason.trim() || fulfillmentMutation.isPending}
              onClick={() =>
                fulfillmentMutation.mutate({
                  status: "CANCELLED",
                  cancellation_reason: cancellationReason.trim(),
                })
              }
            >
              {fulfillmentMutation.isPending ? "Cancelling..." : "Confirm Cancellation"}
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Items & Customer Details (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Order Items Table (Immutable Snapshot) */}
          <div className="bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-text-primary">Purchased Line Items</h2>
                <p className="text-[11px] text-text-muted">Immutable snapshot captured at checkout approval</p>
              </div>
              <span className="text-xs text-text-muted font-mono bg-surface-secondary px-2.5 py-0.5 rounded-full border border-border">
                {items.length} Product{items.length !== 1 ? "s" : ""}
              </span>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU & Product</TableHead>
                  <TableHead>Unit Price</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead className="text-right">Line Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-text-secondary">
                      No line items recorded in order snapshot.
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-surface-tertiary border border-border flex items-center justify-center text-text-muted shrink-0">
                            <ShoppingBag className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-bold text-xs text-text-primary">{item.name}</p>
                            <p className="text-[10px] font-mono text-text-muted">{item.sku}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-text-primary font-medium font-mono">
                        ₹{(item.unit_price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell className="text-xs font-bold text-text-primary font-mono">{item.quantity}</TableCell>
                      <TableCell className="text-right font-extrabold text-xs text-text-primary font-mono">
                        ₹{(item.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>

            {/* Price Breakdown Footer */}
            <div className="p-5 bg-surface-secondary/40 border-t border-border space-y-2 text-xs">
              <div className="flex justify-between text-text-secondary">
                <span>Subtotal</span>
                <span className="font-mono">₹{(subtotalPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-text-secondary">
                <span>Delivery Fee</span>
                <span className="font-mono">
                  {deliveryPaise === 0 ? "FREE" : `₹${(deliveryPaise / 100).toFixed(2)}`}
                </span>
              </div>
              <div className="pt-2 border-t border-border flex justify-between text-sm font-extrabold text-text-primary">
                <span>Authoritative Amount</span>
                <span className="text-accent font-extrabold text-base font-mono">
                  ₹{(order.amount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} {order.currency}
                </span>
              </div>
            </div>
          </div>

          {/* Customer & Shipping Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-3">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <User className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide">Customer Details</h3>
              </div>
              <div className="space-y-1 text-xs">
                <p className="font-semibold text-text-primary">{order.customer_name}</p>
                <p className="text-text-secondary">{order.customer_email}</p>
                <p className="text-text-secondary font-mono">{order.customer_phone}</p>
              </div>
            </div>

            <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-3">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <MapPin className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide">Shipping Address</h3>
              </div>
              <div className="space-y-1 text-xs text-text-secondary">
                <p className="text-text-primary font-medium">{order.shipping_address?.line1}</p>
                <p>
                  {order.shipping_address?.city}, {order.shipping_address?.state} - {order.shipping_address?.postal_code}
                </p>
                <p>{order.shipping_address?.country}</p>
              </div>
            </div>
          </div>

          {/* Payment & Logistics Metadata */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-success" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide">Payment & Provider Info</h3>
              </div>
              {getPaymentBadge(order.payment_status)}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-[10px] text-text-muted uppercase block">Razorpay Order ID</span>
                <code className="font-mono text-text-primary block mt-0.5">{order.razorpay_order_id || "N/A"}</code>
              </div>
              <div>
                <span className="text-[10px] text-text-muted uppercase block">Carrier</span>
                <span className="font-medium text-text-primary block mt-0.5">{order.carrier || "Not assigned"}</span>
              </div>
              <div>
                <span className="text-[10px] text-text-muted uppercase block">Tracking Number</span>
                <code className="font-mono text-text-primary block mt-0.5">{order.tracking_number || "Not assigned"}</code>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Authoritative Audit Trail Timeline (4 cols) */}
        <div className="lg:col-span-4 bg-surface rounded-2xl border border-border p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide">Audit Trail History</h3>
            </div>
            <span className="text-[10px] font-mono text-text-muted bg-surface-secondary px-2 py-0.5 rounded border border-border">
              Authoritative
            </span>
          </div>

          {isAuditLoading ? (
            <div className="py-8 text-center space-y-2">
              <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-text-secondary">Loading audit records...</p>
            </div>
          ) : auditEvents.length === 0 ? (
            <p className="text-xs text-text-secondary py-4 text-center">No audit events recorded.</p>
          ) : (
            <div className="space-y-5">
              {auditEvents.map((evt) => (
                <div key={evt.id} className="relative pl-6 pb-2 border-l border-border last:border-l-transparent">
                  <span className="absolute -left-1.5 top-0.5 w-3 h-3 rounded-full bg-accent ring-4 ring-accent-light" />
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-text-primary">{formatActionName(evt.action)}</span>
                    <span className="text-[10px] font-mono text-text-muted">
                      {new Date(evt.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-mono bg-surface-secondary text-text-secondary px-1.5 py-0.5 rounded border border-border">
                      {evt.actor_type}
                    </span>
                    <span className="text-[10px] text-text-muted">
                      {new Date(evt.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                    </span>
                  </div>
                  {evt.metadata && Object.keys(evt.metadata).length > 0 ? (
                    <div className="mt-1.5 p-2 rounded-lg bg-surface-secondary/50 border border-border text-[11px] text-text-secondary space-y-0.5">
                      {evt.metadata.new_status ? (
                        <p>Status: <strong className="text-text-primary">{String(evt.metadata.new_status)}</strong></p>
                      ) : null}
                      {evt.metadata.carrier ? (
                        <p>Carrier: <span className="font-medium text-text-primary">{String(evt.metadata.carrier)}</span></p>
                      ) : null}
                      {evt.metadata.tracking_number ? (
                        <p>Tracking: <code className="font-mono text-text-primary">{String(evt.metadata.tracking_number)}</code></p>
                      ) : null}
                      {evt.metadata.cancellation_reason ? (
                        <p className="text-error font-medium">Reason: {String(evt.metadata.cancellation_reason)}</p>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminOrderDetail;
