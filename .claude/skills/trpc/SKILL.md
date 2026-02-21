---
name: trpc
description: "tRPC — end-to-end typesafe APIs for TypeScript without schemas or code generation. Use when building with tRPC or asking about its router setup, procedures, middleware, context, subscriptions, or integration with React, Next.js, or other frameworks. Fetch live documentation for up-to-date details."
---

# tRPC

tRPC enables end-to-end typesafe APIs for TypeScript without requiring schemas or code generation. Type safety flows automatically from server procedure definitions to React hooks and client calls.

## Documentation

- **Docs**: https://trpc.io/llms.txt

## Key Capabilities

tRPC ships with built-in support for patterns that commonly require external libraries:

- **Subscriptions**: Real-time updates via WebSockets or Server-Sent Events — no separate pub/sub package needed (`wsLink`, `httpSubscriptionLink`)
- **Request batching**: Multiple procedure calls in a single HTTP request via `httpBatchLink` — the recommended default link used in all official quickstart setups (must be explicitly configured in the client's `links` option)
- **Data transformers**: Serialize complex types (Date, BigInt, Map) end-to-end via `superjson` transformer option — no manual serialization layer
- **Server-side caller**: Call procedures directly in tests or server code without HTTP overhead using `createCallerFactory()`
- **Middleware chaining**: Compose reusable auth, logging, and rate-limiting logic with `t.middleware()` — result passed through typed `ctx` augmentation

## Best Practices

**Always use `appRouter` type export, never the router value, for client-side type inference.** Importing the router value on the client creates a bundle dependency on server code. Export only the type: `export type AppRouter = typeof appRouter`. Agents often import the full router by mistake, which can bundle server-only code or cause circular imports.

**Procedures are not callable unless registered on a router.** A procedure built with `.query()` or `.mutation()` is a definition, not a live endpoint. It must be added to a router object passed to `createHTTPServer` or the Next.js adapter. Agents sometimes call `createCallerFactory` on a bare procedure instead of a router.

**Context is created per-request — never mutate shared state inside `createContext`.** Each request receives a fresh context object. Storing request-scoped data (user session, request ID) in a module-level variable instead of returning it from `createContext` causes data leakage between concurrent requests.

**Nest sub-routers under named keys, not flat.** Use `t.router({ posts: postRouter, users: userRouter })` to create typed namespaces. Use `t.mergeRouters(a, b)` only when you intentionally want a flat merge with no nesting — otherwise type inference for namespaced routes breaks.

**Set `abortOnUnmount: true` on the tRPC React provider to cancel in-flight requests on component unmount.** By default tRPC does not abort queries when a component unmounts, which causes state updates on unmounted components and potential race conditions in fast navigation scenarios.
