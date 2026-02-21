---
name: tanstack-query
description: "TanStack Query — powerful async state manager for TypeScript/JavaScript with caching, background refetching, and server state synchronization. Use when building with TanStack Query (React Query) or asking about its caching, query keys, mutations, invalidation, optimistic updates, or integration with React, Vue, Solid, or Svelte. Fetch live documentation for up-to-date details."
---

# TanStack Query

TanStack Query is a powerful async state manager with caching, background refetching, and server state synchronization for TypeScript/JavaScript.

## Documentation

- **Docs**: https://tanstack.com/llms.txt

## Best Practices

- **Query keys must be stable and structured** — use arrays with a logical hierarchy (e.g., `['todos', { status: 'active' }]`). TanStack Query hashes keys by serialized value (not reference), so the real gotcha is unstable keys where the object's contents change on every render — this causes unnecessary refetches.
- **`staleTime` defaults to 0, not infinity** — data is immediately considered stale after fetching, triggering a background refetch on every mount and window focus. Set `staleTime` deliberately (e.g., `staleTime: 60_000`) to avoid unnecessary network requests.
- **Invalidate after mutations, do not manually merge** — after a mutation succeeds, call `queryClient.invalidateQueries({ queryKey: ['todos'] })` to let Query refetch fresh data. Always scope the call — `invalidateQueries()` with no arguments invalidates every query in the cache.
- **`gcTime` (formerly `cacheTime`) controls when unused data is garbage collected** — the default is 5 minutes. Queries are not removed immediately when a component unmounts; the cached data stays available for that window, which is intentional for back-navigation but surprises developers expecting instant cleanup.
- **Do not put server state in a separate global store** — TanStack Query is the server state manager. Adding Redux or Zustand alongside it for async data leads to duplication. Reserve other stores for purely client-side UI state.
