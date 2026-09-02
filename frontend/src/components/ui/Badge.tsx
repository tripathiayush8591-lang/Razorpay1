import React from "react";
import clsx from "clsx";

export type BadgeVariant = "neutral" | "success" | "warning" | "error" | "accent" | "info";
export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  size = "sm",
  icon,
  className,
  ...props
}) => {
  const baseClasses =
    "inline-flex items-center font-medium rounded-full select-none shrink-0 border";

  const sizeClasses: Record<BadgeSize, string> = {
    sm: "text-[11px] px-2 py-0.5 gap-1",
    md: "text-xs px-2.5 py-1 gap-1.5",
  };

  const variantClasses: Record<BadgeVariant, string> = {
    neutral: "bg-surface-secondary text-text-secondary border-border",
    success: "bg-success-light text-success-foreground border-success/20",
    warning: "bg-warning-light text-warning border-warning/20",
    error: "bg-error-light text-error-foreground border-error/20",
    accent: "bg-accent-light text-accent-dark border-accent/20",
    info: "bg-info-light text-info-foreground border-info/20",
  };

  return (
    <span
      className={clsx(baseClasses, sizeClasses[size], variantClasses[variant], className)}
      {...props}
    >
      {icon ? <span className="shrink-0">{icon}</span> : null}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
