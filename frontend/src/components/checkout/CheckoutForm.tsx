import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  ShieldCheck,
  User,
  MapPin,
  Lock,
  ArrowRight,
  Sparkles,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
  RefreshCw,
} from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { apiClient, ApiErrorClass } from "../../lib/api/client";
import { loadRazorpayScript } from "../../lib/razorpay";
import type { RazorpayOptions } from "../../types/razorpay";

export const CheckoutForm: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { cartId, cartItems, activeQuote, isCartLoading } = useMockCommerce();

  // Revalidate authoritative cart on mount
  React.useEffect(() => {
    queryClient.invalidateQueries({ queryKey: ["active-cart"] });
    queryClient.invalidateQueries({ queryKey: ["active-quote"] });
  }, [queryClient]);

  // Form State - Pre-filled with demo recipient for frictionless demo flow
  const [customerName, setCustomerName] = useState("Aarav Sharma");
  const [customerEmail, setCustomerEmail] = useState("aarav.running@example.com");
  const [customerPhone, setCustomerPhone] = useState("+91 98765 43210");
  const [addressLine, setAddressLine] = useState("42 Indiranagar 100ft Road");
  const [city, setCity] = useState("Bengaluru");
  const [stateName, setStateName] = useState("Karnataka");
  const [postalCode, setPostalCode] = useState("560038");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [dismissedNotice, setDismissedNotice] = useState<string | null>(null);
  const [isStaleQuote, setIsStaleQuote] = useState(false);

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

  const handleApproveAndPlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!customerName || !customerEmail || !customerPhone || !addressLine || !city || !postalCode) {
      setFormError("Please provide all required shipping and contact details.");
      return;
    }

    if (cartItems.length === 0 || !cartId) {
      setFormError("Your shopping cart is empty.");
      return;
    }

    setSubmitting(true);

    try {
      // 1. Ensure official Razorpay SDK checkout.js is available
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded || !window.Razorpay) {
        throw new Error("Unable to load the official Razorpay payment gateway script. Please check your internet connection.");
      }

      // 2. Call backend checkout initiation endpoint with authoritative quote verification
      const checkoutRes = await apiClient.createCheckout(cartId, {
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
        approved_total_paise: activeQuote.total_paise,
      });

      if (!checkoutRes.data) {
        throw new Error("Invalid response received from checkout service.");
      }

      const {
        merchant_order_id,
        razorpay_order_id,
        razorpay_key_id,
        amount_paise,
        currency,
      } = checkoutRes.data;

      // 3. Configure official Razorpay Standard Checkout modal with RunCraft branding
      const options: RazorpayOptions = {
        key: razorpay_key_id,
        amount: amount_paise,
        currency: currency || "INR",
        name: "RunCraft",
        description: "Official Agentic Commerce Checkout",
        order_id: razorpay_order_id,
        prefill: {
          name: customerName,
          email: customerEmail,
          contact: customerPhone,
        },
        notes: {
          merchant_order_id,
        },
        theme: {
          color: "#7c5cfc", // RunCraft brand accent token
        },
        handler: async (response) => {
          try {
            setSubmitting(true);
            // 4. Send payment identifiers and signature to backend for cryptographic verification
            const verifyRes = await apiClient.verifyPayment({
              merchant_order_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });

            if (!verifyRes.data) {
              throw new Error("Payment verification succeeded but no order data returned.");
            }

            // 5. Invalidate active cart & quote so a clean state is initialized
            queryClient.invalidateQueries({ queryKey: ["active-cart"] });
            queryClient.invalidateQueries({ queryKey: ["active-quote"] });

            // 6. Navigate to authoritative order confirmation view
            navigate(`/orders/${verifyRes.data.order_id}`);
          } catch (verifyErr: any) {
            setSubmitting(false);
            const msg = verifyErr?.message || "Payment verification failed. Please try again or contact support.";
            setFormError(msg);
          }
        },
        modal: {
          ondismiss: () => {
            setSubmitting(false);
            setDismissedNotice("Payment window was closed. Your cart and shipping details are preserved — click 'Approve & Pay' whenever you are ready.");
          },
        },
      };

      // 4. Open official Razorpay modal
      const rzp = new window.Razorpay(options);
      rzp.on("payment.failed", (failRes: any) => {
        setSubmitting(false);
        const desc = failRes?.error?.description || "Transaction declined by gateway";
        setFormError(`Payment failed: ${desc}`);
      });

      rzp.open();
    } catch (err: any) {
      setSubmitting(false);
      const errMsg = err?.message || "";
      if (
        (err instanceof ApiErrorClass && (err.code === "HTTP_409" || err.code === "HTTP_400")) ||
        errMsg.toLowerCase().includes("quote") ||
        errMsg.toLowerCase().includes("approved total")
      ) {
        queryClient.invalidateQueries({ queryKey: ["active-quote"] });
        setIsStaleQuote(true);
        setFormError("The authoritative quote changed on the server (price, stock, or policy update). Please refresh quote to review the latest total and re-approve.");
        return;
      }
      setFormError(errMsg || "Failed to initiate checkout. Please try again.");
    }
  };

  if (isCartLoading) {
    return (
      <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-md mx-auto space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-accent mx-auto" />
        <h2 className="text-lg font-bold text-text-primary">Loading Authoritative Cart...</h2>
        <p className="text-xs text-text-secondary">
          Synchronizing items and pricing with the warehouse ledger.
        </p>
      </div>
    );
  }

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

        {/* Dismissed Notice */}
        {dismissedNotice && !formError && (
          <div className="p-3.5 rounded-xl bg-info-light border border-info/20 text-info-foreground flex items-center justify-between text-xs font-medium animate-in fade-in duration-200">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-info shrink-0" />
              <span>{dismissedNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setDismissedNotice(null)}
              className="text-text-muted hover:text-text-primary p-0.5 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Error / Stale Quote Banner */}
        {formError && (
          <div
            className={`p-4 rounded-xl flex items-start justify-between gap-3 text-xs font-semibold animate-in fade-in duration-200 ${
              isStaleQuote
                ? "bg-warning-light border border-warning/20 text-warning"
                : "bg-error-light border border-error/20 text-error-foreground"
            }`}
          >
            <div className="flex items-start gap-2.5">
              {isStaleQuote ? (
                <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-error shrink-0 mt-0.5" />
              )}
              <div className="space-y-2">
                <span>{formError}</span>
                {isStaleQuote && (
                  <div>
                    <button
                      type="button"
                      onClick={() => {
                        queryClient.invalidateQueries({ queryKey: ["active-quote"] });
                        setFormError(null);
                        setIsStaleQuote(false);
                      }}
                      className="px-3 py-1 rounded-lg bg-warning text-white text-xs font-bold hover:opacity-90 transition cursor-pointer"
                    >
                      Refresh Quote & Review Total
                    </button>
                  </div>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setFormError(null);
                setIsStaleQuote(false);
              }}
              className="text-text-muted hover:text-text-primary p-0.5 cursor-pointer shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
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
              Approve ₹{(activeQuote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} & Pay
            </span>
            <ArrowRight className="w-4 h-4" />
          </Button>

          <p className="text-[11px] text-text-secondary text-center leading-relaxed">
            By approving, you authorize the secure creation of a Razorpay Standard Checkout order.
          </p>
        </div>

        {/* Security / Guardrail pill */}
        <div className="p-3 rounded-xl bg-surface-secondary border border-border flex items-center gap-2 text-[11px] text-text-muted">
          <ShieldCheck className="w-4 h-4 text-success shrink-0" />
          <span>Guaranteed by Merchant Policy: Official Razorpay Web Modal • Zero Autonomous Agent Charges</span>
        </div>
      </div>
    </form>
  );
};

export default CheckoutForm;
