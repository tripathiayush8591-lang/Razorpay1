import React from "react";
import { Link } from "react-router-dom";
import { Sparkles, ArrowRight, ShieldCheck, Zap, Bot, CheckCircle2 } from "lucide-react";
import { Button } from "../ui/Button";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";

export const Hero: React.FC = () => {
  const { setIsAssistantOpen } = useMockCommerce();

  return (
    <section className="relative overflow-hidden py-10 md:py-16">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        {/* Left Column: Headline & Value Prop */}
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-light text-accent-dark text-xs font-semibold border border-accent/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agentic Commerce Architecture • 2026 Edition</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-5xl font-extrabold text-text-primary tracking-tight leading-[1.15]">
            The Performance Running Store That <span className="text-accent">Thinks With You</span>.
          </h1>

          <p className="text-sm sm:text-base text-text-secondary leading-relaxed max-w-xl">
            Tell our in-app shopping agent your goals, split times, or budget. 
            It queries our live SQLite warehouse, enforces merchant discount policies, and builds an authoritative quote ready for your one-click approval.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button
              variant="primary"
              size="lg"
              onClick={() => setIsAssistantOpen(true)}
              icon={<Bot className="w-5 h-5" />}
              className="font-semibold shadow-sm"
            >
              Shop with AI Assistant
            </Button>

            <Link to="/shop">
              <Button variant="outline" size="lg" className="font-semibold">
                <span>Browse Full Catalog</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          {/* Trust Highlights */}
          <div className="pt-4 grid grid-cols-3 gap-4 border-t border-border max-w-lg">
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-text-primary flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-accent" /> Live Stock
              </div>
              <p className="text-[11px] text-text-secondary">Authoritative inventory check</p>
            </div>
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-text-primary flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-success" /> User Consent
              </div>
              <p className="text-[11px] text-text-secondary">No payment without approval</p>
            </div>
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-text-primary flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-info" /> Test Mode
              </div>
              <p className="text-[11px] text-text-secondary">Razorpay verified checkout</p>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive AI Kit Mock Card */}
        <div className="lg:col-span-5 relative">
          <div className="relative bg-surface rounded-2xl border border-border p-5 shadow-lg space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-accent-foreground">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs font-bold text-text-primary block">AI Kit Recommendation</span>
                  <span className="text-[10px] text-text-secondary">Generated for: "Beginner 10K Runner"</span>
                </div>
              </div>
              <span className="text-[10px] font-medium bg-success-light text-success px-2 py-0.5 rounded-full border border-success/20">
                In Stock & Validated
              </span>
            </div>

            {/* Simulated Chat Dialogue */}
            <div className="space-y-2.5 text-xs">
              <div className="p-2.5 rounded-xl bg-surface-secondary text-text-primary text-[11px] leading-relaxed border border-border">
                <span className="font-semibold text-accent block mb-0.5">Commerce Agent:</span>
                I've assembled a training setup under ₹8,000 using our top-rated cushioned shoes and anti-friction socks.
              </div>

              {/* Miniature Product Rows */}
              <div className="space-y-2">
                <div className="flex items-center gap-2.5 p-2 rounded-lg bg-surface-tertiary border border-border">
                  <img
                    src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200&auto=format&fit=crop&q=60"
                    alt="RunPro X2"
                    className="w-10 h-10 object-cover rounded-md"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-text-primary truncate">RunPro X2 Road Runner</p>
                    <p className="text-[10px] text-text-secondary">Size 42 EU • Road Training</p>
                  </div>
                  <span className="text-xs font-bold text-text-primary">₹5,499</span>
                </div>

                <div className="flex items-center gap-2.5 p-2 rounded-lg bg-surface-tertiary border border-border">
                  <img
                    src="https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=200&auto=format&fit=crop&q=60"
                    alt="FleetStride Socks"
                    className="w-10 h-10 object-cover rounded-md"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-text-primary truncate">FleetStride Socks (3-Pack)</p>
                    <p className="text-[10px] text-text-secondary">Anti-Blister Arch Support</p>
                  </div>
                  <span className="text-xs font-bold text-text-primary">₹699</span>
                </div>
              </div>

              {/* Authoritative Quote Pill */}
              <div className="p-3 rounded-xl bg-accent-muted border border-accent/20 flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold text-accent-dark tracking-wider block">
                    Authoritative Total
                  </span>
                  <span className="text-sm font-extrabold text-text-primary">₹6,198.00</span>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsAssistantOpen(true)}
                  className="text-xs"
                >
                  Inspect Quote
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
