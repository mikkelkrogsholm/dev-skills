# Conventions

These rules exist so Claude Code and Cursor can find, read, and modify this codebase reliably. Humans benefit too, but agent-friendliness is the primary design goal. When in doubt, optimize for "an agent can locate the right file from a vague request in under three tool calls."

## 1. Layout: feature folders, fixed file suffixes

Every feature lives in `src/features/<feature>/` and uses the same suffix set:

- `<feature>.routes.ts` — Hono router. HTTP only. No Drizzle imports.
- `<feature>.service.ts` — Business logic. No Hono imports, no `Context`.
- `<feature>.repo.ts` — All Drizzle queries for this feature. No services imported.
- `<feature>.schemas.ts` — Zod input/output schemas.
- `<feature>.types.ts` — Inferred + domain types.
- `<feature>.errors.ts` — Feature-specific error subclasses.
- `<feature>.test.ts` — `bun test`, co-located.

**Why:** An agent given "fix the validation on user signup" should jump straight to `features/auth/auth.schemas.ts`. Predictable suffixes make this a one-glob problem.

**Rule:** Do not invent new suffixes (`*.helpers.ts`, `*.utils.ts`, `*.handlers.ts`). If you need another concern, it is either cross-cutting (`lib/`) or a new feature.

## 2. Layering: strict one-way dependency

```
routes → service → repo → db
         ↑
       lib, integrations, schemas (leaf)
```

Enforced rules:
- `*.routes.ts` imports only `service`, `schemas`, `middleware`, `lib`.
- `*.service.ts` imports only `repo`, `schemas`, `types`, `errors`, `lib`, `integrations`.
- `*.repo.ts` imports only `db/client`, `db/schema`, `types`.
- No feature imports another feature directly. Cross-feature needs go through the target feature's `service.ts` public exports.

An agent asked "where does this DB query live?" should never need to guess.

## 3. File size: hard ceilings

- 300 lines per file is the soft limit. At 300 lines, split.
- 500 lines is a hard ceiling. CI fails above this.
- A single exported function over 80 lines must be split.

Large files defeat agents: context windows fill with irrelevant code, and edits become more error-prone. Splitting by concern (e.g. `billing.service.ts` → `billing.subscriptions.service.ts`, `billing.invoices.service.ts`) is always allowed and preferred over a god-file.

## 4. Naming

- Files and folders: `kebab-case`. Never `camelCase.ts` or `PascalCase.ts` filenames.
- Types and classes: `PascalCase`. Variables and functions: `camelCase`. Constants: `SCREAMING_SNAKE_CASE` only for true compile-time constants.
- DB tables: `snake_case`, plural (`users`, `subscription_items`). Drizzle schema variables: `camelCase` matching the table (`users`, `subscriptionItems`).
- Zod schemas: suffix with purpose — `CreateUserInput`, `UserPublic`, `StripeWebhookEvent`. Never just `UserSchema`.
- Exported functions: verb-first (`createUser`, `findActiveSubscription`). Booleans: `is/has/can` prefix.
- Route handler names match the operation: `POST /users` → handler `createUser`, not `handlePost`.

Consistency here means agent search (`grep createUser`) returns the definition, the test, and the call sites without noise.

## 5. Imports: absolute, via `@/`

- Use `@/` path alias rooted at `src/`. No `../../../` relative imports across feature boundaries.
- Relative imports (`./foo`) only inside the same feature folder.
- Never use barrel `index.ts` files inside `features/*`. They hide symbols from agent search and break tree-shaking. The only barrel allowed is `db/schema/index.ts` (required by drizzle-kit).

## 6. Validation and types

- Every route validates with `zValidator` from `@hono/zod-validator` against a schema in `*.schemas.ts`. No ad-hoc `c.req.json()` parsing.
- Types flow from Zod (`z.infer`) or Drizzle (`$inferSelect` / `$inferInsert`). Do not hand-write types that duplicate a schema.
- `env.ts` is the only file that reads `process.env`. All other code imports the typed `env` object. An agent editing config should only need to touch `env.ts` and `.env.example`.

## 7. Errors

- One `AppError` base class in `lib/errors.ts`. Subclasses carry an HTTP status and a stable string code (`AUTH_INVALID_CREDENTIALS`, `BILLING_STRIPE_WEBHOOK_UNVERIFIED`).
- Services throw typed errors. Routes never build error responses by hand — a single `error-handler` middleware maps `AppError` → JSON response.
- Never throw bare `Error` or strings. An agent should be able to grep a code (`BILLING_CARD_DECLINED`) and find every place it is raised or handled.

## 8. Database

- All queries live in `*.repo.ts`. No Drizzle imports outside `repo.ts`, `db/`, and migration scripts.
- Schema files export table definitions AND their inferred types (`export type User = typeof users.$inferSelect;`).
- Migrations are generated, never hand-written. `bun run db:generate` + `bun run db:migrate`. Committed to `db/migrations/`.
- Neon branching: every PR gets a preview branch via `scripts/db-branch.ts`. Tests run against an ephemeral branch, not a shared dev DB.

## 9. Testing

- `bun test`. Co-located `*.test.ts` next to the code. No separate `__tests__` folders.
- One test file per source file. If `auth.service.ts` exists, `auth.service.test.ts` exists.
- Unit tests mock the repo, not the DB. Integration tests use a real Neon branch via `tests/helpers/test-db.ts`.
- E2E in `tests/e2e/` hit a running Hono app with `app.request()`. No running server needed.
- Test names describe behavior in plain English: `it("rejects signup when email already exists")`. Agents reading a failing test should understand intent without reading the body.

## 10. Dependencies

- Adding a dependency requires a one-line justification in the PR description. Prefer Web Standard APIs (Hono runs on them).
- Forbidden by default: `lodash`, `moment`, `axios`, `express`, `dotenv` (Bun loads `.env` natively), `ts-node`, `nodemon`.
- Prefer: `zod`, `drizzle-orm`, `hono`, `@neondatabase/serverless`, `ulid`, `pino`.
- Node-only packages must be justified — Bun has native equivalents for most of them.

## 11. Comments and docs

- JSDoc on every exported function in `service.ts` and `repo.ts`. One-sentence summary + `@throws` for each `AppError` subclass it can raise. Agents use this to plan edits without reading the body.
- No commented-out code. Delete it; git has history.
- No TODOs without a linked issue (`// TODO(#123): ...`). Otherwise an agent will "helpfully" try to resolve them.

## 12. Agent hand-off rules

- When an agent adds a feature, it must: create the full suffix set (`routes/service/repo/schemas/types/errors/test`), mount the router in `app.ts`, add the Zod schema, add at least one test.
- When an agent adds a table, it must: add the schema file, re-export from `db/schema/index.ts`, run `bun run db:generate`, commit the migration.
- When an agent adds an env var, it must: update `env.ts` schema, update `.env.example`, and reference it via the typed `env` object.

Following these three checklists keeps the repo shape stable for the next agent that shows up.
