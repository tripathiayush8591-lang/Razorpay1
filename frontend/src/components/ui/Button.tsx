import React from "react";
import clsx from "clsx";
import { Loader2 } from "lucide-react";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  icon,
  className,
  ...props
}) => {
  const baseClasses =
    "inline-flex items-center justify-center font-medium transition cursor-pointer select-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none";

  const sizeClasses: Record<ButtonSize, string> = {
    sm: "text-xs px-3 py-1.5 rounded-md gap-1.5 h-8",
    md: "text-sm px-4 py-2 rounded-lg gap-2 h-10",
    lg: "text-base px-5 py-2.5 rounded-lg gap-2.5 h-12",
  };

  const variantClasses: Record<ButtonVariant, string> = {
    primary: "bg-accent text-accent-foreground hover:bg-accent-dark shadow-xs",
    secondary: "bg-surface-secondary text-text-primary border border-border hover:bg-surface-tertiary",
    outline: "bg-transparent text-text-primary border border-border hover:bg-surface-secondary",
    ghost: "bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-secondary",
    destructive: "bg-error text-surface hover:bg-error-foreground shadow-xs",
  };

  return (
    <button
      className={clsx(baseClasses, sizeClasses[size], variantClasses[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      <span>{children}</span>
    </button>
  );
};

export default Button;
