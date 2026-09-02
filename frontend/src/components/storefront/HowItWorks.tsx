import React from "react";
import { MessageSquare, Calculator, ShieldCheck } from "lucide-react";

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: "01",
      icon: <MessageSquare className="w-5 h-5 text-accent" />,
      title: "State Your Goal & Constraints",
      description:
        "Prompt the agent naturally — 'Build a marathon kit under ₹8,000'. The agent reasons over your request without hallucinating fake items.",
    },
    {
      step: "02",
      icon: <Calculator className="w-5 h-5 text-accent" />,
      title: "Authoritative Quote Generation",
      description:
        "The commerce layer validates real SQLite warehouse stock, applies merchant discount policies, and produces a mathematically binding quote.",
    },
    {
      step: "03",
      icon: <ShieldCheck className="w-5 h-5 text-accent" />,
      title: "Explicit Consent & Payment",
      description:
        "No money or checkout order is generated without your explicit one-click approval. Completed instantly via Razorpay Test Mode.",
    },
  ];

  return (
    <section className="py-14 border-t border-border">
      <div className="text-center max-w-2xl mx-auto mb-12">
        <span className="text-xs font-semibold uppercase tracking-wider text-accent">
          Architecture in Motion
        </span>
        <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mt-1">
          How Agentic Shopping Actually Works
        </h2>
        <p className="text-xs sm:text-sm text-text-secondary mt-2">
          Agents decide what to do. The commerce layer decides what is true and what is allowed.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {steps.map((item) => (
          <div
            key={item.step}
            className="bg-surface rounded-2xl border border-border p-6 shadow-xs relative flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-accent-light flex items-center justify-center">
                  {item.icon}
                </div>
                <span className="font-mono text-xs font-extrabold text-accent bg-surface-secondary px-2.5 py-1 rounded-full border border-border">
                  {item.step}
                </span>
              </div>
              <h3 className="text-base font-bold text-text-primary mb-2">{item.title}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{item.description}</p>
            </div>

            <div className="mt-6 pt-4 border-t border-border text-[11px] font-medium text-text-muted">
              FastAPI Commerce Service Verified
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
