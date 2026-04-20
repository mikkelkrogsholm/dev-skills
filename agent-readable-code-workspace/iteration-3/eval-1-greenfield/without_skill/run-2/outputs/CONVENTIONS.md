# Conventions

Optimized for AI agents (Claude Code, Cursor) as primary maintainers. Rules are concrete so agents can apply them without judgement calls.

## 1. Architecture

- **Vertical slices** under `src/features/<domain>/`. Each slice owns its routes, service, repo, schemas, errors. Never reach into another feature's internals; go through its `*.service.ts` export.
- **Layer direction (strict):** `routes -> service -> repo -> db`. Routes never touch Drizzle. Services never touch `Context` (Hono `c`).
- **`lib/` is framework-agnostic.** No `hono`, no `drizzle-orm`, no env reads. Pure TS only.
- **`db/` holds schema and the singleton `db` client.** Schemas grouped by owning feature but all re-exported from `db/schema/index.ts`.

## 2. Naming

- **Files:** `kebab-case.ts`. Feature files: `<feature>.<role>.ts` (e.g. `users.service.ts`). One default concept per file.
- **Folders:** kebab-case, singular for slices (`auth`, `billing`), plural for collections (`features`, `middleware`).
- **Exports:** named only. No `export default` except for Drizzle config / framework-required files.
- **Types:** `PascalCase`. DTOs end in `DTO`, inputs in `Input`, queries in `Query` (e.g. `UserDTO`, `CreateUserInput`, `ListUsersQuery`).
- **Zod schemas:** same name as the type in `camelCase` + `Schema` (e.g. `createUserInputSchema`). Infer types via `z.infer`.
- **DB tables:** `snake_case` plural (`users`, `billing_invoices`). Drizzle variable matches: `export const users = pgTable('users', ...)`.
- **Errors:** `PascalCase` ending in `Error`, extending `AppError` from `lib/errors.ts`. One error class per distinct HTTP status/meaning.
- **Booleans:** `is`/`has`/`can` prefix. **Functions:** verb-first (`createUser`, not `userCreate`).

## 3. File size

- **SKILL ceiling: 250 lines per file.** Split before you hit it. Agents read whole files; large files waste context.
- **Route files:** at most one router per file, max ~150 lines. If bigger, split by resource (`users.me.routes.ts`, `users.admin.routes.ts`).
- **Functions:** max 40 lines, max 4 parameters. Use an options object past 3 params.
- **One exported symbol per file** is ideal. Two or three closely-related ones is fine. Ten is a code smell.

## 4. TypeScript

- `"strict": true`, `"noUncheckedIndexedAccess": true`, `"exactOptionalPropertyTypes": true`.
- No `any`. No `as` casts except at trust boundaries (DB row -> DTO, parsed webhook -> typed event), and only after a Zod parse.
- Return types **required** on exported functions. Inferred internally is fine.
- Prefer `type` aliases; use `interface` only when declaration merging is needed.
- No enums — use `as const` objects + `(typeof X)[keyof typeof X]` unions.

## 5. Validation and errors

- **All external input goes through Zod** at the edge: request body, query, params, webhook payloads, env. Never trust `c.req.json()` directly.
- Parse with `.parse()` inside routes (let the error handler format it). Use `.safeParse()` only when you need to branch on failure.
- Throw typed `AppError` subclasses from services. Never throw strings. Never return `null` to signal an error — throw.
- A single `middleware/error-handler.ts` maps errors to JSON. Response shape: `{ error: { code, message, details? } }`. Never leak stack traces in production.

## 6. Database (Drizzle + Neon)

- Use the Neon **serverless driver** (HTTP) for request-scoped queries. Use **pooled** connection for long-running work (jobs, migrations).
- Queries live in `*.repo.ts`. One function per query intent; name it after the intent (`findUserByEmail`, not `getUser`).
- **Never use `select *` style `db.select().from(table)` without a column list in hot paths.** Always select explicitly once the schema stabilizes.
- Migrations generated via `bun drizzle-kit generate`. Never hand-edit `db/migrations/`. Commit every generated SQL file.
- Seed is **idempotent** — running it twice must not duplicate rows. Use `onConflictDoNothing`.
- Transactions via `db.transaction(async (tx) => ...)`. Pass `tx` down through repo functions; don't capture `db` inside a transaction.

## 7. Hono

- One root `app` in `src/app.ts`. Each feature exports `<feature>Routes` (a `Hono` instance) and is mounted with `app.route('/billing', billingRoutes)`.
- Use `c.get('userId')` / `c.get('user')` — augment types in `src/types/hono.d.ts`.
- Responses go through helpers in `http/response.ts`. Don't call `c.json(...)` directly in routes except for one-off cases.
- Middleware order is fixed in `app.ts`: requestId -> logger -> cors -> rateLimit -> routes -> errorHandler.

## 8. Dependencies

- **Runtime: Bun.** Use `Bun.password`, `Bun.file`, `bun:sqlite` (tests), `bun:test` where possible before reaching for npm.
- Prefer zero-dependency solutions. New dependency must justify: (a) >100 lines saved, or (b) security-critical (crypto, auth).
- **No Node-only deps** (`fs` from node is fine via Bun, but avoid `node-fetch`, `bcrypt` — use Bun equivalents).
- Pin exact versions in `package.json` (`"hono": "4.6.3"`, not `"^4.6.3"`). Renovate/Dependabot handles bumps.
- Don't import from a feature's `*.repo.ts` or `*.routes.ts` outside that feature. `*.service.ts` is the public surface.

## 9. Testing

- `bun test`. Colocate unit tests under `tests/` mirroring `src/`. Integration tests under `tests/integration/`.
- **Unit tests:** pure service/repo functions against a real test DB (Neon branch or local Postgres). No mocking Drizzle.
- **Integration tests:** invoke `app.fetch(new Request(...))`. No live HTTP server needed.
- Each test file sets up and tears down its own data via factories (`tests/helpers/factories.ts`). No shared fixtures.
- One assertion theme per test; name format: `it('returns 401 when session is expired')`.
- Required coverage: every route has at least one integration test for happy path + one for auth/validation failure.

## 10. Environment and secrets

- All env access goes through `src/env.ts`. Zod-parsed at module load; boot fails fast on invalid config.
- **Never** read `process.env.X` outside `env.ts`.
- `.env` is gitignored. `.env.example` is committed and lists every variable with a dummy value.

## 11. Logging

- Single `logger` from `config/logger.ts`. Structured JSON only.
- Log at service boundaries: start, success (with duration), failure (with error code).
- **Never log PII** (emails, tokens, full request bodies). Log `userId`, `requestId`, and error codes.

## 12. Git and CI

- Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`.
- Branch per change. PRs must pass: `bun run typecheck`, `bun run lint`, `bun test`, `bun run build`.
- Migrations in the same PR as the schema/code that uses them.

## 13. For AI agents specifically

- When adding a capability, **add it to the existing feature slice** before creating a new one. New slices require a new bounded context, not a new endpoint.
- When unsure where something goes, check `layout.txt`. If it doesn't fit, the slice boundary is probably wrong — surface that, don't improvise.
- Always read `*.schemas.ts` and `*.errors.ts` of a feature before editing its service or routes.
- Before writing a new utility, grep `lib/` and `http/` — it probably exists.
- Prefer editing over creating. Don't add `index.ts` barrels except in `db/schema/`.
