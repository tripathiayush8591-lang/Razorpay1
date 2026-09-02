# UI Tokens — Agentic Commerce V2

Use these tokens instead of hardcoded component colors.

## Tailwind v4 Theme

```css
@import "tailwindcss";

@theme {
  --font-sans: "Inter", sans-serif;

  --color-background: #f6f7fb;
  --color-surface: #ffffff;
  --color-surface-secondary: #f9fafb;
  --color-surface-tertiary: #f2f5f7;

  --color-border: #e7eaf3;
  --color-border-strong: #dfe1e7;

  --color-text-primary: #101828;
  --color-text-secondary: #6a7282;
  --color-text-muted: #99a1af;
  --color-text-dark: #364153;

  --color-accent: #7c5cfc;
  --color-accent-dark: #5e4cff;
  --color-accent-light: #f3e8ff;
  --color-accent-muted: #faf5ff;
  --color-accent-foreground: #ffffff;

  --color-success: #10b981;
  --color-success-light: #ecfdf5;
  --color-success-foreground: #007a55;

  --color-info: #61a8ff;
  --color-info-light: #eff6ff;
  --color-info-foreground: #155dfc;

  --color-warning: #ff8904;
  --color-warning-light: #fff7ed;

  --color-error: #ef4444;
  --color-error-light: #fef2f2;
  --color-error-foreground: #b91c1c;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}
```

## Usage

- Page: `bg-background`
- Card: `bg-surface border-border`
- Primary text: `text-text-primary`
- Secondary text: `text-text-secondary`
- Muted: `text-text-muted`
- Primary action: `bg-accent text-accent-foreground`
- Success: `text-success`
- Warning: `text-warning`
- Error: `text-error`

Never use raw Tailwind colors such as `bg-purple-500` or `text-gray-600`.

## Commerce Status

| State | Token |
|---|---|
| In stock | `success` |
| Low stock | `warning` |
| Out of stock | `error` |
| Active | `success` |
| Draft/inactive | `text-muted` |
| Payment pending | `warning` |
| Paid | `success` |
| Confirmed | `accent` |

## Spacing

- 4px: `gap-1`
- 8px: `gap-2`
- 12px: `gap-3`
- 16px: `gap-4`
- 24px: `gap-6`
- 32px: `gap-8`
- 48px: `gap-12`

## Radii

- Small controls: `rounded-md`
- Cards: `rounded-xl` or `rounded-2xl`
- Pills: `rounded-full`

## Shadows

Use subtle shadows only:
- cards: `shadow-sm`
- floating assistant panel: `shadow-lg`

Avoid excessive glow or neon effects.
