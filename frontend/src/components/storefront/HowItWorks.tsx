import React from "react";
import { MessageSquare, Calculator, ShieldCheck } from "lucide-react";

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: "01",
      icon: <MessageSquare className="w-5 h-5 text-accent" />,
      title: "Tell Us What You Need",
      description:
        "Tell Pace your running goals or target budget — like 'Build a 10K running kit under ₹8,000'. We find gear that matches your exact training routine.",
    },
    {
      step: "02",
      icon: <Calculator className="w-5 h-5 text-accent" />,
      title: "Verified Price & Stock",
      description:
        "Every recommendation checks real-time warehouse inventory and active promotions, giving you an exact, verified total with zero hidden costs.",
    },
    {
      step: "03",
      icon: <ShieldCheck className="w-5 h-5 text-accent" />,
      title: "You're Always in Control",
      description:
        "Your order is never placed without your explicit approval. Review your complete item breakdown and pay securely via Razorpay.",
    },
  ];

  return (
    <section className="py-14 border-t border-border">
      <div className="text-center max-w-2xl mx-auto mb-12">
        <span className="text-xs font-semibold uppercase tracking-wider text-accent">
          How It Works
        </span>
        <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mt-1">
          Simple, Transparent & Fast Shopping
        </h2>
        <p className="text-xs sm:text-sm text-text-secondary mt-2">
          Personalized running recommendations backed by real-time inventory and customer-approved checkout.
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
              Live Warehouse Verified
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
