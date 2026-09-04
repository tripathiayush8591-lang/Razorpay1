import React from "react";
import { ShieldCheck, Lock, Database, Cpu } from "lucide-react";

export const TrustSection: React.FC = () => {
  const pillars = [
    {
      icon: <Database className="w-5 h-5 text-accent" />,
      title: "Accurate Pricing & Real Stock",
      description:
        "What you see is what is in our warehouse. Real-time inventory checks ensure you never pay for an out-of-stock product.",
    },
    {
      icon: <Lock className="w-5 h-5 text-success" />,
      title: "You Approve Before You Pay",
      description:
        "No surprise charges. You always review and approve your complete item list and delivery details before any payment.",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-info" />,
      title: "Secure, Verified Checkout",
      description:
        "Fast, reliable payments powered by Razorpay with instant order confirmation and live shipment tracking.",
    },
    {
      icon: <Cpu className="w-5 h-5 text-warning" />,
      title: "Shop Your Way",
      description:
        "Browse our catalog normally, build kits with Pace, or connect via AI shopping assistants with consistent pricing across all channels.",
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
            Why Runners Trust RunCraft
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary mt-2">
            Modern performance running equipment backed by real-time inventory, transparent pricing, and shopper-first checkout.
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
