import React from "react";
import type { Quote } from "../../types/domain";
import { Button } from "../ui/Button";
import { ShieldCheck, ArrowRight, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

export interface ApprovalCardProps {
  quote: Quote;
  onApprove?: () => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({ quote, onApprove }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const handleApprove = () => {
    queryClient.invalidateQueries({ queryKey: ["active-cart"] });
    queryClient.invalidateQueries({ queryKey: ["active-quote"] });
    if (onApprove) {
      onApprove();
    } else {
      navigate("/checkout");
    }
  };

  return (
    <div className="bg-surface border-2 border-accent/40 rounded-2xl p-4 shadow-sm space-y-3.5 my-2">
      {/* Header Badge */}
      <div className="flex items-center justify-between pb-2.5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-accent-light flex items-center justify-center text-accent-dark">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-text-primary uppercase tracking-wide">
            Authoritative Purchase Quote
          </span>
        </div>
        <span className="text-[10px] font-medium text-text-muted bg-surface-secondary px-2 py-0.5 rounded-full border border-border">
          Step: User Approval Required
        </span>
      </div>

      {/* Items Summary */}
      <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 text-xs">
        {quote.items.map((item) => (
          <div key={item.product_id} className="flex justify-between items-center py-1">
            <span className="text-text-primary font-medium truncate max-w-[200px]">
              {item.quantity}× {item.name}
            </span>
            <span className="text-text-dark font-mono text-[11px] shrink-0">
              ₹{(item.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
        ))}
      </div>

      {/* Quote Breakdown */}
      <div className="pt-2 border-t border-border space-y-1 text-xs">
        <div className="flex justify-between text-text-secondary">
          <span>Subtotal</span>
          <span>₹{(quote.subtotal_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
        </div>
        {quote.discount_paise > 0 && (
          <div className="flex justify-between text-success font-medium">
            <span>Special AI Kit Discount</span>
            <span>-₹{(quote.discount_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
          </div>
        )}
        <div className="flex justify-between text-text-secondary">
          <span>Estimated Delivery</span>
          <span>
            {quote.delivery_paise === 0 ? (
              <span className="text-success font-medium">FREE</span>
            ) : (
              `₹${(quote.delivery_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
            )}
          </span>
        </div>
        <div className="pt-2 border-t border-border flex justify-between items-baseline">
          <span className="text-xs font-bold text-text-primary">Authoritative Total</span>
          <span className="text-base font-extrabold text-accent">
            ₹{(quote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Explicit Authorize CTA */}
      <div className="pt-2">
        <Button
          variant="primary"
          size="md"
          className="w-full justify-center gap-2 font-semibold shadow-sm"
          onClick={handleApprove}
        >
          <Lock className="w-4 h-4" />
          <span>
            Approve ₹{(quote.total_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} & Checkout
          </span>
          <ArrowRight className="w-4 h-4" />
        </Button>
        <p className="text-[10px] text-text-secondary text-center mt-2">
          By approving, you authorize the creation of a secure Razorpay test order.
        </p>
      </div>
    </div>
  );
};

export default ApprovalCard;
