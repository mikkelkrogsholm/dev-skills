# Conventions

Opinionated rules for this Hono + Drizzle + Postgres (Neon) + Bun API. Optimized for AI-agent readability: predictable file locations, short files, explicit types.

## 1. Architecture

- **Feature-sliced.** All domain code lives in `src/features/<feature>/`. A feature owns its routes, service, repo, schema, DTOs, and tests. No cross-feature imports except through a feature's public surface (`routes.ts` and exported types from `dto.ts`).
- **Layer per file, not per folder.** Inside a feature, layers are files with suffixes (`.routes.ts`, `.service.ts`, `.repo.ts`), not subdirectories.
- **Dependency direction:** `routes → service → repo → db`. Never skip upward, never call downward.
  - `routes.ts`: HTTP only (parse input, call service, format response). No DB, no business rules.
  - `service.ts`: Business logic. Pure-ish functions. May call repos and other services.
  - `repo.ts`: Drizzle queries only. Returns plain objects. No validation, no HTTP.
- **Shared code lives in `src/lib/` (pure utilities) or `src/http/` (HTTP-layer helpers).** If it's used by 2+ features, lift it.

## 2. Naming

- **Files:** `kebab-case.ts`. Suffixes are semantic: `.routes.ts`, `.service.ts`, `.repo.ts`, `.schema.ts`, `.dto.ts`, `.test.ts`.
- **Directories:** `kebab-case`, plural for collections (`features/users/`), singular for concepts (`db/`, `http/`).
- **Exports:** Named exports only. No default exports (hurts grep and refactors).
- **Types/Interfaces:** `PascalCase`. Prefer `type` over `interface` unless declaration merging is needed.
- **Functions/Variables:** `camelCase`. Booleans: `isX`, `hasX`, `canX`.
- **Constants:** `SCREAMING_SNAKE_CASE` for true constants; `camelCase` for configured values.
- **Drizzle tables:** snake_case in SQL, camelCase in TS (`users`, `userSessions`). Table variable name matches SQL name.
- **Zod schemas:** suffix with `Schema` (`CreateUserSchema`). Inferred types drop the suffix (`type CreateUser = z.infer<typeof CreateUserSchema>`).
- **Hono route handlers:** inline arrow functions in `routes.ts`. Keep bodies <15 lines; extract logic to service.

## 3. File size

- **Hard cap: 200 lines per file.** If approaching, split.
- **Functions: 40 lines max.** Extract helpers.
- **Routes files:** one Hono router per feature, one handler per endpoint. If >8 endpoints, split by subresource (e.g., `users.routes.ts` + `users.admin.routes.ts`).
- **Schema files:** if a feature has >5 tables, split into `<feature>.schema/<table>.ts` and re-export.

## 4. Imports

- **Path alias `@/` maps to `src/`.** Always use `@/...` for cross-directory imports; relative imports only within the same feature folder.
- **Import order** (enforced by linter):
  1. Node/Bun builtins
  2. External packages
  3. `@/` internal imports
  4. Relative imports
  5. Type-only imports last (`import type { ... }`)
- **No barrel files** except `db/schema.ts` (re-exports all table schemas for drizzle-kit). Barrels defeat tree-shaking and hurt agent navigation.

## 5. Dependencies

- **Runtime: Bun only.** Use `bun install`, `bun run`, `bun test`. Lockfile: `bun.lock` (committed).
- **Allowlist-minded.** Every new dep requires justification in the PR. Prefer stdlib/Bun/Hono builtins.
- **Pinned versions.** No `^` or `~` in `package.json` for production deps; exact versions. Dev deps may use `^`.
- **Core stack (do not substitute without discussion):**
  - `hono` — web framework
  - `drizzle-orm`, `drizzle-kit` — ORM + migrations
  - `@neondatabase/serverless` — Postgres driver (HTTP/WebSocket)
  - `zod` — runtime validation (single source of truth for input schemas)
- **Forbidden:** `express`, `prisma`, `sequelize`, `pg` (use Neon driver), `dotenv` (Bun loads `.env` natively), `ts-node`, `nodemon`.

## 6. Validation & errors

- **All external input validated with Zod** at the route boundary via `zValidator` middleware. Services receive already-typed input.
- **Throw typed `AppError` subclasses** from `src/http/errors.ts`. Never throw strings or raw `Error`. The global `onError` handler maps them to HTTP responses.
- **Repo layer never throws for "not found"** — returns `null` or `undefined`. Services decide whether that's a 404.
- **Never swallow errors.** If you catch, you log (with `requestId`) and rethrow or convert to `AppError`.

## 7. Database (Drizzle + Neon)

- **One Drizzle client, imported from `@/db/client`.** Do not instantiate elsewhere.
- **Migrations are generated, never hand-written.** Run `bun run db:generate` after schema changes. Commit generated SQL.
- **IDs: `ulid` (26-char string) as primary keys** unless there's a reason otherwise. Stored as `text` with `notNull()`.
- **Timestamps: `createdAt`, `updatedAt` on every user-facing table**, `timestamp({ withTimezone: true })`, defaulted to `now()`.
- **Soft deletes:** `deletedAt` column, not a `isDeleted` boolean. Repo queries filter it by default; hard-delete requires an explicit repo function.
- **No raw SQL** except in migrations or explicit `sql\`\`` for features Drizzle can't express. Document why.

## 8. Testing

- **Framework: `bun test`.** No Jest, no Vitest.
- **Co-located.** `foo.service.ts` → `foo.service.test.ts` in the same folder.
- **Pyramid:**
  - Unit tests for services/utilities (fast, no DB).
  - Integration tests for routes hit a real Postgres (test branch on Neon or local Postgres via Docker). Use transactions that rollback per test.
  - No mocking the DB. Mock external HTTP (Stripe, email) via `msw` or Bun's `fetch` mock.
- **Naming:** `describe('usersService.createUser', ...)` → `it('rejects duplicate email', ...)`.
- **Coverage is not a target**, but every bug fix ships with a regression test.

## 9. Env & config

- **`src/env.ts` defines a Zod schema for `process.env` and exports a typed `env` object.** Import `env` everywhere; never read `process.env` directly outside this file.
- **`.env.example` is the source of truth for required vars.** Keep it in sync.
- **Secrets never logged.** The logger has a redact list for `authorization`, `cookie`, `password`, `token`.

## 10. HTTP conventions

- **JSON only.** `Content-Type: application/json`. No form bodies outside webhooks.
- **Response shape:**
  - Success: `{ data: T }` or `{ data: T[], pagination: {...} }`
  - Error: `{ error: { code: string, message: string, details?: unknown } }`
- **Pagination: cursor-based** (`?cursor=...&limit=...`) unless a resource is bounded (<1000 rows), in which case offset is fine.
- **Versioning:** URL-prefixed (`/v1/...`). Breaking changes bump the prefix.
- **Idempotency:** `POST` mutations that may be retried accept `Idempotency-Key` header.

## 11. Git & PRs

- **Conventional Commits.** `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`.
- **One feature per PR.** Migrations go in their own PR when possible.
- **Every PR must:** pass `bun run check` (typecheck + lint + test), update `.env.example` if env changed, update this file if a convention changed.

## 12. AI-agent notes

- **File paths are stable and predictable.** If you need "the users service," it is at `src/features/users/users.service.ts`. Always.
- **Grep-friendly.** Named exports + suffix-based naming mean `users.service` finds exactly one file.
- **No magic.** No decorators, no DI containers, no metadata reflection. Plain functions and objects.
- **Comments explain *why*, not *what*.** The code says what; comments say why it isn't obvious.
