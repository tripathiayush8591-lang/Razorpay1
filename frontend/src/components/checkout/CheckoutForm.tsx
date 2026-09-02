import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ShieldCheck,
  User,
  MapPin,
  Lock,
  ArrowRight,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export const CheckoutForm: React.FC = () => {
  const navigate = useNavigate();
  const { cartItems, activeQuote, createOrder, clearCart } = useMockCommerce();

  // Form State
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [city, setCity] = useState("");
  const [stateName, setStateName] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fillDemoDetails = () => {
    setCustomerName("Aarav Sharma");
    setCustomerEmail("aarav.running@example.com");
    setCustomerPhone("+91 98765 43210");
    setAddressLine("42 Indiranagar 100ft Road");
    setCity("Bengaluru");
    setStateName("Karnataka");
    setPostalCode("560038");
    setFormError(null);
  };

  const handleApproveAndPlaceOrder = (e: React.FormEvent) => {
    e.preventDefault();

    if (!customerName || !customerEmail || !customerPhone || !addressLine || !city || !postalCode) {
      setFormError("Please provide all required shipping and contact details.");
      return;
    }

    if (cartItems.length === 0) {
      setFormError("Your shopping cart is empty.");
      return;
    }

    setSubmitting(true);

    setTimeout(() => {
      // Create confirmed order in MockCommerceContext
      const newOrder = createOrder({
        cart_id: "cart_guest_demo",
        customer_name: customerName,
        customer_email: customerEmail,
        customer_phone: customerPhone,
        shipping_address: {
          line1: addressLine,
          city,
          state: stateName || "Karnataka",
          postal_code: postalCode,
          country: "India",
        },
        amount_paise: activeQuote.total_paise,
        currency: "INR",
        status: "CONFIRMED",
        razorpay_order_id: `order_test_${Date.now().toString().slice(-6)}`,
        approved_at: new Date().toISOString(),
        paid_at: new Date().toISOString(),
        confirmed_at: new Date().toISOString(),
      });

      // Clear the cart
      clearCart();
      setSubmitting(false);

      // Navigate to the order confirmation page
      navigate(`/orders/${newOrder.id}`);
    }, 600);
  };

  if (cartItems.length === 0) {
    return (
      <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-md mx-auto space-y-4">
        <h2 className="text-lg font-bold text-text-primary">No items to checkout</h2>
        <p className="text-xs text-text-secondary">
          Your cart is currently empty. Please add running gear before proceeding to checkout.
        </p>
        <Link to="/shop">
          <Button variant="primary" size="md">
            Return to Catalog
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleApproveAndPlaceOrder} className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Column: Customer & Shipping Details (7 cols) */}
      <div className="lg:col-span-7 space-y-6">
        {/* Contact Information Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                1. Customer Contact
              </h3>
            </div>
            <button
              type="button"
              onClick={fillDemoDetails}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-accent-light text-accent-dark text-[11px] font-semibold hover:bg-accent-muted transition cursor-pointer"
            >
              <Sparkles className="w-3 h-3" />
              <span>Fill Demo Details</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <Input
                label="Full Name"
                placeholder="Aarav Sharma"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                required
              />
            </div>

            <Input
              label="Email Address"
              type="email"
              placeholder="aarav@example.com"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              helperText="Order confirmation & tracking receipts"
              required
            />

            <Input
              label="Phone Number"
              type="tel"
              placeholder="+91 98765 43210"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Shipping Address Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <MapPin className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              2. Delivery Address
            </h3>
          </div>

          <div className="space-y-4">
            <Input
              label="Street Address / Building"
              placeholder="Flat 302, Palm Grove Apts, 12th Main Road"
              value={addressLine}
              onChange={(e) => setAddressLine(e.target.value)}
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Input
                label="City"
                placeholder="Bengaluru"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />

              <Input
                label="State"
                placeholder="Karnataka"
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                required
              />

              <Input
                label="Postal Code (PIN)"
                placeholder="560038"
                value={postalCode}
                onChange={(e) => setPostalCode(e.target.value)}
                required
              />
            </div>
          </div>
        </div>

        {formError && (
          <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2 text-xs font-semibold">
            <AlertCircle className="w-4 h-4 text-error" />
            <span>{formError}</span>
          </div>
        )}
      </div>

      {/* Right Column: High-Importance Authoritative Approval Card (5 cols) */}
      <div className="lg:col-span-5 bg-surface rounded-2xl border-2 border-accent/40 p-6 shadow-md space-y-5">
        {/* Header */}
        <div className="pb-3 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              3. Authoritative Quote & Approval
            </h3>
          </div>
          <span className="text-[10px] font-semibold text-accent bg-accent-light px-2 py-0.5 rounded-full">
            Explicit Consent
          </span>
        </div>

        {/* Selected Items Breakdown */}
        <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
          {activeQuote.items.map((item) => (
            <div key={item.product_id} className="flex justify-between items-center text-xs py-1">
              <span className="text-text-primary font-medium truncate max-w-[220px]">
                {item.quantity}× {item.name}
              </span>
              <span className="font-mono text-text-dark font-bold text-[11px] shrink-0">
                ₹{(item.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            </div>
          ))}
        </div>

        {/* Quote Financial Breakdown */}
        <div className="pt-3 border-t border-border space-y-2 text-xs">
          <div className="flex justify-between text-text-secondary">
            <span>Subtotal</span>
            <span>₹{(activeQuote.subtotal_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
          </div>

          {activeQuote.discount_paise > 0 && (
            <div className="flex justify-between text-success font-medium">
              <span>Applied Volume Promotion</span>
              <span>-₹{(activeQuote.discount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
          )}

          <div className="flex justify-between text-text-secondary">
            <span>Standard Delivery</span>
            <span>
              {activeQuote.delivery_paise === 0 ? (
                <span className="text-success font-semibold">FREE</span>
              ) : (
                `₹${(activeQuote.delivery_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
              )}
            </span>
          </div>

          <div className="pt-3 border-t border-border flex justify-between items-baseline">
            <span className="text-sm font-extrabold text-text-primary">Grand Authoritative Total</span>
            <span className="text-2xl font-black text-accent">
              ₹{(activeQuote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* Explicit Human Approval CTA */}
        <div className="pt-2 space-y-3">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={submitting}
            className="w-full justify-center gap-2 font-bold text-sm shadow-sm"
          >
            <Lock className="w-4 h-4" />
            <span>
              Approve ₹{(activeQuote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} & Place Order
            </span>
            <ArrowRight className="w-4 h-4" />
          </Button>

          <p className="text-[11px] text-text-secondary text-center leading-relaxed">
            By approving, you authorize the simulated creation and signature verification of a Razorpay test transaction.
          </p>
        </div>

        {/* Security / Guardrail pill */}
        <div className="p-3 rounded-xl bg-surface-secondary border border-border flex items-center gap-2 text-[11px] text-text-muted">
          <ShieldCheck className="w-4 h-4 text-success shrink-0" />
          <span>Guaranteed by Merchant Policy: No autonomous agent payments without human approval.</span>
        </div>
      </div>
    </form>
  );
};

export default CheckoutForm;
