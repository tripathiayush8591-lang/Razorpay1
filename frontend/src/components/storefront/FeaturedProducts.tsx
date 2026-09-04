import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShoppingBag, ArrowRight, Check } from "lucide-react";
import { apiClient, resolveImageUrl } from "@/lib/api/client";
import { useMockCommerce } from "@/lib/mock/MockCommerceContext";
import { Button } from "../ui/Button";

export const FeaturedProducts: React.FC = () => {
  const { addToCart, cartItems } = useMockCommerce();

  // Fetch real active products from backend
  const { data: response } = useQuery({
    queryKey: ["public-products"],
    queryFn: () => apiClient.getProducts(),
  });

  const products = response?.data || [];
  // Pick first 4 active items from backend
  const featured = products.slice(0, 4);

  if (featured.length === 0) return null;

  return (
    <section className="py-12 border-t border-border">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-accent">
            Curated Gear
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mt-1">
            Featured Products
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Engineered for endurance runners and backed by verified warehouse stock.
          </p>
        </div>

        <Link
          to="/shop"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:text-accent-dark transition shrink-0"
        >
          <span>View All Products</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {featured.map((product) => {
          const isInCart = cartItems.some((item) => item.product_id === product.id);
          const displayImage = resolveImageUrl(product.image_url);

          return (
            <div
              key={product.id}
              className="bg-surface rounded-2xl border border-border overflow-hidden shadow-xs hover:border-border-strong hover:shadow-sm transition flex flex-col group"
            >
              {/* Product Image */}
              <div className="h-48 bg-surface-tertiary overflow-hidden relative">
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
                <span className="absolute top-3 right-3 text-[10px] font-medium bg-success-light text-success-foreground px-2 py-0.5 rounded-full border border-success/20">
                  {product.inventory_quantity} in stock
                </span>
              </div>

              {/* Product Content */}
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

                <div className="mt-4 pt-3 border-t border-border flex items-center justify-between gap-2">
                  <div>
                    <span className="text-[10px] text-text-muted block">Price</span>
                    <span className="text-sm font-extrabold text-text-primary">
                      ₹{(product.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <Button
                    variant={isInCart ? "secondary" : "primary"}
                    size="sm"
                    onClick={() => addToCart(product, 1)}
                    icon={isInCart ? <Check className="w-3.5 h-3.5 text-success" /> : <ShoppingBag className="w-3.5 h-3.5" />}
                    className="text-xs"
                  >
                    {isInCart ? "Added" : "Add to Cart"}
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default FeaturedProducts;
