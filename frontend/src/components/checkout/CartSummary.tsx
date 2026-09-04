import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Trash2, Plus, Minus, ArrowRight, ShieldCheck, Truck, ShoppingBag, AlertTriangle } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../ui/Button";
import { resolveImageUrl } from "../../lib/api/client";

export const CartSummary: React.FC = () => {
  const { cartItems, updateQuantity, removeFromCart, clearCart, activeQuote, policy } = useMockCommerce();
  const navigate = useNavigate();

  const freeDeliveryThresholdPaise = policy.delivery_rules.free_delivery_threshold_paise;
  const currentSubtotalPaise = activeQuote.subtotal_paise;
  const remainingForFreeDeliveryPaise = Math.max(0, freeDeliveryThresholdPaise - currentSubtotalPaise);
  const qualifiesForFreeDelivery = remainingForFreeDeliveryPaise === 0;

  if (cartItems.length === 0) {
    return (
      <div className="bg-surface rounded-2xl border border-border p-12 text-center max-w-lg mx-auto space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-surface-secondary flex items-center justify-center text-text-muted mx-auto border border-border">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-text-primary">Your Shopping Cart is Empty</h2>
        <p className="text-xs text-text-secondary leading-relaxed max-w-sm mx-auto">
          Explore our performance running gear or consult the in-app AI assistant to build a personalized kit.
        </p>
        <div className="pt-3">
          <Link to="/shop">
            <Button variant="primary" size="md">
              Browse Catalog
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Column: Cart Items Table (8 cols) */}
      <div className="lg:col-span-8 bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-text-primary">Cart Items</h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Review selected gear before authoritative quote generation
            </p>
          </div>
          <button
            onClick={clearCart}
            className="text-xs text-text-muted hover:text-error transition cursor-pointer"
          >
            Clear Cart
          </button>
        </div>

        <div className="divide-y divide-border p-5">
          {cartItems.map((item) => {
            const product = item.product;
            const unitPrice = product ? product.price_paise : item.unit_price_paise_snapshot;

            return (
              <div key={item.id} className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                {/* Thumbnail & Info */}
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-16 h-16 rounded-xl bg-surface-tertiary overflow-hidden shrink-0 border border-border">
                    {product?.image_url ? (
                      <img
                        src={resolveImageUrl(product.image_url)}
                        alt={product.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-text-muted">
                        <ShoppingBag className="w-6 h-6" />
                      </div>
                    )}
                  </div>

                  <div className="min-w-0">
                    <span className="text-[10px] font-mono text-text-muted">{product?.sku}</span>
                    <Link to={`/product/${product?.id || item.product_id}`}>
                      <h3 className="text-xs sm:text-sm font-bold text-text-primary hover:text-accent transition truncate">
                        {product?.name || "Catalog Product"}
                      </h3>
                    </Link>
                    <span className="text-xs font-semibold text-text-secondary mt-0.5 block">
                      ₹{(unitPrice / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} each
                    </span>
                  </div>
                </div>

                {/* Quantity Controls & Line Total */}
                <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto">
                  {/* Quantity Controller */}
                  <div className="flex items-center border border-border rounded-xl bg-surface-secondary">
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      className="p-1.5 text-text-secondary hover:text-text-primary transition cursor-pointer"
                      aria-label="Decrease quantity"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-3 text-xs font-bold text-text-primary min-w-[28px] text-center">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      className="p-1.5 text-text-secondary hover:text-text-primary transition cursor-pointer"
                      aria-label="Increase quantity"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Line Total */}
                  <div className="text-right min-w-[90px]">
                    <span className="text-sm font-extrabold text-text-primary block">
                      ₹{((unitPrice * item.quantity) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  {/* Remove Item */}
                  <button
                    onClick={() => removeFromCart(item.id)}
                    className="p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error-light transition cursor-pointer"
                    title="Remove item"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Free Shipping Progress Indicator */}
        <div className="p-4 bg-surface-secondary/60 border-t border-border flex items-center gap-3">
          <Truck className="w-4 h-4 text-accent shrink-0" />
          <div className="flex-1 text-xs">
            {qualifiesForFreeDelivery ? (
              <span className="text-success font-semibold">
                Congratulations! You qualify for FREE Standard Delivery.
              </span>
            ) : (
              <span className="text-text-secondary">
                Add <strong className="text-text-primary">₹{(remainingForFreeDeliveryPaise / 100).toLocaleString("en-IN")}</strong> more to unlock FREE delivery.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Right Column: Authoritative Quote Summary Card (4 cols) */}
      <div className="lg:col-span-4 bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
        <div className="pb-3 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              Authoritative Quote
            </h3>
          </div>
          <span className="text-[10px] text-text-muted font-mono">Live Validation</span>
        </div>

        {/* Quote Breakdown */}
        <div className="space-y-2.5 text-xs">
          <div className="flex justify-between text-text-secondary">
            <span>Subtotal</span>
            <span>₹{(activeQuote.subtotal_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
          </div>

          {activeQuote.discount_paise > 0 && (
            <div className="flex justify-between text-success font-medium">
              <span>Volume Promotion Discount</span>
              <span>-₹{(activeQuote.discount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
          )}

          <div className="flex justify-between text-text-secondary">
            <span>Estimated Delivery</span>
            <span>
              {activeQuote.delivery_paise === 0 ? (
                <span className="text-success font-semibold">FREE</span>
              ) : (
                `₹${(activeQuote.delivery_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
              )}
            </span>
          </div>

          <div className="pt-3 border-t border-border flex justify-between items-baseline">
            <span className="text-sm font-bold text-text-primary">Binding Total</span>
            <span className="text-xl font-extrabold text-accent">
              ₹{(activeQuote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* Warnings if any */}
        {activeQuote.warnings.length > 0 && (
          <div className="p-3 bg-warning-light border border-warning/20 rounded-xl flex items-start gap-2 text-xs text-warning">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{activeQuote.warnings.join(" ")}</span>
          </div>
        )}

        {/* Checkout CTA */}
        <div className="pt-2 space-y-2">
          <Button
            variant="primary"
            size="lg"
            className="w-full justify-between font-semibold shadow-xs"
            onClick={() => navigate("/checkout")}
          >
            <span>Proceed to Checkout</span>
            <ArrowRight className="w-4 h-4" />
          </Button>

          <Link to="/shop" className="block text-center pt-2">
            <span className="text-xs text-text-secondary hover:text-text-primary transition">
              ← Continue Shopping
            </span>
          </Link>
        </div>

        <div className="pt-3 border-t border-border text-[10px] text-text-muted text-center leading-relaxed">
          Review your order before you pay. Your order won't be placed until you approve it.
        </div>
      </div>
    </div>
  );
};

export default CartSummary;
