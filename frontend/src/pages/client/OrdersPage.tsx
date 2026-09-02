import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Package, Calendar } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";

export const OrdersPage: React.FC = () => {
  const { orders } = useMockCommerce();

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary">Order History & Tracking</h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Review your previous confirmed purchases, test payment receipts, and delivery updates.
        </p>
      </div>

      {orders.length === 0 ? (
        <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-md mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-surface-secondary flex items-center justify-center text-text-muted mx-auto border border-border">
            <Package className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-text-primary">No orders placed yet</h3>
          <p className="text-xs text-text-secondary">
            Once you approve an order and complete test checkout, your order receipt will appear here.
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
                  <span className="text-base font-extrabold text-text-primary mt-1 block">
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
