import React, { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Save, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { ImageUpload } from "../ui/ImageUpload";

export const SkuForm: React.FC = () => {
  const { skuId } = useParams<{ skuId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const isEdit = Boolean(skuId);

  // Fetch product for edit mode
  const { data: productResponse, isLoading: loadingProduct } = useQuery({
    queryKey: ["admin-product", skuId],
    queryFn: () => apiClient.getAdminProductById(skuId!),
    enabled: isEdit,
  });

  const existingProduct = productResponse?.data;

  // Form State
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Running Shoes");
  const [priceInr, setPriceInr] = useState("4999.00");
  const [inventoryQuantity, setInventoryQuantity] = useState("25");
  const [shortDescription, setShortDescription] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [imageError, setImageError] = useState<string | null>(null);
  const [tagsString, setTagsString] = useState("running, gear, performance");
  const [active, setActive] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState(false);

  useEffect(() => {
    if (existingProduct) {
      setSku(existingProduct.sku);
      setName(existingProduct.name);
      setCategory(existingProduct.category);
      setPriceInr((existingProduct.price_paise / 100).toFixed(2));
      setInventoryQuantity(existingProduct.inventory_quantity.toString());
      setShortDescription(existingProduct.short_description);
      setDescription(existingProduct.description);
      setImageUrl(existingProduct.image_url);
      setTagsString(existingProduct.tags.join(", "));
      setActive(existingProduct.active);
    }
  }, [existingProduct]);

  // Mutation for creating or updating SKU
  const mutation = useMutation({
    mutationFn: async (payload: {
      sku: string;
      name: string;
      category: string;
      short_description: string;
      description: string;
      price_paise: number;
      inventory_quantity: number;
      image_url: string;
      tags: string[];
      attributes: Record<string, unknown>;
      active: boolean;
    }) => {
      if (isEdit && existingProduct) {
        return apiClient.updateAdminProduct(existingProduct.id, payload);
      } else {
        return apiClient.createAdminProduct(payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      queryClient.invalidateQueries({ queryKey: ["public-products"] });
      if (skuId) {
        queryClient.invalidateQueries({ queryKey: ["admin-product", skuId] });
      }
      setSuccessBanner(true);
      setTimeout(() => {
        navigate("/admin/catalog");
      }, 700);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to save SKU to database.";
      setErrorMessage(msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!imageUrl.trim()) {
      setImageError("Please upload a product image from your PC or provide an image URL.");
      return;
    }

    const pricePaise = Math.round(parseFloat(priceInr || "0") * 100);
    const qty = parseInt(inventoryQuantity || "0", 10);
    const tags = tagsString
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    mutation.mutate({
      sku: sku.trim(),
      name: name.trim(),
      category: category.trim(),
      price_paise: pricePaise,
      inventory_quantity: qty,
      short_description: shortDescription.trim(),
      description: description.trim(),
      image_url: imageUrl.trim(),
      tags,
      attributes: existingProduct?.attributes || { edition: "Standard", season: "2026" },
      active,
    });
  };

  if (isEdit && loadingProduct) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
        <p className="text-xs text-text-secondary">Loading SKU details from database...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/admin/catalog"
            className="p-2 rounded-xl bg-surface border border-border text-text-secondary hover:text-text-primary transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              {isEdit ? `Edit SKU: ${sku}` : "Add New Catalog SKU"}
            </h1>
            <p className="text-xs text-text-secondary">
              Product data saved here immediately updates the client storefront and agent discovery tools.
            </p>
          </div>
        </div>

        <Link to="/admin/catalog">
          <Button variant="outline" size="sm">
            Cancel
          </Button>
        </Link>
      </div>

      {successBanner && (
        <div className="p-4 rounded-xl bg-success-light border border-success/20 text-success-foreground flex items-center gap-2 text-xs font-semibold animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-success" />
          <span>SKU saved successfully to SQLite database! Redirecting to catalog...</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2.5 text-xs font-semibold animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-error shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="SKU Code"
            placeholder="e.g. RUN-X2-BLK-42"
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            required
            helperText="Unique merchant stock identifier"
          />

          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="Running Shoes">Running Shoes</option>
            <option value="Running Apparel">Running Apparel</option>
            <option value="Running Socks">Running Socks</option>
            <option value="Hydration & Accessories">Hydration & Accessories</option>
            <option value="Nutrition & Recovery">Nutrition & Recovery</option>
          </Select>
        </div>

        <Input
          label="Product Name"
          placeholder="e.g. RunPro X2 Road Runner"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Retail Price (INR ₹)"
            type="number"
            step="0.01"
            min="0"
            placeholder="4999.00"
            value={priceInr}
            onChange={(e) => setPriceInr(e.target.value)}
            required
            helperText="Authoritative checkout price"
          />

          <Input
            label="Available Inventory Quantity"
            type="number"
            min="0"
            placeholder="25"
            value={inventoryQuantity}
            onChange={(e) => setInventoryQuantity(e.target.value)}
            required
            helperText="Current warehouse physical stock"
          />
        </div>

        <ImageUpload
          label="Product Image"
          value={imageUrl}
          onChange={(url) => {
            setImageUrl(url);
            setImageError(null);
          }}
          error={imageError || undefined}
        />

        <Input
          label="Short Description"
          placeholder="One-line product summary for catalog cards"
          value={shortDescription}
          onChange={(e) => setShortDescription(e.target.value)}
          required
        />

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-text-dark">Full Product Description</label>
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Detailed technical specifications, foam materials, and drop metrics..."
            className="w-full bg-surface text-text-primary text-sm rounded-lg border border-border p-3 focus:outline-hidden focus:border-accent focus:ring-2 focus:ring-accent/20 transition placeholder:text-text-muted"
            required
          />
        </div>

        <Input
          label="Search & Recommendation Tags"
          placeholder="running, shoes, marathon, lightweight (comma separated)"
          value={tagsString}
          onChange={(e) => setTagsString(e.target.value)}
          helperText="Used by the in-app AI agent to match user constraints"
        />

        {/* Active Toggle */}
        <div className="pt-2 border-t border-border flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-text-primary block">Active Status</span>
            <span className="text-[11px] text-text-secondary">
              Inactive SKUs are hidden from the customer storefront and AI assistant.
            </span>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-surface-tertiary peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent border border-border"></div>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
          <Link to="/admin/catalog">
            <Button variant="outline" size="md">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={mutation.isPending}
            icon={<Save className="w-4 h-4" />}
          >
            {isEdit ? "Update SKU" : "Save & Publish SKU"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default SkuForm;
