import React, { createContext, useContext, useState, useCallback } from "react";
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

export type ToastVariant = "info" | "success" | "warning" | "error";

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  title?: string;
}

interface ToastContextType {
  toast: (message: string, options?: { variant?: ToastVariant; title?: string; durationMs?: number }) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = (): ToastContextType => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      toast: (msg: string) => console.log("[Toast]", msg),
      removeToast: () => {},
    };
  }
  return ctx;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, options?: { variant?: ToastVariant; title?: string; durationMs?: number }) => {
      const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      const variant = options?.variant || "info";
      const title = options?.title;
      const durationMs = options?.durationMs ?? 4000;

      const newToast: ToastItem = { id, message, variant, title };
      setToasts((prev) => [...prev.slice(-4), newToast]);

      if (durationMs > 0) {
        setTimeout(() => {
          removeToast(id);
        }, durationMs);
      }
    },
    [removeToast]
  );

  const getVariantStyles = (variant: ToastVariant) => {
    switch (variant) {
      case "success":
        return {
          card: "bg-surface border-success/30 shadow-md",
          icon: <CheckCircle2 className="w-4 h-4 text-success shrink-0" />,
          titleColor: "text-success font-bold",
        };
      case "error":
        return {
          card: "bg-surface border-error/30 shadow-md",
          icon: <AlertCircle className="w-4 h-4 text-error shrink-0" />,
          titleColor: "text-error font-bold",
        };
      case "warning":
        return {
          card: "bg-surface border-warning/30 shadow-md",
          icon: <AlertTriangle className="w-4 h-4 text-warning shrink-0" />,
          titleColor: "text-warning font-bold",
        };
      default:
        return {
          card: "bg-surface border-info/30 shadow-md",
          icon: <Info className="w-4 h-4 text-info shrink-0" />,
          titleColor: "text-info font-bold",
        };
    }
  };

  return (
    <ToastContext.Provider value={{ toast, removeToast }}>
      {children}
      <div
        aria-live="polite"
        className="fixed top-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((t) => {
          const styles = getVariantStyles(t.variant);
          return (
            <div
              key={t.id}
              className={`pointer-events-auto p-3.5 rounded-xl border flex items-start gap-3 transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${styles.card}`}
            >
              <div className="pt-0.5">{styles.icon}</div>
              <div className="flex-1 min-w-0">
                {t.title && <div className={`text-xs ${styles.titleColor}`}>{t.title}</div>}
                <div className="text-xs text-text-primary leading-relaxed">{t.message}</div>
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-text-muted hover:text-text-primary p-0.5 rounded transition cursor-pointer shrink-0"
                aria-label="Dismiss alert"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};
