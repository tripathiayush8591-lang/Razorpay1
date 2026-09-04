import React from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, ShieldCheck } from "lucide-react";

export const StorefrontFooter: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand & Tagline */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-accent-foreground">
              <ShoppingBag className="w-3.5 h-3.5" />
            </div>
            <div className="flex items-center">
              <span className="font-bold text-sm text-text-primary tracking-tight">RunCraft Athletics</span>
              <span className="hidden sm:inline-block text-text-muted text-xs mx-2">|</span>
              <span className="hidden sm:inline-block text-xs text-text-secondary">Precision Running Gear & AI Commerce</span>
            </div>
          </div>

          {/* Minimal Navigation */}
          <nav className="flex flex-wrap items-center justify-center gap-5 text-xs text-text-secondary">
            <Link to="/shop" className="hover:text-text-primary transition">
              Shop Catalog
            </Link>
            <Link to="/orders" className="hover:text-text-primary transition">
              Track Orders
            </Link>
            <Link to="/external-buyer" className="hover:text-text-primary transition">
              External AI (MCP)
            </Link>
            <Link to="/admin/dashboard" className="hover:text-text-primary transition">
              Merchant Portal
            </Link>
          </nav>

          {/* Trust Badge */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-success bg-success-light px-2.5 py-0.5 rounded-full border border-success/20">
              <ShieldCheck className="w-3.5 h-3.5" /> Razorpay Secured
            </span>
          </div>
        </div>

        {/* Minimal Bottom Info */}
        <div className="mt-6 pt-4 border-t border-border/60 flex flex-col sm:flex-row items-center justify-between text-[11px] text-text-muted gap-2">
          <p>© {new Date().getFullYear()} RunCraft Athletics Inc. All rights reserved.</p>
          <div className="flex items-center gap-3">
            <span>Fast Courier Delivery Across India</span>
            <span>•</span>
            <span>support@runcraft.internal</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default StorefrontFooter;

