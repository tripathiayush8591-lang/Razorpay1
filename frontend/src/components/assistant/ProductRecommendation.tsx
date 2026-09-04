import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Product } from "../../types/domain";
import { Button } from "../ui/Button";
import { ShoppingBag, Check, Loader2 } from "lucide-react";
import { apiClient, resolveImageUrl } from "../../lib/api/client";

export interface ProductRecommendationProps {
  product: Product;
  reason?: string;
}

export const ProductRecommendation: React.FC<ProductRecommendationProps> = ({
  product,
  reason,
}) => {
  const queryClient = useQueryClient();

  // Active authoritative cart
  const { data: cartData } = useQuery({
    queryKey: ["active-cart"],
    queryFn: () => apiClient.getOrCreateCart(),
  });

  const cart = cartData?.data;
  const isInCart = cart?.items.some((item) => item.product_id === product.id) ?? false;

  // Lightweight recommendation feedback state (stored in localStorage)
  const [feedback, setFeedback] = React.useState<"helpful" | "not_helpful" | null>(() => {
    try {
      return (localStorage.getItem(`runcraft_fb_${product.id}`) as any) || null;
    } catch {
      return null;
    }
  });

  const handleFeedback = (val: "helpful" | "not_helpful") => {
    const nextVal = feedback === val ? null : val;
    setFeedback(nextVal);
    try {
      if (nextVal) {
        localStorage.setItem(`runcraft_fb_${product.id}`, nextVal);
      } else {
        localStorage.removeItem(`runcraft_fb_${product.id}`);
      }
    } catch {
      // ignore storage exceptions
    }
  };

  // Real backend cart mutation
  const addMutation = useMutation({
    mutationFn: async () => {
      const activeCart = cart || (await apiClient.getOrCreateCart()).data;
      if (!activeCart) throw new Error("Cart unavailable");
      return apiClient.addToCart(activeCart.id, product.id, 1);
    },
    onSuccess: (res) => {
      queryClient.setQueryData(["active-cart"], res);
      queryClient.setQueryData(["cart"], res);
      queryClient.invalidateQueries({ queryKey: ["active-cart"] });
      queryClient.invalidateQueries({ queryKey: ["active-quote"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    },
  });

  return (
    <div className="bg-surface border border-border rounded-xl p-3 shadow-xs hover:border-border-strong transition flex flex-col sm:flex-row gap-3 items-center">
      {/* Thumbnail */}
      <div className="w-20 h-20 rounded-lg bg-surface-tertiary overflow-hidden shrink-0 border border-border flex items-center justify-center">
        {product.image_url ? (
          <img
            src={resolveImageUrl(product.image_url)}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <ShoppingBag className="w-6 h-6 text-text-muted" />
        )}
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0 w-full">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] uppercase font-semibold text-text-muted tracking-wider truncate">
            {product.category}
          </span>
          <span className="text-[11px] font-medium text-success bg-success-light px-2 py-0.5 rounded-full border border-success/20 shrink-0">
            {product.inventory_quantity} in stock
          </span>
        </div>

        <h4 className="text-xs font-bold text-text-primary mt-0.5 truncate">{product.name}</h4>
        {reason ? (
          <p className="text-[11px] text-text-secondary mt-0.5 line-clamp-1 italic">
            "{reason}"
          </p>
        ) : (
          <p className="text-[11px] text-text-secondary mt-0.5 line-clamp-1">
            {product.short_description}
          </p>
        )}

        <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-border">
          <span className="text-xs font-bold text-text-primary">
            ₹{(product.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </span>

          <Button
            variant={isInCart ? "secondary" : "primary"}
            size="sm"
            disabled={addMutation.isPending || isInCart}
            onClick={() => addMutation.mutate()}
            icon={
              addMutation.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : isInCart ? (
                <Check className="w-3 h-3 text-success" />
              ) : (
                <ShoppingBag className="w-3 h-3" />
              )
            }
          >
            {addMutation.isPending ? "Adding..." : isInCart ? "In Cart" : "Add to Cart"}
          </Button>
        </div>

        {/* Lightweight Feedback: Helpful / Not helpful */}
        <div className="mt-2 pt-1.5 border-t border-border/60 flex items-center justify-between text-[11px] text-text-secondary">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-text-muted">Recommendation:</span>
            <button
              onClick={() => handleFeedback("helpful")}
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] transition cursor-pointer ${
                feedback === "helpful"
                  ? "bg-success-light text-success font-bold"
                  : "hover:bg-surface-secondary text-text-secondary"
              }`}
              title="Helpful recommendation"
              aria-label="Helpful"
            >
              <span>👍</span>
              <span>Helpful</span>
            </button>
            <button
              onClick={() => handleFeedback("not_helpful")}
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] transition cursor-pointer ${
                feedback === "not_helpful"
                  ? "bg-surface-secondary text-text-dark font-bold"
                  : "hover:bg-surface-secondary text-text-secondary"
              }`}
              title="Not helpful recommendation"
              aria-label="Not helpful"
            >
              <span>👎</span>
              <span>Not helpful</span>
            </button>
          </div>
          {feedback && (
            <span className="text-[9px] text-success font-medium italic">Thanks!</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductRecommendation;
