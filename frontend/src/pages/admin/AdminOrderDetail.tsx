import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  User,
  MapPin,
  Clock,
  Lock,
  Sparkles,
} from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../components/ui/Table";

export const AdminOrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const { orders, products } = useMockCommerce();

  const order = orders.find((o) => o.id === orderId) || orders[0];

  // Pick sample products for line item display
  const sampleItems = [
    {
      product: products[0],
      quantity: 1,
      unitPricePaise: products[0].price_paise,
    },
    {
      product: products[5],
      quantity: 1,
      unitPricePaise: products[5].price_paise,
    },
  ];

  const subtotalPaise = sampleItems.reduce((sum, item) => sum + item.unitPricePaise * item.quantity, 0);
  const deliveryPaise = 0; // Free delivery
  const totalPaise = subtotalPaise + deliveryPaise;

  const timelineEvents = [
    {
      time: "10:14:00",
      title: "Cart Created & Constraints Ingested",
      desc: "User prompted: 'Build beginner running kit under ₹8,000'. In-app agent initialized guest session.",
      status: "completed",
    },
    {
      time: "10:14:30",
      title: "Authoritative Quote Generated",
      desc: "Live inventory locked; cross-sell socks recommendation policy triggered and validated.",
      status: "completed",
    },
    {
      time: "10:15:00",
      title: "Explicit Customer Approval",
      desc: "Customer reviewed Approval Card and clicked 'Approve ₹6,198.00'. Consent recorded.",
      status: "completed",
    },
    {
      time: "10:15:30",
      title: "Razorpay Test Transaction Created",
      desc: `Server generated Razorpay Order ${order.razorpay_order_id || "order_test_mock_101"} in INR paise.`,
      status: "completed",
    },
    {
      time: "10:16:00",
      title: "Payment Signature Verified",
      desc: "HMAC-SHA256 test checkout signature verified server-side. Webhook processed idempotently.",
      status: "completed",
    },
    {
      time: "10:16:02",
      title: "Merchant Order CONFIRMED",
      desc: "Order status transitioned to CONFIRMED. Warehouse fulfillment triggered.",
      status: "completed",
    },
  ];

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
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-text-primary">Order {order.id}</h1>
              <Badge variant={order.status === "CONFIRMED" ? "accent" : "success"}>
                {order.status}
              </Badge>
            </div>
            <p className="text-xs text-text-secondary mt-0.5">
              Placed on {new Date(order.created_at).toLocaleDateString()} via In-App Commerce Agent
            </p>
          </div>
        </div>

        <Link to="/admin/orders">
          <Button variant="outline" size="sm">
            Back to Orders
          </Button>
        </Link>
      </div>

      {/* Demo Notice */}
      <div className="p-3.5 rounded-xl bg-accent-muted border border-accent/20 flex items-start gap-3 text-xs">
        <Sparkles className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-semibold text-text-primary">Phase 1 Simulated Order Inspection</p>
          <p className="text-text-secondary">
            Payment signatures and event states below demonstrate the authoritative audit pipeline. Real Razorpay Test Mode checkout connects in Phase 5.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Items & Customer Details (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Order Items Table */}
          <div className="bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <h2 className="text-sm font-bold text-text-primary">Purchased Line Items</h2>
              <span className="text-xs text-text-muted">{sampleItems.length} Products</span>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU & Product</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Unit Price</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead className="text-right">Line Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sampleItems.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <img
                          src={item.product.image_url}
                          alt={item.product.name}
                          className="w-10 h-10 rounded-lg object-cover bg-surface-tertiary border border-border shrink-0"
                        />
                        <div>
                          <p className="font-bold text-xs text-text-primary">{item.product.name}</p>
                          <p className="text-[10px] font-mono text-text-muted">{item.product.sku}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-text-secondary">{item.product.category}</TableCell>
                    <TableCell className="text-xs text-text-primary font-medium">
                      ₹{(item.unitPricePaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-text-primary">{item.quantity}</TableCell>
                    <TableCell className="text-right font-extrabold text-xs text-text-primary">
                      ₹{((item.unitPricePaise * item.quantity) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Price Breakdown Footer */}
            <div className="p-5 bg-surface-secondary/40 border-t border-border space-y-2 text-xs">
              <div className="flex justify-between text-text-secondary">
                <span>Subtotal</span>
                <span>₹{(subtotalPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-text-secondary">
                <span>Standard Delivery</span>
                <span className="text-success font-semibold">FREE (Threshold Met)</span>
              </div>
              <div className="pt-2 border-t border-border flex justify-between text-sm font-extrabold text-text-primary">
                <span>Total Paid</span>
                <span className="text-accent font-extrabold text-base">
                  ₹{(totalPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>

          {/* Customer & Delivery Cards */}
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
                <p className="text-text-primary font-medium">{order.shipping_address.line1}</p>
                <p>{order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.postal_code}</p>
                <p>{order.shipping_address.country}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Visual Audit & Status Timeline (4 cols) */}
        <div className="lg:col-span-4 bg-surface rounded-2xl border border-border p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide">Audit Trail Timeline</h3>
              </div>
              <span className="text-[10px] font-mono text-text-muted">Authoritative</span>
            </div>

            <div className="space-y-5">
              {timelineEvents.map((evt, idx) => (
                <div key={idx} className="relative pl-6 pb-2 border-l border-border last:border-l-transparent">
                  <span className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-accent ring-4 ring-accent-light" />
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-text-primary">{evt.title}</span>
                    <span className="text-[10px] font-mono text-text-muted">{evt.time}</span>
                  </div>
                  <p className="text-[11px] text-text-secondary mt-1 leading-relaxed">{evt.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border">
            <div className="p-3 rounded-xl bg-surface-secondary border border-border flex items-center gap-2 text-xs text-text-secondary">
              <Lock className="w-3.5 h-3.5 text-success shrink-0" />
              <span>Razorpay Order ID: <code className="font-mono text-text-primary">{order.razorpay_order_id || "order_test_mock"}</code></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminOrderDetail;
