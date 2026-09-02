import React, { forwardRef } from "react";
import clsx from "clsx";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, className, children, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label htmlFor={selectId} className="text-xs font-semibold text-text-dark">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={clsx(
            "w-full bg-surface text-text-primary text-sm rounded-lg border border-border px-3 py-2 transition",
            "focus:outline-hidden focus:border-accent focus:ring-2 focus:ring-accent/20",
            "disabled:bg-surface-secondary disabled:text-text-muted disabled:cursor-not-allowed",
            error && "border-error focus:border-error focus:ring-error/20",
            className
          )}
          {...props}
        >
          {children}
        </select>
        {error ? (
          <p className="text-xs text-error">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-text-secondary">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Select.displayName = "Select";

export default Select;
