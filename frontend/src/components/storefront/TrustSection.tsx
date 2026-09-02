import React from "react";
import { ShieldCheck, Lock, Database, Cpu } from "lucide-react";

export const TrustSection: React.FC = () => {
  const pillars = [
    {
      icon: <Database className="w-5 h-5 text-accent" />,
      title: "Zero LLM Hallucination on Price & Stock",
      description:
        "The model never invents inventory or discounts. Every SKU, quantity, and rupee total originates from our authoritative SQLite database.",
    },
    {
      icon: <Lock className="w-5 h-5 text-success" />,
      title: "Human Approval Required Before Charging",
      description:
        "AI agents cannot autonomously charge cards. Shoppers inspect an immutable final quote and explicitly authorize payment.",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-info" />,
      title: "Razorpay Test Mode Payment Pipeline",
      description:
        "Payments are verified server-side with HMAC-SHA256 signature verification and idempotent webhook handlers to prevent duplicate orders.",
    },
    {
      icon: <Cpu className="w-5 h-5 text-warning" />,
      title: "Universal MCP Adapter Parity",
      description:
        "External AI Buyers connecting through MCP use the exact same commerce services and quote rules as human shoppers in the storefront.",
    },
  ];

  return (
    <section className="py-14 border-t border-border">
      <div className="bg-surface rounded-2xl border border-border p-8 sm:p-10 shadow-xs">
        <div className="max-w-2xl mb-10">
          <span className="text-xs font-semibold uppercase tracking-wider text-accent">
            Built for Real-World Trust
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mt-1">
            Why Agentic Commerce Requires Guardrails
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary mt-2">
            Most AI commerce demos fall apart when prices change or stocks run out. 
            RunCraft uses a decoupled architecture where backend rules govern every transaction.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pillars.map((pillar, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl bg-surface-secondary border border-border flex items-start gap-4"
            >
              <div className="p-2.5 rounded-lg bg-surface border border-border shrink-0 shadow-2xs">
                {pillar.icon}
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-text-primary">{pillar.title}</h4>
                <p className="text-xs text-text-secondary leading-relaxed">{pillar.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TrustSection;
