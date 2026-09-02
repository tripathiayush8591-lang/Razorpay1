import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, ArrowUpDown, SlidersHorizontal, Bot, Loader2, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { useMockCommerce } from "@/lib/mock/MockCommerceContext";
import ProductGrid from "@/components/storefront/ProductGrid";
import ProductFilters from "@/components/storefront/ProductFilters";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";

export const ShopPage: React.FC = () => {
  const { setIsAssistantOpen } = useMockCommerce();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [maxPrice, setMaxPrice] = useState(16000);
  const [inStockOnly, setInStockOnly] = useState(false);
  const [sortBy, setSortBy] = useState<"featured" | "price-asc" | "price-desc" | "stock">("featured");
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Fetch real authoritative active products from FastAPI backend
  const {
    data: response,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["public-products", searchQuery, selectedCategory],
    queryFn: () =>
      apiClient.getProducts({
        q: searchQuery || undefined,
        category: selectedCategory !== "all" ? selectedCategory : undefined,
      }),
  });

  const products = response?.data || [];

  const standardCategories = [
    "Running Shoes",
    "Running Apparel",
    "Running Socks",
    "Hydration & Accessories",
    "Nutrition & Recovery",
  ];
  const dynamicCategories = Array.from(new Set(products.map((p) => p.category)));
  const categories = Array.from(new Set([...standardCategories, ...dynamicCategories]));

  const handleReset = () => {
    setSearchQuery("");
    setSelectedCategory("all");
    setMaxPrice(16000);
    setInStockOnly(false);
    setSortBy("featured");
  };

  // Client-side Price & Stock Filters & Sorting Pipeline
  const filteredProducts = useMemo(() => {
    return products
      .filter((p) => {
        const matchesPrice = p.price_paise / 100 <= maxPrice;
        const matchesStock = inStockOnly ? p.inventory_quantity > 0 : true;
        return matchesPrice && matchesStock;
      })
      .sort((a, b) => {
        if (sortBy === "price-asc") return a.price_paise - b.price_paise;
        if (sortBy === "price-desc") return b.price_paise - a.price_paise;
        if (sortBy === "stock") return b.inventory_quantity - a.inventory_quantity;
        return 0; // Default order
      });
  }, [products, maxPrice, inStockOnly, sortBy]);

  return (
    <div className="space-y-8">
      {/* Top Banner with AI CTA */}
      <div className="bg-surface rounded-2xl border border-border p-6 sm:p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-xl space-y-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-accent">
            Authoritative Catalog
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">Performance Running Gear</h1>
          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Road runners, carbon race racers, moisture-wicking apparel, and hydration accessories backed by live warehouse stock.
          </p>
        </div>

        <Button
          variant="secondary"
          size="md"
          onClick={() => setIsAssistantOpen(true)}
          icon={<Bot className="w-4 h-4 text-accent" />}
          className="shrink-0 font-semibold"
        >
          Need Advice? Ask AI Assistant
        </Button>
      </div>

      {/* Filter, Search & Sorting Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search running shoes, apparel, socks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto justify-between sm:justify-end">
          {/* Mobile Filter Toggle Button */}
          <button
            onClick={() => setMobileFiltersOpen(!mobileFiltersOpen)}
            className="lg:hidden inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface border border-border text-xs font-medium text-text-dark hover:bg-surface-secondary cursor-pointer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Filters</span>
          </button>

          {/* Sort selector */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 text-text-muted hidden sm:inline" />
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="text-xs w-44"
            >
              <option value="featured">Featured SKUs</option>
              <option value="price-asc">Price: Low to High</option>
              <option value="price-desc">Price: High to Low</option>
              <option value="stock">Stock Availability</option>
            </Select>
          </div>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2.5 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 text-error" />
          <span>Failed to load storefront catalog: {error instanceof Error ? error.message : "Network error"}</span>
        </div>
      )}

      {/* Main Two Column Area: Filters & Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Desktop Sidebar Filters (3 cols) */}
        <div className="hidden lg:block lg:col-span-3 sticky top-24">
          <ProductFilters
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            maxPrice={maxPrice}
            onMaxPriceChange={setMaxPrice}
            inStockOnly={inStockOnly}
            onInStockToggle={setInStockOnly}
            onReset={handleReset}
          />
        </div>

        {/* Mobile Filter Drawer */}
        {mobileFiltersOpen && (
          <div className="lg:hidden col-span-1">
            <ProductFilters
              categories={categories}
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
              maxPrice={maxPrice}
              onMaxPriceChange={setMaxPrice}
              inStockOnly={inStockOnly}
              onInStockToggle={setInStockOnly}
              onReset={handleReset}
            />
          </div>
        )}

        {/* Products Grid (9 cols) */}
        <div className="lg:col-span-9 space-y-4">
          <div className="flex items-center justify-between text-xs text-text-muted px-1">
            <span>
              {isLoading
                ? "Loading products from backend..."
                : `Showing ${filteredProducts.length} verified products`}
            </span>
            {selectedCategory !== "all" && (
              <span className="font-semibold text-accent">Category: {selectedCategory}</span>
            )}
          </div>

          {isLoading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3 bg-surface rounded-2xl border border-border">
              <Loader2 className="w-6 h-6 animate-spin text-accent" />
              <p className="text-xs text-text-secondary">Connecting to live catalog...</p>
            </div>
          ) : (
            <ProductGrid products={filteredProducts} onResetFilters={handleReset} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ShopPage;
