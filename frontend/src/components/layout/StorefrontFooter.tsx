import React from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, ShieldCheck, Zap, Bot } from "lucide-react";

export const StorefrontFooter: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand Col */}
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center text-accent-foreground">
                <ShoppingBag className="w-4 h-4" />
              </div>
              <span className="font-bold text-base text-text-primary">RunCraft Athletics</span>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              Performance road & trail running equipment powered by an authoritative agentic commerce layer.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success-light px-2.5 py-0.5 rounded-full border border-success/20">
                <ShieldCheck className="w-3.5 h-3.5" /> Razorpay Secured
              </span>
            </div>
          </div>

          {/* Catalog Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Shop Categories</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/shop" className="text-text-secondary hover:text-text-primary transition">
                  Running Shoes
                </Link>
              </li>
              <li>
                <Link to="/shop" className="text-text-secondary hover:text-text-primary transition">
                  Technical Apparel
                </Link>
              </li>
              <li>
                <Link to="/shop" className="text-text-secondary hover:text-text-primary transition">
                  Hydration & Accessories
                </Link>
              </li>
              <li>
                <Link to="/shop" className="text-text-secondary hover:text-text-primary transition">
                  Nutrition & Recovery
                </Link>
              </li>
            </ul>
          </div>

          {/* AI Shopping */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Agentic Platform</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/assistant" className="text-accent hover:text-accent-dark font-medium transition inline-flex items-center gap-1">
                  <Bot className="w-3.5 h-3.5" /> AI Shopping Assistant
                </Link>
              </li>
              <li>
                <Link to="/cart" className="text-text-secondary hover:text-text-primary transition">
                  Active Cart & Quote
                </Link>
              </li>
              <li>
                <Link to="/orders" className="text-text-secondary hover:text-text-primary transition">
                  Order Status & Tracking
                </Link>
              </li>
              <li>
                <Link to="/admin/dashboard" className="text-text-secondary hover:text-text-primary transition">
                  Merchant Control Center
                </Link>
              </li>
            </ul>
          </div>

          {/* Architecture Guarantee */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Commerce Guarantee</h4>
            <div className="bg-surface-secondary border border-border rounded-xl p-3.5 space-y-2 text-xs">
              <div className="flex items-start gap-2">
                <Zap className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                <p className="text-text-secondary text-[11px] leading-tight">
                  <strong className="text-text-primary">Authoritative Layer:</strong> Live inventory and policy checks protect every quote.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-success shrink-0 mt-0.5" />
                <p className="text-text-secondary text-[11px] leading-tight">
                  <strong className="text-text-primary">Explicit Approval:</strong> No payment happens without your deliberate authorization.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between text-xs text-text-secondary gap-3">
          <p>© 2026 RunCraft Athletics Inc. • Agentic Commerce MVP Hackathon Build</p>
          <div className="flex items-center gap-4 text-[11px]">
            <span>FastAPI Backend</span>
            <span>•</span>
            <span>SQLite Persistence</span>
            <span>•</span>
            <span>Razorpay Test Mode</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default StorefrontFooter;
