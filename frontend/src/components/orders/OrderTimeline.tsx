import React from "react";
import { CheckCircle2, Clock, Truck, ShieldCheck, Package } from "lucide-react";
import type { OrderStatus } from "../../types/domain";

export interface OrderTimelineProps {
  status: OrderStatus;
  confirmedAt?: string;
}

export const OrderTimeline: React.FC<OrderTimelineProps> = ({ status, confirmedAt }) => {
  const steps = [
    {
      title: "Order Placed & Quote Validated",
      description: "Authoritative price and live warehouse inventory confirmed.",
      icon: <ShieldCheck className="w-4 h-4" />,
      completed: true,
      current: false,
    },
    {
      title: "Customer Approval & Consent",
      description: "Explicit purchase approval provided by shopper.",
      icon: <CheckCircle2 className="w-4 h-4" />,
      completed: true,
      current: false,
    },
    {
      title: "Razorpay Test Mode Payment Captured",
      description: "Payment signature verified server-side with zero discrepancy.",
      icon: <Clock className="w-4 h-4" />,
      completed: status === "CONFIRMED" || status === "PAID" || status === "FULFILLED",
      current: status === "PENDING_PAYMENT",
    },
    {
      title: "Merchant Order Confirmed",
      description: confirmedAt
        ? `Order confirmed on ${new Date(confirmedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
        : "Order is verified and recorded in merchant database.",
      icon: <Package className="w-4 h-4" />,
      completed: status === "CONFIRMED" || status === "FULFILLED",
      current: status === "PAID",
    },
    {
      title: "Dispatch & Courier Delivery",
      description: "Fast standard delivery initiated from Bengaluru fulfillment hub.",
      icon: <Truck className="w-4 h-4" />,
      completed: status === "FULFILLED",
      current: status === "CONFIRMED",
    },
  ];

  return (
    <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
          Live Order Status & Timeline
        </h3>
        <span className="text-[10px] font-mono font-medium text-accent bg-accent-light px-2 py-0.5 rounded-full">
          Status: {status}
        </span>
      </div>

      <div className="relative pl-6 space-y-6 border-l-2 border-border ml-2">
        {steps.map((step, idx) => (
          <div key={idx} className="relative">
            {/* Step Node Dot */}
            <div
              className={`absolute -left-[31px] top-0 w-6 h-6 rounded-full flex items-center justify-center text-xs transition ${
                step.completed
                  ? "bg-accent text-accent-foreground ring-4 ring-accent-light"
                  : step.current
                  ? "bg-warning text-surface ring-4 ring-warning-light animate-pulse"
                  : "bg-surface-secondary text-text-muted border border-border"
              }`}
            >
              {step.icon}
            </div>

            <div className="space-y-0.5">
              <h4 className={`text-xs font-bold ${step.completed || step.current ? "text-text-primary" : "text-text-muted"}`}>
                {step.title}
              </h4>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrderTimeline;
