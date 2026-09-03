import React from "react";
import { CheckCircle2, Clock, Truck, ShieldCheck, Package, XCircle } from "lucide-react";
import type { OrderStatus } from "../../types/domain";

export interface OrderTimelineProps {
  status: OrderStatus;
  confirmedAt?: string;
  processingAt?: string;
  shippedAt?: string;
  deliveredAt?: string;
  cancelledAt?: string;
  cancellationReason?: string;
  carrier?: string;
  trackingNumber?: string;
}

export const OrderTimeline: React.FC<OrderTimelineProps> = ({
  status,
  confirmedAt,
  processingAt,
  shippedAt,
  deliveredAt,
  cancelledAt,
  cancellationReason,
  carrier,
  trackingNumber,
}) => {
  const isCancelled = status === "CANCELLED";

  const steps = isCancelled
    ? [
        {
          title: "Payment Captured",
          description: "Payment signature verified server-side with zero discrepancy.",
          icon: <Clock className="w-4 h-4" />,
          completed: true,
          current: false,
        },
        {
          title: "Merchant Order Confirmed",
          description: confirmedAt
            ? `Order confirmed on ${new Date(confirmedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
            : "Order was recorded in merchant database.",
          icon: <Package className="w-4 h-4" />,
          completed: true,
          current: false,
        },
        {
          title: "Fulfillment Cancelled",
          description: cancellationReason
            ? `Reason: ${cancellationReason}`
            : cancelledAt
            ? `Cancelled on ${new Date(cancelledAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
            : "Order fulfillment was cancelled by merchant administrator.",
          icon: <XCircle className="w-4 h-4" />,
          completed: false,
          current: true,
          isError: true,
        },
      ]
    : [
        {
          title: "Payment Captured",
          description: "Razorpay payment signature verified server-side.",
          icon: <Clock className="w-4 h-4" />,
          completed: status !== "PENDING_PAYMENT",
          current: status === "PENDING_PAYMENT",
        },
        {
          title: "Merchant Order Confirmed",
          description: confirmedAt
            ? `Order confirmed on ${new Date(confirmedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
            : "Order is verified and recorded in merchant database.",
          icon: <ShieldCheck className="w-4 h-4" />,
          completed: ["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"].includes(status),
          current: status === "CONFIRMED",
        },
        {
          title: "Warehouse Processing",
          description: processingAt
            ? `Processing started on ${new Date(processingAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
            : "Gear is being inspected, picked, and packed in warehouse.",
          icon: <Package className="w-4 h-4" />,
          completed: ["PROCESSING", "SHIPPED", "DELIVERED"].includes(status),
          current: status === "PROCESSING",
        },
        {
          title: "Dispatched & In Transit",
          description: shippedAt
            ? `Dispatched via ${carrier || "Express Courier"} ${trackingNumber ? `(${trackingNumber})` : ""}.`
            : "Fast delivery scheduled from fulfillment hub.",
          icon: <Truck className="w-4 h-4" />,
          completed: ["SHIPPED", "DELIVERED"].includes(status),
          current: status === "SHIPPED",
        },
        {
          title: "Delivered",
          description: deliveredAt
            ? `Delivered on ${new Date(deliveredAt).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}.`
            : "Package will be delivered to your shipping address.",
          icon: <CheckCircle2 className="w-4 h-4" />,
          completed: status === "DELIVERED",
          current: false,
        },
      ];

  return (
    <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
          Live Order Status & Timeline
        </h3>
        <span
          className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full ${
            isCancelled
              ? "bg-error/15 text-error"
              : status === "DELIVERED"
              ? "bg-success/15 text-success font-bold"
              : "text-accent bg-accent-light"
          }`}
        >
          {status}
        </span>
      </div>

      <div className="relative pl-6 space-y-6 border-l-2 border-border ml-2">
        {steps.map((step, idx) => {
          const isErr = (step as { isError?: boolean }).isError;
          return (
            <div key={idx} className="relative">
              {/* Step Node Dot */}
              <div
                className={`absolute -left-[31px] top-0 w-6 h-6 rounded-full flex items-center justify-center text-xs transition ${
                  isErr
                    ? "bg-error text-surface ring-4 ring-error/20"
                    : step.completed
                    ? "bg-accent text-accent-foreground ring-4 ring-accent-light"
                    : step.current
                    ? "bg-warning text-surface ring-4 ring-warning-light animate-pulse"
                    : "bg-surface-secondary text-text-muted border border-border"
                }`}
              >
                {step.icon}
              </div>

              <div className="space-y-0.5">
                <h4
                  className={`text-xs font-bold ${
                    isErr
                      ? "text-error"
                      : step.completed || step.current
                      ? "text-text-primary"
                      : "text-text-muted"
                  }`}
                >
                  {step.title}
                </h4>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrderTimeline;
