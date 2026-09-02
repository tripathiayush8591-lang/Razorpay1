import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ShoppingBag,
  Check,
  ShieldCheck,
  Sparkles,
  Zap,
  Truck,
  Plus,
  Minus,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { apiClient, resolveImageUrl } from "@/lib/api/client";
import { useMockCommerce } from "@/lib/mock/MockCommerceContext";
import { Button } from "@/components/ui/Button";

export const ProductDetailPage: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const { addToCart, cartItems, policy, setIsAssistantOpen } = useMockCommerce();

  const [quantity, setQuantity] = useState(1);
  const [addedSuccess, setAddedSuccess] = useState(false);

  // Fetch real authoritative product by ID from backend
  const {
    data: response,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["public-product", productId],
    queryFn: () => apiClient.getProductById(productId!),
    enabled: Boolean(productId),
  });

  // Fetch authoritative related products based on merchant cross-sell policy
  const { data: relatedProductsResponse } = useQuery({
    queryKey: ["related-products", productId],
    queryFn: () => apiClient.getRelatedProducts(productId!, 4),
    enabled: Boolean(productId),
  });

  const product = response?.data;
  const relatedProducts = relatedProductsResponse?.data || [];

  // Fetch authoritative delivery estimate for this product price
  const { data: deliveryEstimateResponse } = useQuery({
    queryKey: ["delivery-estimate", product?.price_paise],
    queryFn: () => apiClient.getDeliveryEstimate(product!.price_paise),
    enabled: Boolean(product?.price_paise),
  });

  const deliveryEstimate = deliveryEstimateResponse?.data;

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
        <p className="text-xs text-text-secondary">Loading product specifications...</p>
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="py-20 text-center space-y-4 max-w-md mx-auto">
        <AlertCircle className="w-10 h-10 text-error mx-auto" />
        <h2 className="text-lg font-bold text-text-primary">Product Not Found</h2>
        <p className="text-xs text-text-secondary">
          {error instanceof Error ? error.message : "The product you requested does not exist or is currently inactive."}
        </p>
        <Link to="/shop">
          <Button variant="primary" size="md">
            Return to Storefront Catalog
          </Button>
        </Link>
      </div>
    );
  }

  const isInCart = cartItems.some((item) => item.product_id === product.id);
  const isOutOfStock = product.inventory_quantity === 0;
  const displayImage = resolveImageUrl(product.image_url);

  // Identify cross-sell pairing from merchant policies or authoritative related products
  const crossSellRule = policy?.cross_sell_rules?.find(
    (rule) => rule.trigger_category.toLowerCase() === product.category.toLowerCase()
  );

  const crossSellProduct = relatedProducts.length > 0 ? relatedProducts[0] : undefined;

  const handleAddToCart = () => {
    if (isOutOfStock) return;
    addToCart(product, quantity);
    setAddedSuccess(true);
    setTimeout(() => setAddedSuccess(false), 2500);
  };

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/shop"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-text-primary transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Catalog</span>
        </Link>
        <span className="text-xs font-mono text-text-muted">SKU: {product.sku}</span>
      </div>

      {/* Main Product Showcase Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        {/* Left Column: Image Showcase (6 cols) */}
        <div className="lg:col-span-6 bg-surface rounded-2xl border border-border p-6 shadow-xs flex flex-col items-center">
          <div className="w-full h-80 sm:h-96 rounded-xl bg-surface-tertiary overflow-hidden relative border border-border">
            <img
              src={displayImage}
              alt={product.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src =
                  "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60";
              }}
            />
            <span className="absolute top-4 left-4 bg-surface/90 backdrop-blur-xs text-xs font-semibold px-3 py-1 rounded-md text-text-dark border border-border">
              {product.category}
            </span>
          </div>

          <div className="w-full grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-border text-center text-xs">
            <div className="space-y-0.5">
              <span className="text-text-muted block text-[10px] uppercase">Stock Status</span>
              <span className="font-bold text-success flex items-center justify-center gap-1">
                <Check className="w-3 h-3" /> {product.inventory_quantity} Units
              </span>
            </div>
            <div className="space-y-0.5">
              <span className="text-text-muted block text-[10px] uppercase">Shipping</span>
              <span className="font-bold text-text-primary flex items-center justify-center gap-1">
                <Truck className="w-3 h-3 text-accent" /> {deliveryEstimate?.is_free ? "FREE Delivery" : `₹${(deliveryEstimate?.standard_delivery_paise || 15000) / 100} Standard`}
              </span>
            </div>
            <div className="space-y-0.5">
              <span className="text-text-muted block text-[10px] uppercase">Verification</span>
              <span className="font-bold text-text-primary flex items-center justify-center gap-1">
                <ShieldCheck className="w-3 h-3 text-info" /> Authoritative
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Pricing, Specs & CTA (6 cols) */}
        <div className="lg:col-span-6 space-y-6">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-accent">
              {product.category}
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-1">
              {product.name}
            </h1>
            <p className="text-xs sm:text-sm text-text-secondary mt-2 leading-relaxed">
              {product.short_description}
            </p>
          </div>

          {/* Pricing Row */}
          <div className="p-4 rounded-2xl bg-surface-secondary border border-border flex items-baseline justify-between">
            <div>
              <span className="text-[10px] text-text-muted uppercase tracking-wider block">Authoritative Price</span>
              <span className="text-3xl font-extrabold text-text-primary">
                ₹{(product.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            </div>
            <span className="text-xs font-medium text-success bg-success-light px-2.5 py-1 rounded-full border border-success/20">
              {product.inventory_quantity > 0 ? "Ready to Ship" : "Out of Stock"}
            </span>
          </div>

          {/* Quantity and Add to Cart */}
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              {/* Quantity controller */}
              <div className="flex items-center border border-border rounded-xl bg-surface p-1">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={isOutOfStock || quantity <= 1}
                  className="p-2 text-text-secondary hover:text-text-primary transition cursor-pointer disabled:opacity-40"
                  aria-label="Decrease quantity"
                >
                  <Minus className="w-3.5 h-3.5" />
                </button>
                <span className="px-4 text-xs font-bold text-text-primary min-w-[32px] text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(Math.min(product.inventory_quantity, quantity + 1))}
                  disabled={isOutOfStock || quantity >= product.inventory_quantity}
                  className="p-2 text-text-secondary hover:text-text-primary transition cursor-pointer disabled:opacity-40"
                  aria-label="Increase quantity"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Primary Add to Cart Button */}
              <Button
                variant="primary"
                size="lg"
                disabled={isOutOfStock}
                onClick={handleAddToCart}
                icon={addedSuccess ? <Check className="w-4 h-4 text-surface" /> : <ShoppingBag className="w-4 h-4" />}
                className="flex-1 font-semibold"
              >
                {isOutOfStock ? "Out of Stock" : addedSuccess ? "Added to Cart!" : "Add to Cart"}
              </Button>
            </div>

            {/* In Cart Indicator */}
            {isInCart && (
              <p className="text-xs text-success flex items-center gap-1.5 pt-1">
                <Check className="w-3.5 h-3.5" /> This item is currently in your shopping cart.
              </p>
            )}
          </div>

          {/* AI Consultation Callout */}
          <div className="p-4 rounded-xl bg-accent-muted border border-accent/20 flex items-start gap-3 text-xs">
            <Sparkles className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-text-primary block">Ask the AI Assistant about this item</span>
              <p className="text-text-secondary leading-relaxed">
                Wondering if this shoe fits wide feet or pairs well with hydration vests? The in-app agent can explain sizing and bundle compatible gear.
              </p>
              <button
                onClick={() => setIsAssistantOpen(true)}
                className="text-xs font-bold text-accent hover:underline inline-block pt-1 cursor-pointer"
              >
                Launch AI Assistant →
              </button>
            </div>
          </div>

          {/* Product Specifications Table */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Product Specifications</h3>
            <div className="divide-y divide-border text-xs">
              <div className="flex justify-between py-2">
                <span className="text-text-secondary">Category:</span>
                <span className="font-medium text-text-primary">{product.category}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-text-secondary">Merchant SKU:</span>
                <span className="font-mono font-medium text-text-primary">{product.sku}</span>
              </div>
              {product.attributes &&
                Object.entries(product.attributes).map(([key, val]) => (
                  <div key={key} className="flex justify-between py-2">
                    <span className="text-text-secondary capitalize">{key.replace(/_/g, " ")}:</span>
                    <span className="font-medium text-text-primary">{String(val)}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Description Section */}
      <div className="bg-surface rounded-2xl border border-border p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-text-primary">Detailed Overview & Engineering</h2>
        <p className="text-xs sm:text-sm text-text-secondary leading-relaxed max-w-4xl">
          {product.description}
        </p>
        <div className="pt-2 flex flex-wrap gap-1.5">
          {product.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] font-medium bg-surface-secondary text-text-muted px-2.5 py-1 rounded-full border border-border"
            >
              #{tag}
            </span>
          ))}
        </div>
      </div>

      {/* Cross-Sell Recommendation Card (if rule triggered) */}
      {crossSellProduct && (
        <div className="bg-surface rounded-2xl border-2 border-accent/20 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-accent" />
              <h3 className="text-sm font-bold text-text-primary">
                Merchant Policy Pairing: Recommended With This Gear
              </h3>
            </div>
            <span className="text-[11px] font-medium text-text-muted">Policy Rule Enforced</span>
          </div>

          <p className="text-xs text-text-secondary">
            {crossSellRule?.reason || "Frequently bought together for enhanced endurance training."}
          </p>

          <div className="p-4 rounded-xl bg-surface-secondary border border-border flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <img
                src={resolveImageUrl(crossSellProduct.image_url)}
                alt={crossSellProduct.name}
                className="w-14 h-14 rounded-lg object-cover bg-surface-tertiary border border-border shrink-0"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60";
                }}
              />
              <div>
                <span className="text-[10px] uppercase font-semibold text-text-muted">{crossSellProduct.category}</span>
                <h4 className="text-xs font-bold text-text-primary">{crossSellProduct.name}</h4>
                <span className="text-xs font-extrabold text-text-primary mt-0.5 block">
                  ₹{(crossSellProduct.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => addToCart(crossSellProduct, 1)}
              icon={<ShoppingBag className="w-3.5 h-3.5" />}
              className="shrink-0 text-xs"
            >
              Add Compatible Pair
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDetailPage;
