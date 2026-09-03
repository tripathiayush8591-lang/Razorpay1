import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ShoppingBag, Sparkles, Shield, Compass, Search, Bot } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";

export const StorefrontHeader: React.FC = () => {
  const { cartCount, setIsCartOpen } = useMockCommerce();
  const location = useLocation();

  const navLinks = [
    { label: "Shop", path: "/shop", icon: <Compass className="w-4 h-4" /> },
    { label: "AI Assistant", path: "/assistant", icon: <Sparkles className="w-4 h-4 text-accent" /> },
    { label: "AI Buyer (MCP)", path: "/external-buyer", icon: <Bot className="w-4 h-4 text-accent" /> },
    { label: "Track Orders", path: "/orders" },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-surface/90 backdrop-blur-md border-b border-border shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center text-accent-foreground shadow-xs group-hover:bg-accent-dark transition">
              <ShoppingBag className="w-4.5 h-4.5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-text-primary group-hover:text-accent transition">
                RunCraft
              </span>
              <span className="text-xs text-text-secondary font-medium ml-1.5 hidden sm:inline">
                Athletics
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    isActive
                      ? "bg-accent-light text-accent-dark"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
                  }`}
                >
                  {link.icon}
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Subtle Demo Merchant Switch */}
          <Link
            to="/admin/dashboard"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-secondary hover:bg-surface-tertiary border border-border text-xs font-medium text-text-secondary hover:text-text-primary transition"
            title="Open Merchant Operations Portal"
          >
            <Shield className="w-3.5 h-3.5 text-text-muted" />
            <span className="hidden sm:inline">Merchant Portal</span>
            <span className="sm:hidden">Admin</span>
          </Link>

          {/* Search Trigger */}
          <Link
            to="/shop"
            className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition"
            aria-label="Search catalog"
          >
            <Search className="w-4 h-4" />
          </Link>

          {/* Cart Icon & Counter */}
          <button
            onClick={() => setIsCartOpen(true)}
            className="relative inline-flex items-center justify-center p-2 rounded-lg text-text-primary hover:bg-surface-secondary border border-border/80 transition cursor-pointer"
            aria-label="Open Cart"
          >
            <ShoppingBag className="w-4.5 h-4.5" />
            {cartCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 bg-accent text-accent-foreground text-[10px] font-bold w-4.5 h-4.5 rounded-full flex items-center justify-center shadow-xs animate-in zoom-in-50 duration-200">
                {cartCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

export default StorefrontHeader;
