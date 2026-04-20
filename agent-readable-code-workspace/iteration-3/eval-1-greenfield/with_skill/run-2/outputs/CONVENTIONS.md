# Conventions

Opinionated norms for this API. Optimised for AI agents (Claude Code, Cursor) editing the code by grep + partial file reads. Humans benefit too.

**Core heuristic:** write so someone grepping a single file can act correctly without reading the rest of the repo.

---

## Stack (pinned, boring on purpose)

- Runtime: **Bun** (latest LTS, pinned in `package.json` engines)
- Framework: **Hono**
- ORM: **Drizzle**
- DB: **Postgres on Neon** via `@neondatabase/serverless` HTTP driver
- Validation: **Zod**
- Tests: **`bun:test`**

Pin exact versions (no `^`) for `hono`, `drizzle-orm`, `drizzle-kit`, `zod`, `@neondatabase/serverless`, `stripe`. Agents know a specific API version; drifting minor versions break their memory.

---

## Architecture: vertical slices

Code lives under `src/features/<area>/` — one folder per bounded context (`auth`, `users`, `billing`). A feature owns **its routes, service, repo, schema, DTOs, and tests** together.

Do **not** create top-level `controllers/`, `services/`, `repositories/` directories. That spreads one feature across four folders and makes agents fix 3 of 5 touchpoints.

A feature's public surface is its `index.ts`: `mount<Feature>Routes(app, ctx)` plus exported types. Cross-feature imports go through `index.ts`, never into sibling internals.

---

## Naming

- **Files:** `kebab-case.ts`. Feature files prefix with the feature: `billing.service.ts`, not `service.ts`.
- **Functions:** verbs that describe the domain action: `issueRefund`, `markInvoicePaid`, `startCheckoutAndReserveSeat`. Not `process`, `handle`, `doStuff`, `manage`.
- **Banned file/folder names:** `utils.ts`, `helpers.ts`, `common.ts`, `misc.ts`, `lib/` as a dumping ground, `Manager`, `Service` (standalone), `Handler`. If you need shared code, name it for what it does: `http/errors.ts`, `db/ids.ts`.
- **IDs:** branded types. `type UserId = string & { readonly __brand: 'UserId' }`. Never pass raw `string` across feature boundaries.
- **Events / webhook payloads:** discriminated unions keyed by `kind`, with one exhaustive `switch`. No string-keyed dispatch tables.

---

## File size and shape

- **Hard cap: 300 lines per file.** Warn at 200. Split by splitting the feature, not by extracting abstract bases.
- **Line width: 120 chars.** No minified or generated code checked into `src/` — generated output goes in `drizzle/` or `dist/` and is `.gitignore`d where possible.
- **One exported function per `*.service.ts` file** when it exceeds ~80 lines. Small files beat clever files.
- **No barrel re-exports** beyond the feature `index.ts`. Import from the defining file: `import { issueRefund } from "@/features/billing/billing.service"`, not from a root `@/index`.

---

## Dependencies and side effects

- **Inject `ctx` (`{ db, clock, logger, env }`) as the first argument** to every service and repo function. No reaching into module-global singletons for `process.env`, `new Date()`, `Math.random()`, or the DB client.
- **No DI container.** Wiring is explicit in `src/app.ts` and `src/index.ts`. Control flow must be traceable by grep.
- **No metaprogramming.** No `Proxy`, no runtime monkey-patching, no decorator stacks that rewrite behaviour. Hono middleware is fine — it's explicit and local.
- **Inheritance depth: 1.** Use composition. Error classes may extend `Error` once; that's it.
- **One source of truth for types:** `z.infer<typeof Schema>` for inputs, `typeof table.$inferSelect` for rows. Never hand-maintain parallel type declarations.

---

## Drizzle + Neon

- Schema per feature in `<feature>.schema.ts`, re-exported from `src/db/schema.ts` so `drizzle-kit` sees everything.
- Repos own all SQL. Services never import `drizzle-orm` directly.
- Migrations are generated (`bunx drizzle-kit generate`) and committed. Never hand-edit a migration after it lands on `main`.
- Use the Neon HTTP driver for request-scoped queries. Transactions that span multiple round trips need the WebSocket driver — document that locally where used.

---

## HTTP and errors

- Hono routers defined per feature. `app.ts` only imports `mount<Feature>Routes` and mounts them under a prefix.
- Validate every request body, query, and param with Zod at the route boundary. Services assume inputs are already typed and valid.
- Throw typed errors (`NotFoundError`, `UnauthorizedError`, `ConflictError`) from services. A single `app.onError` in `app.ts` maps them via `http/errors.ts::toHttpResponse`. No try/catch around every handler.

---

## Testing

- **Colocated.** `foo.ts` and `foo.test.ts` in the same directory. No `tests/` mirror tree.
- Test runner: `bun test`. One command runs everything. CI runs `bun run check` = `tsc --noEmit && bun test && bunx drizzle-kit check`.
- **Deterministic.** `test/setup.ts` seeds faker, freezes the clock, injects a fixed-seed RNG. Snapshots never contain UUIDs or timestamps generated at test time.
- **Database tests** use `makeTestDb()` from `src/test/db.ts` — either a Neon branch per test file or transaction-rollback isolation. Never hit a shared dev DB from tests.
- **Coverage target:** every service function has at least one unit test; every route has at least one HTTP-level test. Don't chase a percentage.

---

## Comments and docs

- Comment the **why**, never the what. Types and names cover the what.
- A stale comment is worse than none — it confidently lies to the next agent. Delete comments you can't keep accurate.
- Top of each feature `index.ts`: a 3-5 line block stating what the feature owns, its public functions, and any non-obvious invariants (e.g. "all timestamps are UTC, stored as `timestamptz`").

---

## Commands (memorise these)

```
bun install              # install deps
bun run dev              # bun --hot src/index.ts
bun test                 # all tests
bun run check            # typecheck + tests + drizzle schema check
bunx drizzle-kit generate  # create migration from schema changes
bunx drizzle-kit migrate   # apply migrations to $DATABASE_URL
```

A single `bun run check` must pass before any PR. Agents use it as their verification loop.

---

## When to break these rules

Framework conventions win (rare here — Hono is unopinionated). Migrations and fixtures are allowed to duplicate shape; that's the domain, not a refactor target. Throwaway scripts under `scripts/` skip the ceremony. Everything else: follow the rules, or leave a one-line `// NOTE:` explaining why not.
