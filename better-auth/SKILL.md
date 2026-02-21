---
name: better-auth
description: "Better Auth — framework-agnostic authentication and authorization framework for TypeScript. Use when building with Better Auth or asking about its APIs, configuration, plugins, session management, OAuth, or integration. Fetch live documentation for up-to-date details."
---

# Better Auth

Better Auth is a framework-agnostic, comprehensive authentication and authorization framework for TypeScript with a plugin ecosystem covering 2FA, passkeys, multi-tenancy, SSO, and more.

## Documentation

- **Docs**: https://www.better-auth.com/llms.txt

## Key Capabilities

Better Auth ships built-in support for features that typically require external libraries:

- **Two-factor authentication** — TOTP/OTP via the `twoFactor` plugin, no third-party lib needed
- **Passkeys** — WebAuthn support via the `passkey` plugin
- **Multi-session** — concurrent sessions per user via the `multiSession` plugin
- **Organization/multi-tenancy** — teams, roles, and permissions via the `organization` plugin
- **Admin panel** — user management API via the `admin` plugin
- **OIDC/OAuth provider** — make your app an identity provider via `oidcProvider`
- **API key management** — issue and validate API keys via the `apiKey` plugin

## Best Practices

**Plugins require both server and client registration.**
Adding a plugin only to the server-side `auth` config is not enough. Every plugin that exposes client-callable endpoints must also be added to `createAuthClient({ plugins: [...] })`. Without the client plugin, the typed methods are absent and requests will fail.

```ts
// server: auth.ts
export const auth = betterAuth({
  plugins: [twoFactor()],
})

// client: auth-client.ts  — must mirror server plugins
export const authClient = createAuthClient({
  plugins: [twoFactorClient()],
})
```

**Cookie cache delays session revocation.**
When `cookieCache` is enabled, calling `revokeSession` or signing out on one device does not immediately invalidate other devices' sessions. The old session remains valid until the cookie cache `maxAge` expires. Design logout flows accordingly — do not rely on instant cross-device revocation when cookie caching is active.

**Session freshness and session validity are independent checks.**
A session can be valid (not expired) but not "fresh" (too old since creation). Certain sensitive endpoints enforce freshness via `freshAge`. Treat a 401 on a protected endpoint as potentially a freshness failure, not just an expiry — prompt re-authentication rather than a full sign-out flow.

**`disableOriginCheck` disables CSRF protection too.**
The option name implies only URL validation is affected, but it simultaneously disables the origin-header-based CSRF defense. Never set `disableOriginCheck: true` in production. Use `trustedOrigins` to allowlist specific domains instead.

**Custom session fields are never served from cache.**
Fields added via `session` customization functions are re-fetched from the database on every request, even when secondary storage or cookie caching is configured. Heavy custom session computations have no cache benefit — keep them lightweight or memoize externally.
