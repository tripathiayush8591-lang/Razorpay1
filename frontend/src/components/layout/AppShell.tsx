import React from "react";
import { Outlet } from "react-router-dom";
import StorefrontHeader from "./StorefrontHeader";
import StorefrontFooter from "./StorefrontFooter";
import CartDrawer from "./CartDrawer";
import AssistantPanel from "../assistant/AssistantPanel";
import { Sparkles } from "lucide-react";
import { useMockCommerce } from "../../lib/mock/MockCommerceContext";

export const AppShell: React.FC = () => {
  const { isAssistantOpen, setIsAssistantOpen } = useMockCommerce();

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col antialiased selection:bg-accent-light selection:text-accent-dark">
      {/* Top Storefront Navigation */}
      <StorefrontHeader />

      {/* Main Page Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <StorefrontFooter />

      {/* Slide-over Cart Drawer */}
      <CartDrawer />

      {/* Persistent Floating AI Assistant Launcher & Panel */}
      <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end">
        {isAssistantOpen ? (
          <div className="mb-3 animate-in slide-in-from-bottom-5 duration-200">
            <AssistantPanel onClose={() => setIsAssistantOpen(false)} />
          </div>
        ) : (
          <button
            onClick={() => setIsAssistantOpen(true)}
            className="group inline-flex items-center gap-2.5 px-4 py-3 rounded-full bg-accent text-accent-foreground shadow-lg hover:bg-accent-dark hover:scale-105 active:scale-95 transition duration-200 cursor-pointer border border-surface/20"
            aria-label="Open AI Shopping Assistant"
          >
            <div className="relative">
              <Sparkles className="w-5 h-5 group-hover:rotate-12 transition duration-200" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-success rounded-full ring-2 ring-accent" />
            </div>
            <span className="text-xs font-semibold tracking-wide pr-1">Shop with AI</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default AppShell;
