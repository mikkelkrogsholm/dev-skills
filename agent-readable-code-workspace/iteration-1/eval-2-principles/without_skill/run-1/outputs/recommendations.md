# Structuring code for AI coding agents

A prioritized, failure-mode-grounded list of changes you can make to a codebase so that AI agents (Claude Code, Cursor, Copilot, Aider) read and modify it correctly. Ordered by impact, not by effort.

The core mental model: agents are stateless between sessions, work from a narrow context window, rely heavily on grep/semantic search rather than whole-repo understanding, and will confidently invent APIs that "look right" when they cannot verify. Your job is to make the truth cheap to discover and hard to misread.

---

## Tier 1 — Highest leverage

### 1. Make the type system the contract, and make it strict

**Failure mode:** Agents confidently generate calls to functions with the wrong argument shape, invent fields on objects, and swallow `any` / `unknown` without noticing. In JS especially, `any` propagates silently and the agent writes downstream code that "compiles" but is wrong.

**What to do:**
- TypeScript: `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`, `noImplicitOverride: true`. Ban `any` in lint (`@typescript-eslint/no-explicit-any: error`). Prefer `unknown` + narrowing.
- Python: run `mypy --strict` or `pyright` in CI. Use `from __future__ import annotations` and typed dataclasses/Pydantic models instead of dicts-as-structs.
- Validate all external inputs at the boundary with Zod / Pydantic / Valibot so that internal code has real types, not "types plus trust."
- Prefer branded/nominal types for IDs: `type UserId = string & { __brand: 'UserId' }`. Agents mix up `userId` and `orgId` constantly when both are `string`.

**Why it works:** A type error is a cheap, local, mechanically-checkable signal. It turns hallucination into a compile failure the agent can self-correct on — which is the single most reliable feedback loop agents have.

### 2. Give the agent a fast, deterministic feedback loop

**Failure mode:** Without a fast check-command, agents "finish" edits without ever running them, leave broken imports, and declare success based on pattern-matching. With a slow or flaky loop, they skip it.

**What to do:**
- Provide one command that does type-check + lint + unit tests in under ~30 seconds for a small change (e.g. `bun run check` or `pnpm check`). Document it at the top of `CLAUDE.md` / `AGENTS.md` / `README.md`.
- Make tests hermetic. No network, no real databases, no wall-clock dependencies. Use fakes/in-memory DBs. Agents cannot debug a flaky test — they will either retry forever or disable it.
- Output must be machine-readable: prefer tools that print file:line:col + error code. Agents grep errors; novels don't help.
- Fail loudly on warnings in CI; agents ignore warnings.

**Why it works:** Agents iterate on whatever signal you give them. A 3-second red/green loop yields correct code; a 3-minute loop yields shortcuts.

### 3. Write a short, honest `AGENTS.md` / `CLAUDE.md` at the repo root

**Failure mode:** The agent spends its context window re-discovering conventions (where tests live, what the build command is, which package manager, which ORM), or worse, invents them. Every session starts from zero.

**What to do:** Keep it under ~200 lines. Include:
- Commands: install, dev, test, typecheck, lint, format, single-test invocation.
- Project layout: where routes, components, server code, migrations live — one sentence each.
- Non-obvious conventions: "we never import from `src/internal/*` outside that folder", "DB access only via `src/db/queries/`", "all dates are UTC ISO strings at API boundaries".
- Forbidden patterns: "do not add new `any`", "do not introduce new dependencies without asking", "do not modify `generated/`".
- What *not* to touch: vendored code, generated files, migration history.

Do **not** duplicate information that lives in code. Point at the file instead.

### 4. Prefer explicitness over cleverness at module boundaries

**Failure mode:** Agents follow imports. If they can't find a symbol via grep or an IDE jump, they assume it doesn't exist and reimplement it. Barrel files (`index.ts` re-exports), dynamic dispatch, metaprogramming, and string-based registries all defeat this.

**What to do:**
- Minimize `export *` and deep re-export chains. Let consumers import from the defining file.
- Avoid decorators / metaclasses / monkey-patching for core behavior. If framework-idiomatic (NestJS, Django), fine — but don't roll your own.
- Avoid magic strings that map to handlers (`registerHandler("user.created", ...)` spread across 40 files). Prefer an explicit discriminated union or a single registry file.
- Name things so that a grep for the feature name finds everything. If a feature is called "checkout", every file related to it should contain that string.

### 5. Collocate code, tests, types, and schema

**Failure mode:** Agent edits `UserService.ts` but misses the test in `/tests/unit/services/user.test.ts`, the type in `/types/user.d.ts`, the Zod schema in `/schemas/user.ts`, and the OpenAPI in `/docs/api.yaml`. Code and its contract drift apart.

**What to do:** Put `foo.ts`, `foo.test.ts`, `foo.types.ts`, `foo.schema.ts` in the same directory. When the agent opens one, it sees the rest. This is worth more than "clean" top-level folder structures.

---

## Tier 2 — High leverage

### 6. Keep files small and single-purpose — but not too small

**Failure mode:** A 2000-line file blows the context window; the agent edits a fragment and breaks invariants it never saw. Conversely, 40 three-line files force the agent to grep 20 times to understand one change.

**Rule of thumb:** aim for 100–400 lines per file. Split by *behavior boundary*, not by arbitrary rules like "one class per file".

### 7. Make errors carry structured, localizable information

**Failure mode:** `throw new Error("Invalid input")` — agent has no way to find the source, no way to handle it distinctly, no way to test for it. It ends up catching `Error` and guessing.

**What to do:**
- Use typed error classes or tagged error unions (`Result<T, E>` / `neverthrow` / Effect). Each error has a code.
- Include the offending value and a stable error code: `new ValidationError({ code: 'USER_EMAIL_TAKEN', email })`.
- Never `catch (e) {}` silently. Agents propagate this pattern virally.

### 8. Pin conventions mechanically, not socially

**Failure mode:** "We use camelCase for DB columns" lives in someone's head. Agent adds `snake_case` columns because the ORM example uses them. Now you have both.

**What to do:**
- ESLint / Biome / Ruff rules over docs.
- Prettier / dprint / Biome format on save and in CI.
- Custom lint rules for project-specific invariants: "no direct imports from `@/components/ui` outside `@/components`", "no `process.env` outside `@/env.ts`".
- A `schema.ts` + generated types instead of hand-maintained parallel definitions.

### 9. One source of truth per fact, with generation downstream

**Failure mode:** The DB schema, the TS type, the Zod validator, and the OpenAPI spec all describe "User" independently. Agent updates one and the others drift. Bugs surface weeks later.

**What to do:** Pick a source (e.g. Drizzle schema, Prisma schema, or a Zod schema) and *generate* the rest. `drizzle-zod`, `prisma-zod-generator`, `zod-to-openapi`, `ts-to-zod`, etc. The agent's job becomes "edit one place" instead of "find and sync four places."

### 10. Keep dependencies conservative and stable

**Failure mode:** Agent picks up a library in `package.json`, writes code using the v2 API, but you're on v4. Or it adds a new dep that overlaps with one you already have.

**What to do:**
- Minimize the dep list. Each dep is a surface the agent will try to use.
- Pin versions (no `^` for anything load-bearing) so the agent's training-data memory of the API matches reality.
- A short note in `AGENTS.md`: "We use `zod`, not `yup`. We use `drizzle`, not `prisma`. Do not introduce alternatives."
- Prefer libraries with stable APIs and public `llms.txt` / good docs. Agents do better with Hono than with a bespoke internal router.

---

## Tier 3 — Meaningful polish

### 11. Write docstrings/JSDoc on public functions — short, input/output focused

Not prose. Types + one sentence of *why*, plus any invariant that isn't expressible in types ("caller must hold the tx lock", "throws if the user is soft-deleted"). Agents read these and condition on them.

### 12. Name booleans and flags unambiguously

`isDryRun`, `allowUnsafe`, `shouldEmail` — not `flag`, `mode`, `opt`. Agents will invert booleans when names are ambiguous. Prefer enums/string literals over booleans once you have more than two states: `mode: 'dry-run' | 'execute' | 'plan'`.

### 13. Make side effects explicit and injectable

**Failure mode:** A function reads `process.env`, calls `Date.now()`, hits the network, and writes to the filesystem — none of it visible from its signature. Agent can't test it and doesn't realize it's stateful.

**What to do:** Pass `clock`, `env`, `db`, `fetch`, `logger` as arguments (or via a small context object). Agents recognize this pattern and write testable code when they see it. Ban `new Date()` and raw `process.env` outside a central module; enforce with lint.

### 14. Keep migrations, fixtures, and seed data in code, not in prose

If onboarding requires "run these SQL snippets Slack'd to you in 2023", the agent can't reproduce state. Commit it as migrations + seed scripts. The agent can then reset and retry.

### 15. Comment the non-obvious *why*, delete the obvious *what*

`// increment counter` on `counter++` is noise. `// Stripe returns cents; we store dollars` is gold. Agents will propagate noise comments and miss the one that matters if it's buried. Delete the noise.

### 16. Avoid "stringly-typed" APIs

`updateUser(id, { field: 'email', value: 'x' })` is worse than `updateUserEmail(id, email)`. Strings hide coupling from grep and from the type-checker, which is exactly where agents work.

### 17. Keep the repo's public surface small

One entrypoint per package. A `src/index.ts` that exports what's public, and nothing else. Agents asked to "use the library" will otherwise reach into internals and create coupling you didn't intend.

### 18. Deterministic test order and deterministic IDs in tests

Agents cannot debug "fails 1 in 10 runs". Seed all randomness, freeze time, use sequential IDs. If a test uses `uuid()` directly, it will eventually produce a flaky snapshot.

### 19. Prefer "boring" stacks the agent has seen a million times

A vanilla Postgres + Drizzle + Hono + React setup will have 100x better agent performance than a bespoke EffectTS + XState + custom-DSL stack, even if the latter is technically superior. This is a legitimate engineering tradeoff now, not snobbery.

### 20. Leave breadcrumbs, not maps

Instead of a `docs/architecture.md` that goes stale, leave one-line comments at the top of each key file: `// Entry point for background jobs. See src/jobs/README.md for the queue model.` Agents follow links; they don't read unprompted architecture docs.

---

## Anti-patterns to actively remove

- **Re-export barrels** (`index.ts` files that do nothing but `export * from './foo'`). They defeat grep.
- **"Magic" DI containers** where the resolver key is a runtime string. Agents cannot trace these.
- **Multi-repo monorepos without workspace configuration.** Agents can't find symbols across them.
- **Config in five places** (`.env`, `config.ts`, `package.json`, `turbo.json`, runtime flags) with unclear precedence. Centralize.
- **Dead code and commented-out blocks.** Agents will "restore" them or pattern-match from them.
- **TODO comments older than a month.** Agents will treat them as active guidance.
- **Pre-commit hooks that rewrite files unpredictably** (e.g. auto-import sorters that fight the agent's edits). Make them idempotent or remove them.
- **Silent failure modes** (`try { x() } catch {}`, `?.()` swallowing everything, returning `null` on error without a type). Agents copy these patterns.

---

## A minimal checklist you can apply this week

1. Enable strict type-checking and ban `any`.
2. Write `AGENTS.md` with commands + conventions + forbidden patterns.
3. Ensure `<one-command> && echo OK` runs typecheck + lint + tests in under 30s.
4. Collocate tests with source.
5. Delete `export *` barrels that add no value.
6. Pick one source of truth for your data model and generate the rest.
7. Pin dependency versions.
8. Add a lint rule forbidding raw `process.env` / `new Date()` outside designated modules.
9. Rename ambiguous booleans and stringly-typed APIs.
10. Delete dead code and stale TODOs.

Done consistently, these changes convert an "agents frequently break things" codebase into an "agents reliably make correct edits on the first try" codebase. The theme is always the same: **make the truth mechanically checkable, locally discoverable, and singular.**
