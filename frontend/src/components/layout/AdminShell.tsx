import React, { useState } from "react";
import { Link, useLocation, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ShoppingBag,
  Sliders,
  Network,
  Menu,
  X,
  ExternalLink,
  LogOut,
  Shield,
} from "lucide-react";
import { useAdminAuth } from "../../lib/auth/AdminAuthContext";

export const AdminShell: React.FC = () => {
  const { admin, logout } = useAdminAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { label: "Overview", path: "/admin/dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: "Catalog", path: "/admin/catalog", icon: <Package className="w-4 h-4" /> },
    { label: "Orders", path: "/admin/orders", icon: <ShoppingBag className="w-4 h-4" /> },
    { label: "Agent Policies", path: "/admin/policies", icon: <Sliders className="w-4 h-4" /> },
    { label: "Channels & MCP", path: "/admin/channels", icon: <Network className="w-4 h-4" /> },
  ];

  const SidebarContent = () => (
    <div className="h-full flex flex-col justify-between bg-surface border-r border-border select-none">
      {/* Top Brand */}
      <div>
        <div className="h-16 px-6 border-b border-border flex items-center justify-between">
          <Link to="/admin/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center text-accent-foreground shadow-2xs">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-sm text-text-primary block leading-tight">
                RunCraft
              </span>
              <span className="text-[10px] text-accent font-semibold tracking-wider uppercase">
                Merchant Admin
              </span>
            </div>
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition cursor-pointer"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path !== "/admin/dashboard" && location.pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? "bg-accent-light text-accent-dark"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
                }`}
              >
                <span className={isActive ? "text-accent-dark" : "text-text-muted"}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Quick Exit */}
      <div className="p-4 border-t border-border space-y-3 bg-surface-secondary/40">
        {/* User Card */}
        <div className="px-2 py-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-primary capitalize">{admin?.role || "Demo Admin"}</span>
            <span className="text-[10px] font-semibold text-success bg-success-light px-1.5 py-0.2 rounded-full border border-success/20">
              Active
            </span>
          </div>
          <p className="text-[11px] text-text-secondary truncate mt-0.5">
            {admin?.email || "admin@runcraft.internal"}
          </p>
        </div>

        {/* Links */}
        <div className="pt-2 border-t border-border space-y-1 text-xs">
          <Link
            to="/"
            className="flex items-center justify-between px-2 py-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition"
          >
            <span className="flex items-center gap-2">
              <ExternalLink className="w-3.5 h-3.5 text-text-muted" />
              <span>View Storefront</span>
            </span>
            <span className="text-[10px] text-accent font-medium">Live</span>
          </Link>

          <button
            onClick={() => logout()}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-error hover:bg-error-light transition cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col lg:flex-row antialiased">
      {/* Desktop Fixed Sidebar */}
      <aside className="hidden lg:block w-60 shrink-0 h-screen sticky top-0 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile Header Bar */}
      <div className="lg:hidden h-14 bg-surface border-b border-border px-4 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-accent-foreground">
            <Shield className="w-4 h-4" />
          </div>
          <span className="font-bold text-sm text-text-primary">RunCraft Admin</span>
        </div>
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition cursor-pointer"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Drawer Backdrop & Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden overflow-hidden">
          <div
            className="fixed inset-0 bg-text-primary/40 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <div className="fixed inset-y-0 left-0 max-w-full flex">
            <div className="w-64 bg-surface shadow-2xl">
              <SidebarContent />
            </div>
          </div>
        </div>
      )}

      {/* Main Admin Content Area */}
      <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminShell;
