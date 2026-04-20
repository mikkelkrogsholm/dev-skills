# Conventions

Stack: Hono + Drizzle + Postgres (Neon) on Bun. Maintained mostly by Claude Code and Cursor. These rules optimize for **agent-readability first, human-readability second**. When they conflict, agent-readability wins — agents are our default reader.

The underlying heuristic: *an agent grepping a single file should be able to act correctly without reading the rest of the repo.*

---

## 1. Architecture: vertical slices, not layers

- One directory per feature under `src/`: `auth/`, `users/`, `billing/`, `health/`. Everything the feature needs (routes, schema, handlers, tests, types) lives inside it.
- **No** `controllers/`, `services/`, `repositories/`, `dto/`. Layer directories scatter a feature across five files and are the #1 cause of partial agent edits.
- `src/lib/` is for cross-feature primitives only (IDs, Money, Result, logger). If something is only used by one feature, it belongs in that feature's directory.
- `src/http/` holds transport concerns shared by all features: error mapping, request-id, OpenAPI.
- New feature = new directory. Do not grow existing features past ~10 files; split by sub-resource (`billing/invoices/`, `billing/subscriptions/`) when it gets there.

## 2. File size and shape

- **Hard cap: 300 lines per file.** Soft target: 150. Files over 300 regularly break agent apply-model merges.
- **One exported function per `.ts` file** for feature logic. Filename = function name in kebab-case (`issue-refund.ts` exports `issueRefund`).
- Route files (`routes.ts`) are the only exception — they may group related handlers but must stay under 300 lines.
- **Max line length: 120 chars.** No minified assets, no generated code in `src/`. Generated output goes in `dist/` or `.gitignore`.
- No barrel files (`index.ts` that only re-exports). Import from the defining file. Exception: a feature's `types.ts` may aggregate `z.infer` types.

## 3. Naming

- **Domain-specific verbs.** `issueRefund`, `verifySession`, `chargeCustomer`. Not `process`, `handle`, `doStuff`, `execute`, `run`.
- **Banned filenames:** `utils.ts`, `helpers.ts`, `common.ts`, `misc.ts`, `manager.ts`, `service.ts`, `handler.ts`. If you need one, you are missing a feature slice.
- **Files:** kebab-case (`issue-refund.ts`). **Exports:** camelCase for functions, PascalCase for types/classes. **DB tables/columns:** snake_case.
- **Route files:** always `routes.ts`. **Test files:** `<source>.test.ts` colocated next to source. **Schema files:** `schema.ts` (drizzle tables for that feature).
- Rename aggressively during refactors. A stale name is worse than a generic one — it actively misleads the agent.

## 4. Types

- **Branded IDs.** `type UserId = string & { readonly __brand: 'UserId' }`. Never pass `string` where you mean an ID; the compiler must catch swaps.
- **One source of truth.** Derive types with `z.infer<typeof Schema>` and `typeof users.$inferSelect`. No hand-maintained parallel `interface User`.
- **Discriminated unions over magic strings.** Webhook events, job kinds, result variants: `type Event = { kind: 'created'; ... } | { kind: 'deleted'; ... }` with an exhaustive switch.
- **`as const` on literal tuples/records** so types narrow to the literal.
- **Typed public signatures everywhere.** No `any`. No implicit `any` (`"strict": true` + `"noImplicitAny": true` in `tsconfig.json`). `unknown` at untrusted boundaries, validated by Zod immediately.

## 5. Dependencies and side effects

- **Inject via `deps`.** Every non-pure function takes `deps: { db, clock, logger, fetch, env }` (or a subset) as the first argument. No reaching into `process.env` mid-function. No module-level `new Date()`.
- **No metaprogramming.** No `Proxy`, no `Reflect`, no runtime monkey-patching, no decorator stacks that rewrite behavior. Agents can't grep through them.
- **No magic-string dispatch.** No `registerHandler("user.created", ...)` spread across files. Webhook handlers use a single exhaustive switch in one file.
- **Max inheritance depth: 2.** Prefer composition and plain functions. Class hierarchies beyond `class Foo extends BaseError` are banned.
- **Direct imports only.** No dynamic `import()` except for lazy-loaded optional deps, and then only in one clearly-named file.

## 6. Drizzle and database

- Each feature owns its tables in `<feature>/schema.ts`. `src/db/schema.ts` re-exports them for drizzle-kit — this is the **only** permitted barrel file.
- Never write raw migration SQL by hand. `bun drizzle-kit generate` -> review -> commit.
- Queries live next to the function that uses them, not in a `queries/` or `repositories/` folder.
- Use Drizzle's `db.query.xxx.findFirst` / `findMany` for reads, `db.insert/update/delete` for writes. No repository abstraction layer.
- Use Neon's `@neondatabase/serverless` HTTP driver in production, `postgres` locally — selected in `db/client.ts` based on `env.DATABASE_URL` shape.

## 7. Hono specifics

- One `Hono()` per feature (`auth/routes.ts` exports `authRoutes`). `src/app.ts` mounts them: `app.route('/auth', authRoutes)`.
- Use `@hono/zod-validator` at every route boundary. Untyped `c.req.json()` is banned.
- Middleware that needs deps is exported as a factory: `verifySession(deps) => middleware`. Never close over module-scoped state.
- Errors thrown from handlers must be `AppError` subclasses; `http/error-middleware.ts` maps them to HTTP responses. No ad-hoc `c.json({ error: ... }, 500)` inside handlers.

## 8. Testing

- **Colocated.** `issue-refund.ts` + `issue-refund.test.ts` in the same directory. No distant `tests/` tree.
- **`bun test`** only. No Vitest, no Jest. Run everything with `bun test`; run one feature with `bun test src/billing/`.
- **Determinism is non-negotiable.** Freeze time (inject `clock`), seed randomness, use fixed UUIDs in fixtures. A flaky test is a broken test — delete or fix, never retry.
- **Integration tests** use a throwaway Neon branch per run (`NEON_BRANCH=test-<git-sha>`) or a local Postgres via `docker compose`. Never touch production schemas.
- **One verification command:** `bun run check` runs `bun typecheck && bun lint && bun test`. Must be green before any commit. This is the agent's feedback loop.

## 9. Dependencies (npm)

- **Pin exact versions.** No `^`, no `~` on load-bearing packages (`hono`, `drizzle-orm`, `stripe`, `zod`, `@neondatabase/serverless`). Agent memory of an API is version-specific.
- **Prefer boring, popular packages.** Hono, Drizzle, Zod, Stripe SDK, pino, argon2. Avoid bespoke internal DSLs, EffectTS, fp-ts — they have thin training-data presence and agents guess.
- Adding a new dep requires: (a) a single-file justification in the PR, (b) pinned version, (c) an import from the defining file — no shim/wrapper unless the API is genuinely hostile.

## 10. Agent context

- Keep `CLAUDE.md` and `AGENTS.md` at repo root. They list: the one check command, feature-directory map, and "if you are about to create `utils.ts`, stop."
- Add `.cursorignore` / `.claudeignore` entries for `dist/`, `node_modules/`, `drizzle/migrations/*.sql`.
- Every PR touching a feature must touch that feature's tests in the same commit. No "tests in a follow-up."

---

## When to break these rules

- Framework conventions win. If a future Hono plugin requires a specific layout, follow it.
- Public API stability wins. A published function name cannot be renamed just because it's generic.
- Throwaway scripts (`scripts/one-off-*.ts`) are exempt from size and testing rules but still banned from `utils.ts` naming.

If a rule fires where it shouldn't, suppress explicitly in the PR description. Do not silently refactor around it.
