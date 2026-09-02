import React from "react";
import { useNavigate } from "react-router-dom";
import { X, Trash2, Plus, Minus, ArrowRight, ShoppingBag, AlertTriangle } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { Button } from "../ui/Button";
import { resolveImageUrl } from "../../lib/api/client";

export const CartDrawer: React.FC = () => {
  const {
    isCartOpen,
    setIsCartOpen,
    cartItems,
    updateQuantity,
    removeFromCart,
    activeQuote,
  } = useMockCommerce();

  const navigate = useNavigate();

  if (!isCartOpen) return null;

  const handleCheckout = () => {
    setIsCartOpen(false);
    navigate("/checkout");
  };

  const handleViewCart = () => {
    setIsCartOpen(false);
    navigate("/cart");
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-text-primary/40 backdrop-blur-xs transition-opacity duration-300"
        onClick={() => setIsCartOpen(false)}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-surface shadow-2xl border-l border-border flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-accent" />
              <h2 className="text-base font-bold text-text-primary">Your Shopping Cart</h2>
              <span className="text-xs bg-surface-secondary text-text-secondary px-2 py-0.5 rounded-full border border-border">
                {cartItems.reduce((sum, item) => sum + item.quantity, 0)} items
              </span>
            </div>
            <button
              onClick={() => setIsCartOpen(false)}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition cursor-pointer"
              aria-label="Close cart"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {cartItems.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-12">
                <div className="w-16 h-16 rounded-full bg-surface-secondary flex items-center justify-center text-text-muted mb-4">
                  <ShoppingBag className="w-8 h-8" />
                </div>
                <h3 className="text-base font-semibold text-text-primary">Your cart is empty</h3>
                <p className="text-xs text-text-secondary mt-1 max-w-xs">
                  Browse our performance running catalog or let our AI assistant assemble a personalized gear kit.
                </p>
                <div className="mt-6">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setIsCartOpen(false);
                      navigate("/shop");
                    }}
                  >
                    Browse Running Gear
                  </Button>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {cartItems.map((item) => {
                  const product = item.product;
                  const unitPrice = product ? product.price_paise : item.unit_price_paise_snapshot;

                  return (
                    <div key={item.id} className="py-4 flex gap-3.5 first:pt-0">
                      {/* Thumbnail */}
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

                      {/* Info */}
                      <div className="flex-1 min-w-0 flex flex-col justify-between">
                        <div>
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="text-xs font-semibold text-text-primary truncate">
                              {product?.name || "Product Item"}
                            </h4>
                            <button
                              onClick={() => removeFromCart(item.id)}
                              className="text-text-muted hover:text-error transition p-0.5 cursor-pointer"
                              title="Remove item"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          <p className="text-[11px] font-mono text-text-muted mt-0.5">
                            {product?.sku || item.product_id}
                          </p>
                        </div>

                        <div className="flex items-center justify-between mt-2">
                          {/* Quantity control */}
                          <div className="flex items-center border border-border rounded-lg bg-surface-secondary">
                            <button
                              onClick={() => updateQuantity(item.id, item.quantity - 1)}
                              className="p-1 text-text-secondary hover:text-text-primary transition cursor-pointer"
                              aria-label="Decrease quantity"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="px-2 text-xs font-semibold text-text-primary min-w-[24px] text-center">
                              {item.quantity}
                            </span>
                            <button
                              onClick={() => updateQuantity(item.id, item.quantity + 1)}
                              className="p-1 text-text-secondary hover:text-text-primary transition cursor-pointer"
                              aria-label="Increase quantity"
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>

                          {/* Line Total */}
                          <span className="text-xs font-bold text-text-primary">
                            ₹{((unitPrice * item.quantity) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Warnings if any */}
            {activeQuote.warnings.length > 0 && (
              <div className="p-3 bg-warning-light border border-warning/20 rounded-xl flex items-start gap-2 text-xs text-warning">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{activeQuote.warnings.join(" ")}</span>
              </div>
            )}
          </div>

          {/* Footer with Quote Summary & CTAs */}
          {cartItems.length > 0 && (
            <div className="px-6 py-4 border-t border-border bg-surface-secondary/60 space-y-3">
              {/* Quote Breakdown */}
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between text-text-secondary">
                  <span>Subtotal</span>
                  <span>₹{(activeQuote.subtotal_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                </div>
                {activeQuote.discount_paise > 0 && (
                  <div className="flex justify-between text-success font-medium">
                    <span>Discount (Volume Offer)</span>
                    <span>-₹{(activeQuote.discount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                  </div>
                )}
                <div className="flex justify-between text-text-secondary">
                  <span>Estimated Delivery</span>
                  <span>
                    {activeQuote.delivery_paise === 0 ? (
                      <span className="text-success font-medium">FREE</span>
                    ) : (
                      `₹${(activeQuote.delivery_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                    )}
                  </span>
                </div>
                <div className="pt-2 border-t border-border flex justify-between text-sm font-bold text-text-primary">
                  <span>Final Total</span>
                  <span>₹{(activeQuote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-2 space-y-2">
                <Button
                  variant="primary"
                  size="md"
                  className="w-full justify-between"
                  onClick={handleCheckout}
                >
                  <span>Review & Checkout</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={handleViewCart}
                >
                  View Full Cart & Live Quote
                </Button>
              </div>

              <p className="text-[10px] text-text-muted text-center pt-1">
                Final authoritative recalculation occurs prior to payment approval.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CartDrawer;
