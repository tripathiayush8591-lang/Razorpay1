import React from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, Check } from "lucide-react";
import type { Product } from "../../types/domain";
import { Button } from "../ui/Button";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";
import { resolveImageUrl } from "../../lib/api/client";

export interface ProductCardProps {
  product: Product;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const { addToCart, cartItems } = useMockCommerce();
  const isInCart = cartItems.some((item) => item.product_id === product.id);

  const isLowStock = product.inventory_quantity <= 15 && product.inventory_quantity > 0;
  const isOutOfStock = product.inventory_quantity === 0;
  const displayImage = resolveImageUrl(product.image_url);

  return (
    <div className="bg-surface rounded-2xl border border-border overflow-hidden shadow-xs hover:border-border-strong hover:shadow-sm transition flex flex-col group">
      {/* Product Image & Badges */}
      <Link to={`/product/${product.id}`} className="block h-52 bg-surface-tertiary overflow-hidden relative">
        <img
          src={displayImage}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
          loading="lazy"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60";
          }}
        />
        <span className="absolute top-3 left-3 bg-surface/90 backdrop-blur-xs text-[10px] font-semibold px-2.5 py-0.5 rounded-md text-text-dark border border-border">
          {product.category}
        </span>
        <span
          className={`absolute top-3 right-3 text-[10px] font-medium px-2 py-0.5 rounded-full border ${
            isOutOfStock
              ? "bg-error-light text-error-foreground border-error/20"
              : isLowStock
              ? "bg-warning-light text-warning border-warning/20"
              : "bg-success-light text-success-foreground border-success/20"
          }`}
        >
          {isOutOfStock ? "Out of stock" : isLowStock ? `Only ${product.inventory_quantity} left` : "In stock"}
        </span>
      </Link>

      {/* Product Information */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <span className="text-[10px] font-mono text-text-muted">{product.sku}</span>
          <Link to={`/product/${product.id}`}>
            <h3 className="text-sm font-bold text-text-primary mt-0.5 hover:text-accent transition line-clamp-1">
              {product.name}
            </h3>
          </Link>
          <p className="text-xs text-text-secondary mt-1 line-clamp-2 leading-relaxed">
            {product.short_description}
          </p>
        </div>

        {/* Pricing & Add to Cart */}
        <div className="mt-4 pt-3 border-t border-border flex items-center justify-between gap-2">
          <div>
            <span className="text-[10px] text-text-muted block leading-none">Price</span>
            <span className="text-sm font-extrabold text-text-primary mt-0.5 block">
              ₹{(product.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>

          <Button
            variant={isInCart ? "secondary" : "primary"}
            size="sm"
            disabled={isOutOfStock}
            onClick={() => addToCart(product, 1)}
            icon={isInCart ? <Check className="w-3.5 h-3.5 text-success" /> : <ShoppingBag className="w-3.5 h-3.5" />}
            className="text-xs shrink-0"
          >
            {isOutOfStock ? "Sold Out" : isInCart ? "Added" : "Add to Cart"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
