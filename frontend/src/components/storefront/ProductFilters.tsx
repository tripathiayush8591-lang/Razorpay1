import { Filter, RotateCcw } from "lucide-react";

export interface ProductFiltersProps {
  categories: string[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  maxPrice: number;
  onMaxPriceChange: (price: number) => void;
  inStockOnly: boolean;
  onInStockToggle: (checked: boolean) => void;
  onReset: () => void;
}

export const ProductFilters: React.FC<ProductFiltersProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  maxPrice,
  onMaxPriceChange,
  inStockOnly,
  onInStockToggle,
  onReset,
}) => {
  return (
    <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Catalog Filters</h3>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1 text-[11px] text-text-muted hover:text-accent transition cursor-pointer"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Category Filter */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-text-dark block">Categories</label>
        <div className="space-y-1">
          <button
            onClick={() => onSelectCategory("all")}
            className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
              selectedCategory === "all"
                ? "bg-accent-light text-accent-dark font-semibold"
                : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
            }`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                selectedCategory === cat
                  ? "bg-accent-light text-accent-dark font-semibold"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div className="space-y-2 pt-2 border-t border-border">
        <div className="flex items-center justify-between text-xs">
          <label className="font-semibold text-text-dark">Max Budget</label>
          <span className="font-bold text-accent">₹{maxPrice.toLocaleString("en-IN")}</span>
        </div>
        <input
          type="range"
          min="500"
          max="16000"
          step="500"
          value={maxPrice}
          onChange={(e) => onMaxPriceChange(Number(e.target.value))}
          className="w-full accent-accent cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-text-muted font-mono">
          <span>₹500</span>
          <span>₹16,000</span>
        </div>
      </div>

      {/* Stock Availability */}
      <div className="pt-2 border-t border-border">
        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-xs font-semibold text-text-dark">In Stock Only</span>
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(e) => onInStockToggle(e.target.checked)}
            className="rounded border-border text-accent focus:ring-accent accent-accent cursor-pointer"
          />
        </label>
      </div>
    </div>
  );
};

export default ProductFilters;
