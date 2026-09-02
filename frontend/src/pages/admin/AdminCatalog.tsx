import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Edit2, Trash2, Eye, Loader2, AlertCircle } from "lucide-react";
import { apiClient, resolveImageUrl } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";

export const AdminCatalog: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");

  // TanStack Query for authoritative backend products
  const {
    data: response,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin-products", searchQuery, categoryFilter],
    queryFn: () =>
      apiClient.getAdminProducts({
        q: searchQuery || undefined,
        category: categoryFilter !== "all" ? categoryFilter : undefined,
        active_only: false,
      }),
  });

  const products = response?.data || [];

  // TanStack Mutation for soft deletion / deactivation
  const deleteMutation = useMutation({
    mutationFn: (productId: string) => apiClient.deleteAdminProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      queryClient.invalidateQueries({ queryKey: ["public-products"] });
    },
  });

  // Extract unique categories from current products or standard list
  const standardCategories = [
    "Running Shoes",
    "Running Apparel",
    "Running Socks",
    "Hydration & Accessories",
    "Nutrition & Recovery",
  ];
  const dynamicCategories = Array.from(new Set(products.map((p) => p.category)));
  const allCategories = Array.from(new Set([...standardCategories, ...dynamicCategories]));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Catalog & Inventory</h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Authoritative SKU catalog synced directly with in-app AI assistant and MCP channel.
          </p>
        </div>

        <Link to="/admin/catalog/new">
          <Button variant="primary" size="md" icon={<Plus className="w-4 h-4" />}>
            Add New SKU
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface rounded-2xl border border-border p-4 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search by SKU code or product name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="w-full sm:w-56">
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="all">All Categories</option>
            {allCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </Select>
        </div>

        <div className="text-xs text-text-muted sm:ml-auto">
          {isLoading ? "Loading SKUs..." : `Showing ${products.length} SKUs`}
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2.5 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 text-error" />
          <span>Error loading catalog: {error instanceof Error ? error.message : "Failed to fetch products"}</span>
        </div>
      )}

      {/* Catalog Table */}
      <div className="bg-surface rounded-2xl border border-border shadow-xs overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Product Name</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Price (INR)</TableHead>
              <TableHead>Stock Level</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12 text-text-secondary">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-accent" />
                    <span className="text-xs">Fetching authoritative catalog from SQLite...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : products.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12 text-text-secondary">
                  No SKUs matched your search criteria.
                </TableCell>
              </TableRow>
            ) : (
              products.map((p) => {
                const isLowStock = p.inventory_quantity <= 15 && p.inventory_quantity > 0;
                const isOutOfStock = p.inventory_quantity === 0;
                const imageUrl = resolveImageUrl(p.image_url);

                return (
                  <TableRow key={p.id}>
                    <TableCell className="font-mono text-xs font-semibold text-text-primary">
                      {p.sku}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <img
                          src={imageUrl}
                          alt={p.name}
                          className="w-9 h-9 rounded-lg object-cover bg-surface-tertiary shrink-0 border border-border"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src =
                              "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60";
                          }}
                        />
                        <div className="min-w-0">
                          <p className="font-bold text-xs text-text-primary truncate max-w-xs">{p.name}</p>
                          <p className="text-[11px] text-text-secondary truncate max-w-xs">{p.short_description}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-text-dark font-medium">{p.category}</TableCell>
                    <TableCell className="font-bold text-xs text-text-primary">
                      ₹{(p.price_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      <Badge variant={isOutOfStock ? "error" : isLowStock ? "warning" : "success"}>
                        {isOutOfStock ? "Out of stock" : isLowStock ? `Low (${p.inventory_quantity})` : `${p.inventory_quantity} in stock`}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={p.active ? "success" : "neutral"}>
                        {p.active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-[11px] text-text-muted font-mono">
                      {new Date(p.updated_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          to={`/product/${p.id}`}
                          target="_blank"
                          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition"
                          title="View on Storefront"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Link>
                        <Link
                          to={`/admin/catalog/${p.id}/edit`}
                          className="p-1.5 rounded-lg text-text-muted hover:text-accent hover:bg-surface-secondary transition"
                          title="Edit SKU"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Link>
                        <button
                          onClick={() => {
                            if (confirm(`Are you sure you want to deactivate SKU ${p.sku}? It will be hidden from the customer storefront.`)) {
                              deleteMutation.mutate(p.id);
                            }
                          }}
                          disabled={deleteMutation.isPending}
                          className="p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error-light transition cursor-pointer disabled:opacity-50"
                          title="Deactivate SKU (Soft Delete)"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default AdminCatalog;
