import React from "react";
import {
  Search,
  CheckCircle2,
  ShieldCheck,
  ShoppingBag,
  Loader2,
  PackageCheck,
  ReceiptText,
  AlertCircle,
} from "lucide-react";

export interface ToolActivityProps {
  activity: string;
  status: "running" | "completed" | "failed";
  details?: string;
}

export const ToolActivity: React.FC<ToolActivityProps> = ({
  activity,
  status,
  details,
}) => {
  const getIcon = () => {
    if (status === "running") {
      return <Loader2 className="w-3.5 h-3.5 animate-spin text-accent shrink-0" />;
    }
    if (status === "failed") {
      return <AlertCircle className="w-3.5 h-3.5 text-danger shrink-0" />;
    }
    const lower = activity.toLowerCase();
    if (lower.includes("search") || lower.includes("catalog")) {
      return <Search className="w-3.5 h-3.5 text-accent shrink-0" />;
    }
    if (lower.includes("inventory") || lower.includes("stock")) {
      return <PackageCheck className="w-3.5 h-3.5 text-success shrink-0" />;
    }
    if (lower.includes("cart")) {
      return <ShoppingBag className="w-3.5 h-3.5 text-success shrink-0" />;
    }
    if (lower.includes("quote") || lower.includes("price")) {
      return <ReceiptText className="w-3.5 h-3.5 text-accent shrink-0" />;
    }
    return <ShieldCheck className="w-3.5 h-3.5 text-success shrink-0" />;
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] my-0.5 transition ${
        status === "failed"
          ? "bg-danger-light/50 border-danger/30 text-danger"
          : "bg-surface-secondary border-border text-text-secondary hover:border-accent/40"
      }`}
      title={details || activity}
    >
      {getIcon()}
      <span className="font-mono text-text-dark max-w-[240px] truncate">{activity}</span>
      {status === "completed" && (
        <CheckCircle2 className="w-3 h-3 text-success ml-0.5 shrink-0" />
      )}
      {details && (
        <span className="text-[10px] text-text-muted hidden sm:inline border-l border-border pl-1.5 ml-0.5 max-w-[160px] truncate">
          {details}
        </span>
      )}
    </div>
  );
};

export default ToolActivity;
