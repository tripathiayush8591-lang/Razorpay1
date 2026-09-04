import React from "react";
import { Link } from "react-router-dom";
import { Package, Truck, CheckCircle2, Clock, ArrowRight, ShieldCheck } from "lucide-react";
import type { AgentOrderStatusSnapshot } from "../../types/domain";

export interface OrderStatusCardProps {
  order: AgentOrderStatusSnapshot;
}

export const OrderStatusCard: React.FC<OrderStatusCardProps> = ({ order }) => {
  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "CONFIRMED":
        return {
          label: "Confirmed & Queued",
          badgeClass: "bg-accent-light text-accent-dark border-accent/20",
          icon: <CheckCircle2 className="w-3 h-3 text-accent" />,
          description: "Payment verified. Preparing for dispatch.",
        };
      case "PROCESSING":
        return {
          label: "Processing",
          badgeClass: "bg-warning-light text-warning border-warning/20",
          icon: <Clock className="w-3 h-3 text-warning" />,
          description: "Packed and ready at the warehouse.",
        };
      case "SHIPPED":
        return {
          label: "Shipped",
          badgeClass: "bg-info-light text-info-foreground border-info/20",
          icon: <Truck className="w-3 h-3 text-info" />,
          description: order.carrier ? `In transit via ${order.carrier}` : "In transit with courier.",
        };
      case "DELIVERED":
        return {
          label: "Delivered",
          badgeClass: "bg-success-light text-success border-success/20",
          icon: <CheckCircle2 className="w-3 h-3 text-success" />,
          description: "Delivered to shipping address.",
        };
      case "PENDING_PAYMENT":
        return {
          label: "Pending Payment",
          badgeClass: "bg-warning-light text-warning border-warning/20",
          icon: <Clock className="w-3 h-3 text-warning" />,
          description: "Awaiting customer payment confirmation.",
        };
      default:
        return {
          label: status,
          badgeClass: "bg-surface-secondary text-text-secondary border-border",
          icon: <Package className="w-3 h-3 text-text-muted" />,
          description: "Status update in progress.",
        };
    }
  };

  const statusInfo = getStatusBadge(order.status);
  const formattedTotal = (order.amount_paise / 100).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <div className="bg-surface rounded-xl border border-border p-3.5 shadow-xs space-y-3 animate-in fade-in duration-200">
      {/* Header with Order ID & Status */}
      <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent-light flex items-center justify-center text-accent-dark shrink-0">
            <Package className="w-3.5 h-3.5" />
          </div>
          <div className="min-w-0">
            <span className="text-[10px] text-text-muted block uppercase tracking-wider font-semibold">
              Live Order Status
            </span>
            <span className="text-xs font-bold text-text-primary truncate block">
              Order #{order.order_id}
            </span>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${statusInfo.badgeClass}`}
        >
          {statusInfo.icon}
          <span>{statusInfo.label}</span>
        </span>
      </div>

      {/* Details Row */}
      <div className="grid grid-cols-2 gap-2 text-xs bg-surface-secondary rounded-lg p-2.5 border border-border/60">
        <div>
          <span className="text-[10px] text-text-muted block">Total Paid</span>
          <span className="text-xs font-bold text-text-primary">₹{formattedTotal}</span>
        </div>

        <div>
          <span className="text-[10px] text-text-muted block">Tracking</span>
          {order.tracking_number ? (
            <span className="text-xs font-mono font-medium text-accent truncate block">
              {order.tracking_number}
            </span>
          ) : (
            <span className="text-xs text-text-secondary">Assigned on dispatch</span>
          )}
        </div>

        {order.items_summary && (
          <div className="col-span-2 pt-1 border-t border-border/40">
            <span className="text-[10px] text-text-muted block">Items</span>
            <span className="text-[11px] text-text-secondary truncate block">
              {(order.items_count ?? 0) > 0 ? `${order.items_count} item(s): ` : ""}
              {order.items_summary}
            </span>
          </div>
        )}
      </div>

      {/* Status reassurance */}
      <div className="flex items-center gap-1.5 text-[11px] text-text-secondary">
        <ShieldCheck className="w-3.5 h-3.5 text-success shrink-0" />
        <span className="truncate">{statusInfo.description}</span>
      </div>

      {/* CTA to view full tracking */}
      <Link
        to={`/orders/${order.order_id}`}
        className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-surface-secondary border border-border text-xs font-semibold text-text-primary hover:text-accent hover:border-accent/40 transition group cursor-pointer shadow-2xs"
      >
        <span>View Full Order & Live Tracking</span>
        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
      </Link>
    </div>
  );
};

export default OrderStatusCard;
