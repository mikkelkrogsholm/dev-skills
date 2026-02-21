---
name: hono
description: "Hono — ultrafast, multi-runtime web framework built on Web Standards. Use when building with Hono or asking about its APIs, configuration, patterns, or integration. Fetch live documentation for up-to-date details."
---

# Hono

Hono is an ultrafast, lightweight web framework built on Web Standards that runs on Cloudflare Workers, Deno, Bun, AWS Lambda, Node.js, and other runtimes from a single codebase.

## Documentation

- **Docs**: https://hono.dev/llms.txt

## Key Capabilities

Hono ships with extensive built-in middleware and helpers — no external packages needed for:

- **Auth**: Basic Auth, Bearer Auth, JWT, JWK (`hono/basic-auth`, `hono/bearer-auth`, `hono/jwt`)
- **Security**: CORS, CSRF, Secure Headers, IP Restriction (`hono/cors`, `hono/csrf`, `hono/secure-headers`)
- **Performance**: Compress, Cache, ETag, Body Limit, Timeout (`hono/compress`, `hono/cache`, `hono/etag`)
- **Utilities**: Logger, Request ID, Cookie helper, Streaming, WebSocket (`hono/logger`, `hono/cookie`, `hono/streaming`, `hono/websocket`)
- **Rendering**: JSX renderer, HTML helper, SSG (`hono/jsx`, `hono/html`)

## Best Practices

**Validate header names in lowercase.** Hono normalises incoming header keys to lowercase per the Fetch API spec. When accessing validated header values, always use lowercase keys (`value['idempotency-key']`, not `value['Idempotency-Key']`). Uppercase lookups silently return `undefined`.

**Set Content-Type or validation silently passes empty objects.** The built-in `json()` and `form()` validators only parse when the request `Content-Type` matches. A missing or wrong header causes the validator to receive `{}` and pass — no error is thrown. Always set `Content-Type: application/json` (or `application/x-www-form-urlencoded`) in tests and client calls.

**Do not extract handlers into separate controller files.** Unlike Express, Hono's path-parameter types are inferred from the route string at the call site. Moving handlers into separate files loses that inference without writing complex generics. Keep handlers inline with route definitions, or use `factory.createHandlers()` from `hono/factory` when separation is required.
