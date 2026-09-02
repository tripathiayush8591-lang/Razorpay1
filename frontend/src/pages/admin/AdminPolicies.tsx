import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Save,
  CheckCircle2,
  ShieldCheck,
  Truck,
  Percent,
  ShoppingBag,
  Plus,
  Trash2,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import type { CrossSellRule } from "@/types/domain";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

export const AdminPolicies: React.FC = () => {
  const queryClient = useQueryClient();

  // Fetch authoritative merchant policies from SQLite
  const {
    data: response,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin-policies"],
    queryFn: () => apiClient.getAdminPolicies(),
  });

  const policy = response?.data;

  // Form states
  const [maxDiscount, setMaxDiscount] = useState("15");
  const [allowOutOfStock, setAllowOutOfStock] = useState(false);
  const [requireApproval, setRequireApproval] = useState(true);
  const [freeDeliveryThreshold, setFreeDeliveryThreshold] = useState("2000.00");
  const [standardDeliveryFee, setStandardDeliveryFee] = useState("150.00");
  const [crossSellRules, setCrossSellRules] = useState<CrossSellRule[]>([]);

  // New Cross-Sell Rule inline form state
  const [newTrigger, setNewTrigger] = useState("Running Shoes");
  const [newRecommend, setNewRecommend] = useState("Running Socks");
  const [newReason, setNewReason] = useState("");

  const [successBanner, setSuccessBanner] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync initial query data into local state
  useEffect(() => {
    if (policy) {
      setMaxDiscount(policy.max_discount_percent.toString());
      setAllowOutOfStock(policy.allow_out_of_stock);
      setRequireApproval(policy.require_purchase_approval);
      setFreeDeliveryThreshold((policy.delivery_rules.free_delivery_threshold_paise / 100).toFixed(2));
      setStandardDeliveryFee((policy.delivery_rules.standard_delivery_paise / 100).toFixed(2));
      setCrossSellRules(policy.cross_sell_rules || []);
    }
  }, [policy]);

  // Mutation for updating policies
  const mutation = useMutation({
    mutationFn: async () => {
      const thresholdPaise = Math.round(parseFloat(freeDeliveryThreshold || "0") * 100);
      const deliveryFeePaise = Math.round(parseFloat(standardDeliveryFee || "0") * 100);
      const discountPercent = parseInt(maxDiscount || "15", 10);

      return apiClient.updateAdminPolicies({
        max_discount_percent: discountPercent,
        allow_out_of_stock: allowOutOfStock,
        require_purchase_approval: requireApproval,
        cross_sell_rules: crossSellRules,
        delivery_rules: {
          free_delivery_threshold_paise: thresholdPaise,
          standard_delivery_paise: deliveryFeePaise,
          express_delivery_paise: policy?.delivery_rules?.express_delivery_paise ?? 35000,
          estimated_days_standard: policy?.delivery_rules?.estimated_days_standard ?? 3,
          estimated_days_express: policy?.delivery_rules?.estimated_days_express ?? 1,
        },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-policies"] });
      setSuccessBanner(true);
      setTimeout(() => setSuccessBanner(false), 4000);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to update merchant policies";
      setErrorMessage(msg);
    },
  });

  const handleAddCrossSellRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTrigger || !newRecommend) return;

    const rule: CrossSellRule = {
      trigger_category: newTrigger.trim(),
      recommend_category: newRecommend.trim(),
      reason: newReason.trim() || `Shoppers purchasing ${newTrigger} frequently add ${newRecommend}`,
    };

    setCrossSellRules((prev) => [...prev, rule]);
    setNewReason("");
  };

  const handleRemoveCrossSellRule = (index: number) => {
    setCrossSellRules((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    mutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
        <p className="text-xs text-text-secondary">Loading authoritative policies from SQLite...</p>
      </div>
    );
  }

  const categoryOptions = [
    "Running Shoes",
    "Running Apparel",
    "Running Socks",
    "Hydration & Accessories",
    "Nutrition & Recovery",
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Merchant Selling Policies</h1>
        <p className="text-xs text-text-secondary mt-0.5">
          Authoritative business guardrails enforced during AI agent tool executions and quote calculations.
        </p>
      </div>

      {successBanner && (
        <div className="p-4 rounded-xl bg-success-light border border-success/20 text-success-foreground flex items-center gap-2 text-xs font-semibold animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-success" />
          <span>Policies successfully updated and persisted to SQLite! All quote and agent services now enforce these rules.</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2 text-xs font-semibold animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-error" />
          <span>{errorMessage}</span>
        </div>
      )}

      {isError && (
        <div className="p-4 rounded-xl bg-error-light border border-error/20 text-error-foreground flex items-center gap-2 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 text-error" />
          <span>Failed to load policies: {error instanceof Error ? error.message : "Network error"}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Guardrails Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-lg bg-accent-light text-accent-dark flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-text-primary">Agent Autonomy Guardrails</h2>
              <p className="text-[11px] text-text-secondary">Mandatory safety checks enforced before customer payments</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Approval Requirement */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-surface-secondary border border-border">
              <div className="space-y-0.5 pr-4">
                <span className="text-xs font-bold text-text-primary block">
                  Require Explicit Purchase Approval
                </span>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  When enabled, the AI shopping agent stops before any payment step until the shopper explicitly clicks the Approval Card.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={requireApproval}
                  onChange={(e) => setRequireApproval(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-surface-tertiary peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent border border-border"></div>
              </label>
            </div>

            {/* Out of stock rule */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-surface-secondary border border-border">
              <div className="space-y-0.5 pr-4">
                <span className="text-xs font-bold text-text-primary block">
                  Allow Selling Out-of-Stock SKUs (Backorders)
                </span>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  When disabled, final quotes fail validation if requested item quantity exceeds warehouse inventory.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={allowOutOfStock}
                  onChange={(e) => setAllowOutOfStock(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-surface-tertiary peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent border border-border"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Pricing & Discounts Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-lg bg-warning-light text-warning flex items-center justify-center">
              <Percent className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-text-primary">Discount & Margin Boundaries</h2>
              <p className="text-[11px] text-text-secondary">Caps maximum discount the agent is allowed to apply</p>
            </div>
          </div>

          <div className="max-w-xs">
            <Input
              label="Maximum Agent Discount (%)"
              type="number"
              min="0"
              max="50"
              value={maxDiscount}
              onChange={(e) => setMaxDiscount(e.target.value)}
              helperText="Agent cannot offer discounts exceeding this ceiling"
              required
            />
          </div>
        </div>

        {/* Delivery Rules Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-lg bg-info-light text-info-foreground flex items-center justify-center">
              <Truck className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-text-primary">Delivery Fee Configuration</h2>
              <p className="text-[11px] text-text-secondary">Determines free shipping thresholds and standard freight rates</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Free Delivery Threshold (INR ₹)"
              type="number"
              min="0"
              value={freeDeliveryThreshold}
              onChange={(e) => setFreeDeliveryThreshold(e.target.value)}
              helperText="Orders above this amount qualify for zero freight"
              required
            />

            <Input
              label="Standard Shipping Rate (INR ₹)"
              type="number"
              min="0"
              value={standardDeliveryFee}
              onChange={(e) => setStandardDeliveryFee(e.target.value)}
              helperText="Fee charged for orders below threshold"
              required
            />
          </div>
        </div>

        {/* Cross-Sell Rules (Editable) */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-lg bg-accent-light text-accent-dark flex items-center justify-center">
              <ShoppingBag className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-text-primary">Configured Cross-Sell Pairings</h2>
              <p className="text-[11px] text-text-secondary">Categories automatically recommended during AI kit assembly</p>
            </div>
          </div>

          {/* Current Rules List */}
          <div className="space-y-3">
            {crossSellRules.length === 0 ? (
              <p className="text-xs text-text-muted py-2 italic">No cross-sell pairings configured yet.</p>
            ) : (
              crossSellRules.map((rule, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-surface-secondary border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2 text-xs font-bold text-text-primary">
                      <span className="text-accent">{rule.trigger_category}</span>
                      <span>→</span>
                      <span className="text-success">{rule.recommend_category}</span>
                    </div>
                    <p className="text-[11px] text-text-secondary">{rule.reason}</p>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveCrossSellRule(idx)}
                    className="p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error-light transition self-start sm:self-auto cursor-pointer"
                    title="Remove Rule"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Add New Pairing Sub-Form */}
          <div className="pt-4 border-t border-border space-y-3">
            <h3 className="text-xs font-bold text-text-primary">Add New Cross-Sell Pairing</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Select
                label="Trigger Category (When shopper buys)"
                value={newTrigger}
                onChange={(e) => setNewTrigger(e.target.value)}
              >
                {categoryOptions.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>

              <Select
                label="Recommend Category (Agent suggests)"
                value={newRecommend}
                onChange={(e) => setNewRecommend(e.target.value)}
              >
                {categoryOptions.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </div>

            <Input
              label="Recommendation Reason"
              placeholder="e.g. Runners pairing road shoes need blister-prevention socks"
              value={newReason}
              onChange={(e) => setNewReason(e.target.value)}
              helperText="Brief explanation used by the agent during conversation"
            />

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddCrossSellRule}
              icon={<Plus className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Add Pairing Rule
            </Button>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={mutation.isPending}
            icon={<Save className="w-4 h-4" />}
          >
            Save Policy Settings
          </Button>
        </div>
      </form>
    </div>
  );
};

export default AdminPolicies;
