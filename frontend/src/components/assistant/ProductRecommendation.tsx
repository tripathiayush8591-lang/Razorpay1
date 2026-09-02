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
    queryKey: ["cart"],
    queryFn: () => apiClient.getOrCreateCart(),
  });

  const cart = cartData?.data;
  const isInCart = cart?.items.some((item) => item.product_id === product.id) ?? false;

  // Real backend cart mutation
  const addMutation = useMutation({
    mutationFn: async () => {
      const activeCart = cart || (await apiClient.getOrCreateCart()).data;
      if (!activeCart) throw new Error("Cart unavailable");
      return apiClient.addToCart(activeCart.id, product.id, 1);
    },
    onSuccess: (res) => {
      queryClient.setQueryData(["cart"], res);
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
      </div>
    </div>
  );
};

export default ProductRecommendation;
