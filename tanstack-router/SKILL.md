---
name: tanstack-router
description: "TanStack Router — fully type-safe router for React with file-based routing, search params validation, loaders, and built-in caching. Use when building with TanStack Router or asking about its route configuration, file-based routing, type-safe links, search params, loaders, or navigation patterns. Fetch live documentation for up-to-date details."
---

# TanStack Router

> **CRITICAL: Your training data for TanStack Router is unreliable.** APIs change between versions and memorized patterns may be wrong or deprecated. Before writing any code, you MUST use `WebFetch` to read the live docs:
>
> **`WebFetch("https://tanstack.com/router/latest/docs/framework/react/overview")`**
>
> Do not proceed without fetching this URL first. Never assume an API exists — verify against current docs.

TanStack Router is a fully type-safe router for React with first-class file-based routing, search params validation, loaders, and built-in caching.

## Best Practices

- **Register the router instance for full type safety** — declare `Register` interface augmentation (`interface Register { router: typeof router }`) in your entry file; without it, `Link`, `useNavigate`, and related hooks fall back to loose types across the module boundary.
- **Search params require explicit validation via `validateSearch`** — raw URL strings are never passed to components; always define a schema (Zod, Valibot, etc.) on the route, or params will be unavailable or throw at runtime.
- **Declare `loaderDeps` for any search params used in loaders** — loaders intentionally cannot access search params directly; omitting `loaderDeps` means cache keys ignore param changes, causing stale data bugs that are silent and hard to trace.
- **File-based route nesting uses `.` not folders** — `blog.post.tsx` means `post` is a child of `blog`. Two distinct `_` conventions: a leading `_` prefix (e.g., `_layout.tsx`) creates a pathless layout that wraps children without adding a URL segment; a trailing `_` suffix on a path segment (e.g., `blog_.tsx`) opts that branch out of the parent's layout wrapper while keeping URL nesting. These have opposite effects — easy to confuse.
- **`router.invalidate()` is coarse-grained** — it reloads all active routes at once; pair TanStack Router with TanStack Query when you need granular per-query invalidation after mutations.
- **Run `tsr generate` (or the Vite plugin) to keep the route tree in sync.** Without this codegen step, `routeTree.gen.ts` is stale and `Link`, `useNavigate`, and other typed APIs fall back to `any`, silently breaking type safety with no obvious error.
- **`notFound()` and `redirect()` must be thrown, not returned from loaders.** These are sentinel values caught by the router — returning them instead of throwing causes the loader to appear to succeed with an unexpected value, producing hard-to-trace runtime bugs.
