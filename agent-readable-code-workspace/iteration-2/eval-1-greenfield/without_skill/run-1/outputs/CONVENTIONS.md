# Conventions

This service is built to be maintained primarily by AI agents (Claude Code, Cursor). Every rule here exists to make code easier for an agent to locate, read in one pass, and modify safely.

## Core principle

**One concept per file. Predictable names. Short files.** An agent should be able to guess the path from a feature name without grep.

## Directory and file naming

- All files and directories: `kebab-case`. No `camelCase` or `PascalCase` filenames.
- Feature folders go under `src/features/<feature>/`. Nothing else lives there.
- Inside a feature, files follow the pattern `<feature>.<role>.ts`:
  - `.routes.ts` — Hono router only; no business logic
  - `.service.ts` — business logic; pure functions that take `db` and deps as args
  - `.repo.ts` — all Drizzle queries for this feature (the only place `db` is called)
  - `.schemas.ts` — Zod request/response schemas
  - `.types.ts` — inferred types (`z.infer<...>`) and domain types
  - `.errors.ts` — feature-specific `AppError` subclasses (optional)
  - `.test.ts` — colocated tests
- Do not create `index.ts` barrels inside a feature. Import the exact file. Barrels hide dependencies from agents.
- One top-level `src/db/schema.ts` is the single re-export of all tables. Drizzle-kit needs this.

## Symbol naming

- Types and classes: `PascalCase`. `User`, `CreateUserInput`, `AppError`.
- Functions, variables, Zod schemas: `camelCase`. `createUser`, `createUserSchema`.
- Constants (true constants only): `SCREAMING_SNAKE_CASE`. `MAX_UPLOAD_BYTES`.
- Route handler functions: verb-noun. `createUser`, `listUsers`, `getUserById`.
- Zod schema suffix: always `Schema`. Inferred type drops it: `UserSchema` -> `User`.
- Env vars: `SCREAMING_SNAKE_CASE`, grouped by prefix (`DATABASE_`, `STRIPE_`, `RESEND_`).

## File size

- Hard cap: **300 lines per file**. If you hit 300, split.
- Soft target: **~150 lines**. Agents read one file at a time more accurately than scrolling.
- A single function should fit on one screen (~50 lines). Extract helpers into the same file, below the caller.
- Files longer than 300 lines signal a missing abstraction; split by role (move queries to `.repo.ts`, schemas to `.schemas.ts`) before splitting by arbitrary boundaries.

## Imports

- Use path alias `@/` for `src/`. Configure in `tsconfig.json` and Bun.
- Order: node/bun builtins -> external packages -> `@/` internal -> relative `./`.
- No cross-feature imports between `features/*`. If feature A needs feature B, it calls B's `service.ts` via an explicit import, never B's `repo.ts` or `routes.ts`.
- `db` is only imported inside `*.repo.ts`, `db/`, and `test/`. Services receive `db` as a parameter. This makes services trivially testable and makes data access greppable.

## Dependency rules

- Direction: `routes -> service -> repo -> db`. Never reverse.
- `lib/` has zero feature imports. It is leaf code.
- `integrations/` wraps every third-party SDK. No feature imports `stripe` or `resend` directly; they import from `@/integrations/stripe`.
- Add a new dependency only if it saves >100 lines or provides security-critical code. Prefer the standard library and Bun primitives.
- Pin exact versions in `package.json` (no `^` or `~`). Upgrades are explicit commits.

## Hono patterns

- `src/app.ts` builds the app and returns it. `src/index.ts` calls `Bun.serve` with `app.fetch`. Never mix.
- Mount each feature's router with a clear prefix: `app.route('/users', usersRoutes)`.
- Validation: always `zValidator('json', schema)` or `('query', schema)` in route definitions. Never validate inside services.
- Attach typed values to context via `c.var.user`, `c.var.requestId`. Declare them in `src/types/hono.d.ts`.

## Drizzle patterns

- One table per domain concept, defined in `src/db/schema/<area>.ts`.
- Re-export every table from `src/db/schema.ts`. Drizzle-kit reads only that file.
- Never call `db` in a route handler. Repos only.
- Migrations are generated (`drizzle-kit generate`) and committed. Never hand-edit generated SQL.

## Errors

- Throw `AppError` subclasses with `.status` and `.code`. `error.middleware.ts` maps them to JSON responses.
- Never throw strings or plain `Error` from a service. Unknown errors are caught by the middleware and logged as 500.
- Error codes are `SCREAMING_SNAKE_CASE` and stable. Clients key off them.

## Environment

- All env access goes through `src/env.ts`, which parses `process.env` with Zod and exports a typed `env`.
- Code imports `env.DATABASE_URL`, never `process.env.DATABASE_URL`. Missing vars fail at boot, not at request time.

## Testing

- Runner: `bun test`. Test files colocated as `*.test.ts` next to the code.
- Each feature has at least: one route-level integration test (hits `app.fetch`), one service-level unit test.
- Use `src/test/factories.ts` for entity builders. Never inline fixture objects longer than 5 lines inside a test.
- Tests run against a real Postgres (Neon branch or local). No mocking the db. Mocking Drizzle produces tests that lie.
- External SDKs (Stripe, Resend) are mocked by swapping the integration module in `src/integrations/`.
- Every test is independent: truncate tables in `beforeEach` or use transactions that roll back.
- Test names are full sentences: `it('returns 409 when email already exists', ...)`.

## Comments and docs

- Comment the *why*, never the *what*. If the code needs a *what* comment, rename variables.
- Every feature folder gets no README. The file layout is the documentation.
- Public service functions get a one-line JSDoc stating inputs, outputs, and side effects. Agents use this more than humans do.
- TODOs must include an owner and a date: `// TODO(mikkel, 2026-05): drop legacy column`.

## Git and PRs

- One feature change per PR. Do not mix refactor + feature.
- Commit messages: `feat(users): add email verification`. Scope is always the feature folder name.
- Generated files (migrations, lockfile) get their own commit when possible.

## What to ask before adding code

1. Does this belong in an existing feature folder, or is it a new feature?
2. Is this the right layer (route/service/repo/lib)?
3. Will this file exceed 300 lines? If yes, split first.
4. Can an agent find this by guessing the path? If not, rename.
