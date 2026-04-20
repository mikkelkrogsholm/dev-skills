# Conventions

Opinionated norms for this Hono + Drizzle + Neon + Bun service. Optimized for maintenance by AI agents (Claude Code, Cursor) over a multi-year horizon. The underlying heuristic: **someone grepping a single file should be able to act correctly without reading the rest of the repo.**

---

## 1. Architecture: vertical slices, not horizontal layers

- Every domain lives in `src/features/<feature>/`. Routes, handlers, db access, schemas, types, errors, and unit tests colocate there.
- No top-level `controllers/`, `services/`, `repositories/`. These scatter one feature across five folders and guarantee the agent will fix 3-of-5 touchpoints and ship a bug.
- Cross-feature code goes in `src/lib/` — and only if it names one specific thing (`clock.ts`, `ids.ts`). No `utils.ts`, `helpers.ts`, `common.ts`, `misc.ts`. Ever.
- `src/middleware/` is for truly cross-cutting Hono middleware (CORS, rate limit, error handler). Feature-specific middleware (e.g. `requireUser`) lives inside the feature.

## 2. Naming

- Files: kebab-case, feature-prefixed: `billing.webhooks.ts`, `users.queries.ts`. The prefix is deliberate duplication — it makes grep results readable out of context.
- Functions: verbs that describe the full effect. `chargeCustomerAndEmitReceipt`, not `process`. `syncSubscriptionFromStripe`, not `handle`.
- **Banned names** (CI grep check): `Manager`, `Service`, `Helper`, `Handler` (as a class suffix; Hono route handlers are fine), `Util`, `doStuff`, `process`, `handle` (as a standalone function name), `data`, `info`, `temp`.
- Rename aggressively during refactors. A stale name is a confidently-wrong oracle.
- Feature folder names are singular domain nouns: `auth`, `user`, `billing` — pick one form and stick with it. (We use plural for collections: `users`, singular for concepts: `auth`, `billing`.)

## 3. File size and shape

- **Hard ceiling: 400 lines per file.** Warn at 300. Files over ~800 lines regularly break agent apply-model merges; the middle of a large file is the region agents read worst.
- **Line length ceiling: 200 characters.** Long lines mean generated code, minified blobs, or giant inline SQL — extract or regenerate.
- **No near-duplicate blocks longer than 6 lines within the same file.** Copy-paste defeats `str_replace` edits. Extract at the seam; keep the named function in the same file.
- One exported concept per file when practical. A file named `auth.sessions.ts` should be about sessions; if it grows a second concept, split.
- No barrel files (`index.ts` that only re-exports). Consumers import from the defining file. Barrels add a grep hop and hide the real module graph.

## 4. Dependencies and control flow

- **Static and explicit.** No `eval`, no `Proxy`, no runtime monkey-patching, no dynamic `import()` except for genuine lazy-loaded code.
- **No magic-string dispatch.** Stripe webhook routing, job handlers, event listeners: use a discriminated union + one exhaustive `switch` in one file. Never `registry[evt.type](evt)` spread across the repo.
- **No deep inheritance.** Max 1 level, and only when the framework demands it. Prefer composition and plain functions.
- **No heavy DI containers.** Dependencies are passed explicitly through `AppContext` (`{ db, clock, logger, env, fetch }`). Control flow must be visible to grep.
- **Pinned versions.** `package.json` has no `^` or `~` on `hono`, `drizzle-orm`, `stripe`, `@neondatabase/serverless`, `zod`, `better-auth`. The docs the agent fetches must match the version running.
- **Boring stack only.** Hono, Drizzle, Zod, Stripe, Neon, Bun — all mainstream, all in training data. Do not adopt a cutting-edge library because it's elegant; agents edit Hono + Drizzle correctly and edit bespoke DSLs badly.

## 5. Types at every boundary

- **Branded IDs.** `UserId`, `SessionId`, `CustomerId`, `SubscriptionId` are `string & { readonly __brand: 'UserId' }`. Defined in `lib/ids.ts` using a single `Brand<T, Tag>` helper. This catches the `userId`/`orgId` swap at compile time.
- **Discriminated unions over strings.** Events, errors, request kinds — all tagged:
  ```ts
  type StripeEvent =
    | { kind: 'checkout.session.completed'; session: Stripe.Checkout.Session }
    | { kind: 'customer.subscription.updated'; subscription: Stripe.Subscription };
  ```
  One exhaustive `switch`, one file.
- **Single source of type truth.** Request types are `z.infer<typeof Schema>`. DB row types are `typeof table.$inferSelect`. Never hand-maintain a type parallel to a schema; the agent will update one and the other will silently drift.
- **Public function signatures are fully typed.** No implicit `any`, no unannotated returns on exported functions. Strict mode on in `tsconfig.json`: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`.
- **`as const` on literal tuples and records.** Preserve narrowing.

## 6. Side effects and determinism

- **No global singletons.** `db`, `clock`, `logger`, `env`, `fetch` live in `AppContext` and are passed to functions that need them.
- **No direct `process.env` access** outside `src/env.ts`. The rest of the code reads `ctx.env`.
- **No `new Date()` in non-test code except in `clock.ts`.** Everywhere else: `ctx.clock.now()`.
- **Tests freeze the clock and seed randomness.** UUIDs in snapshots are banned. Use `TestClock` and factory helpers with seeded IDs.

## 7. Errors

- Typed error classes per feature (`auth.errors.ts`, `users.errors.ts`). Each has a stable `code` string for client consumption.
- Never throw plain `Error` in business logic. Throw a typed class or return a `Result<T, E>` for expected failures.
- The top-level `middleware/error-handler.ts` maps typed errors to HTTP responses. Business code never builds `Response` objects directly.

## 8. Comments and docs

- Comment the **why**, never the what. Code shows the what; a stale "what" comment lies.
- Every non-obvious invariant, past-incident workaround, or external-API quirk gets a comment explaining the constraint.
- **Wrong docstrings crash agent accuracy below baseline.** If you change a function's behavior, update or delete its comment in the same commit. CI grep rejects `TODO:` without a linked issue.

## 9. Testing

- **Unit tests colocate:** `foo.ts` sits next to `foo.test.ts`. Agents find them by proximity; distant `tests/` trees guarantee they won't be run or updated.
- **Integration tests live in `/test/integration/`** and spin up an ephemeral Neon branch per CI run. Seed deterministically.
- **One command verifies everything:** `bun run check` runs `bun lint && bun typecheck && bun test`. This is the agent's feedback loop; it must be fast (<60s for unit, <3min with integration) and deterministic.
- **Flaky tests are bugs, not noise.** An agent retrying a flaky test until context runs out either disables the test or declares false success. Fix or delete; never `.skip()` without a linked issue.
- Test the feature from its public entrypoint (the handler), not the internals, unless the internal has genuine complexity. Avoid mocking Drizzle — use a real test db branch.

## 10. Database (Drizzle + Neon)

- All tables in `src/db/schema.ts`. One file. Resist the urge to split by feature — Drizzle's relations are clearer when colocated, and migrations generate from one schema.
- Query functions (`users.queries.ts`, `users.mutations.ts`) accept `db` as a parameter, never import it. This makes them testable against a transaction-scoped db in tests.
- Migrations are drizzle-kit-generated SQL in `src/db/migrations/`. Do not hand-edit. Never squash history on a deployed branch.
- Use Neon branches for preview envs and CI. Branch creation lives in `scripts/db-branch.ts`.

## 11. Agent context file

- `CLAUDE.md` at the repo root lists: the single verification command (`bun run check`), the banned names, the feature-folder rule, and one canonical example feature (probably `users/`) to imitate.
- Keep `CLAUDE.md` under 100 lines. Detailed conventions live here in `CONVENTIONS.md`; `CLAUDE.md` points to it.

## 12. When to break these rules

These rules serve agent-readability — one lens, not the only one. Break them when:

- The framework dictates layout (unlikely here; Hono is unopinionated).
- Some duplication is inherent (DTOs, migration SQL, Stripe webhook payload shapes).
- The code is genuinely throwaway (a one-shot data backfill script in `scripts/` can be looser).

If a rule doesn't fit, write down why in the file or commit message. Silent deviations rot.
