import React from "react";
import type { Product } from "../../types/domain";
import ProductCard from "./ProductCard";
import { PackageSearch } from "lucide-react";
import { Button } from "../ui/Button";

export interface ProductGridProps {
  products: Product[];
  onResetFilters?: () => void;
}

export const ProductGrid: React.FC<ProductGridProps> = ({ products, onResetFilters }) => {
  if (products.length === 0) {
    return (
      <div className="bg-surface rounded-2xl border border-border p-12 text-center flex flex-col items-center justify-center">
        <div className="w-14 h-14 rounded-2xl bg-surface-secondary flex items-center justify-center text-text-muted mb-4 border border-border">
          <PackageSearch className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-text-primary">No running gear found</h3>
        <p className="text-xs text-text-secondary mt-1 max-w-sm">
          No catalog SKUs matched your current category, keyword, or price filter. Try loosening your search criteria.
        </p>
        {onResetFilters && (
          <div className="mt-5">
            <Button variant="outline" size="sm" onClick={onResetFilters}>
              Reset All Filters
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
};

export default ProductGrid;
