---
name: tailwindcss
description: "Tailwind CSS — utility-first CSS framework. Use when building with Tailwind CSS or asking about its utility classes, configuration, theming, dark mode, responsive design, custom plugins, or migration from v3 to v4. Fetch live documentation for up-to-date details."
---

# Tailwind CSS

Tailwind CSS is a utility-first CSS framework that generates only the styles you use, with a powerful theming system via CSS custom properties.

## Documentation

- **Docs**: https://tailwindcss.com/docs
- **Blog (v4 announcement)**: https://tailwindcss.com/blog/tailwindcss-v4
- **GitHub**: https://github.com/tailwindlabs/tailwindcss

## Key Capabilities

Tailwind CSS 4 is a major rewrite. Several things that previously required config files or plugins are now built in:

- **CSS-first configuration**: No `tailwind.config.ts` needed — configure directly in CSS with `@theme` directive
- **Automatic content detection**: No `content` array — Tailwind 4 finds your template files automatically
- **Built-in import support**: `@import "tailwindcss"` replaces the old `@tailwind` directives — no `postcss-import` needed
- **Native CSS variables for theming**: All design tokens exposed as `--color-*`, `--spacing-*`, etc. — no plugin needed
- **Container queries**: Built-in `@container` support with `@min-*` and `@max-*` variants — no plugin needed
- **3D transforms**: `rotate-x-*`, `rotate-y-*`, `perspective-*` built in — no custom utilities needed
- **`not-*` variant**: Built-in `:not()` pseudo-class variant — no plugin needed
- **Zero-config PostCSS**: Just `@import "tailwindcss"` in your CSS entry point

## v3 → v4 Migration (Breaking Changes)

These are common gotchas when migrating or following older tutorials:

**Configuration moved from JS to CSS.** There is no `tailwind.config.ts` in v4. Customization happens in CSS:
```css
@import "tailwindcss";

@theme {
  --color-primary: #406e76;
  --color-accent: #ca8a04;
  --font-heading: "Space Grotesk", sans-serif;
  --radius-lg: 0.75rem;
}
```

**`@tailwind base/components/utilities` is gone.** Replace with a single `@import "tailwindcss"`.

**`@apply` still works but `@theme` is preferred.** For theming, define CSS variables in `@theme` and use them with utilities like `bg-[--color-primary]` or the generated `bg-primary` class.

**Color opacity syntax changed.** `bg-red-500/50` (slash opacity) is the standard. The old `bg-opacity-*` utilities are removed.

**Default border color changed.** Borders default to `currentColor` instead of `gray-200`. Existing designs may need explicit border color classes.

**Renamed utilities:** `flex-shrink-*` → `shrink-*`, `flex-grow-*` → `grow-*`, `overflow-ellipsis` → `text-ellipsis`, `decoration-slice` → `box-decoration-slice`.
