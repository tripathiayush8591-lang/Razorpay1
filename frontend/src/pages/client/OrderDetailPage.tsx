import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  CheckCircle2,
  ArrowLeft,
  MapPin,
  User,
  Sparkles,
} from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import OrderTimeline from "../../components/orders/OrderTimeline";

export const OrderDetailPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const { orders, products, setIsAssistantOpen } = useMockCommerce();

  const order = orders.find((o) => o.id === orderId) || orders[0];

  // Sample items display matching seed products
  const displayItems = [
    {
      product: products[0],
      quantity: 1,
      unitPricePaise: products[0]?.price_paise || 549900,
    },
    {
      product: products[5],
      quantity: 1,
      unitPricePaise: products[5]?.price_paise || 69900,
    },
  ];

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
        <span className="text-xs font-mono text-text-muted">Order ID: {order.id}</span>
      </div>

      {/* Confirmation Success Banner */}
      <div className="bg-success-light border border-success/30 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-xs">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-success text-surface flex items-center justify-center shrink-0 shadow-sm">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-extrabold text-text-primary">
                Order Confirmed!
              </h1>
              <Badge variant="accent">CONFIRMED</Badge>
            </div>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
              Thank you, <strong className="text-text-primary">{order.customer_name}</strong>. Your payment was verified server-side and your running gear is being prepared for dispatch.
            </p>
          </div>
        </div>

        <div className="sm:text-right shrink-0">
          <span className="text-xs text-text-secondary block">Paid via Razorpay Test Mode</span>
          <span className="font-mono text-xs font-bold text-text-dark bg-surface/80 px-2.5 py-1 rounded-md border border-border inline-block mt-1">
            {order.razorpay_order_id || "order_test_mock"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Line Items & Customer Details (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Purchased Items Card */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider pb-3 border-b border-border">
              Purchased Equipment
            </h2>

            <div className="divide-y divide-border">
              {displayItems.map((item, idx) => (
                <div key={idx} className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <img
                      src={item.product?.image_url}
                      alt={item.product?.name || "Gear"}
                      className="w-12 h-12 rounded-xl object-cover bg-surface-tertiary border border-border shrink-0"
                    />
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-text-primary truncate">
                        {item.product?.name || "Running Item"}
                      </p>
                      <p className="text-[10px] font-mono text-text-muted">
                        SKU: {item.product?.sku} • Qty: {item.quantity}
                      </p>
                    </div>
                  </div>

                  <span className="text-xs font-extrabold text-text-primary shrink-0">
                    ₹{((item.unitPricePaise * item.quantity) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
            </div>

            {/* Authoritative Total */}
            <div className="pt-4 border-t border-border flex justify-between items-baseline">
              <span className="text-xs font-bold text-text-secondary">Authoritative Total Paid</span>
              <span className="text-lg font-extrabold text-accent">
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
                <p className="font-medium text-text-primary">{order.shipping_address.line1}</p>
                <p>{order.shipping_address.city}, {order.shipping_address.state}</p>
                <p>{order.shipping_address.postal_code}, {order.shipping_address.country}</p>
              </div>
            </div>
          </div>

          {/* AI Assistant Reassurance */}
          <div className="p-4 rounded-xl bg-accent-muted border border-accent/20 flex items-start gap-3 text-xs">
            <Sparkles className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-text-primary block">Have questions about your kit?</span>
              <p className="text-text-secondary leading-relaxed">
                You can ask the in-app agent for break-in schedules, marathon pacing strategies, or matching hydration accessories.
              </p>
              <button
                onClick={() => setIsAssistantOpen(true)}
                className="text-xs font-bold text-accent hover:underline inline-block pt-0.5 cursor-pointer"
              >
                Chat with Assistant →
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Live Status & Timeline (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <OrderTimeline status={order.status} confirmedAt={order.confirmed_at} />

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
