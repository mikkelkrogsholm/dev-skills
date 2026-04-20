# Making Code Easier for AI Coding Agents to Read and Modify

A prioritized, practical guide for structuring code so agents (Claude Code, Cursor, Copilot, Aider) read it correctly and modify it safely. Each recommendation is grounded in a specific failure mode observed in practice.

Priorities are ordered by expected impact on agent correctness per unit of effort.

---

## Tier 1 — Highest impact (do these first)

### 1. Make the module boundary obvious from the filename and location

**Failure mode:** Agents search by filename and pattern. When `user.ts` contains the HTTP handler, DB model, validation, and email side-effects all mixed together, the agent patches the wrong layer. A request to "fix the email bug" ends up editing the DB query because both live in the same file.

**Do:**
- One concern per file. `users/routes.ts`, `users/repository.ts`, `users/schema.ts`, `users/mailer.ts`.
- Filename should predict contents. If you would need a comment to explain what a file is for, rename the file.
- Keep the tree shallow enough that an agent can `ls` a directory and understand the module. Two or three levels of nesting is plenty.

**Example:**
```
# Bad
src/user.ts           # 800 lines, everything user-related

# Good
src/users/http.ts     # Express/Hono handlers only
src/users/repo.ts     # DB queries only
src/users/schema.ts   # Zod schemas
src/users/mailer.ts   # Email side-effects
```

### 2. Co-locate the contract with the implementation

**Failure mode:** Agents frequently hallucinate type signatures when the type lives in `@types/` or a distant `schemas/` folder. They edit the implementation, the types drift, and the build breaks.

**Do:**
- Put the Zod/TypeScript/JSON-schema definition in the same file as the function that uses it, or a sibling file imported at the top.
- Export the inferred type next to the schema: `export type User = z.infer<typeof UserSchema>`.
- Never split a type across multiple files via `interface` merging — agents miss one of the declarations.

### 3. Write explicit, shallow control flow

**Failure mode:** Agents misread nested ternaries, chained optional calls, and clever reduce-based pipelines. They produce edits that look right lexically but change the semantics.

**Do:**
- Replace `a?.b?.c?.d ?? fallback` with named intermediate variables when the chain carries logic.
- Prefer early returns over nested `if/else`. Agents handle a flat list of guard clauses far better than a deep tree.
- Avoid one-line ternaries inside JSX props and function arguments — lift to a named variable.

**Example:**
```ts
// Bad — agent asked to "return null for banned users" will break this
return user?.subscription?.plan?.features?.includes('x')
  ? render(user.data ?? emptyState, mode === 'full' ? fullProps : slimProps)
  : null;

// Good
if (!user) return null;
if (user.banned) return null;
const plan = user.subscription?.plan;
const hasFeature = plan?.features?.includes('x') ?? false;
if (!hasFeature) return null;
const props = mode === 'full' ? fullProps : slimProps;
const data = user.data ?? emptyState;
return render(data, props);
```

### 4. Name things for what they are, not how they are used

**Failure mode:** A variable named `data` or `result` forces the agent to read the whole function to infer its shape. The agent then edits based on a guess.

**Do:**
- `user` not `data`. `activeOrders` not `items`. `parsedPayload` not `result`.
- Booleans start with `is`, `has`, `should`, `can`.
- Functions that return values are nouns or `get*`. Functions that mutate are verbs. Do not mix.
- Avoid abbreviations that are not universal (`usr`, `ctx` is fine, `prcRqst` is not).

### 5. Make side effects impossible to miss

**Failure mode:** Agents refactor a function thinking it is pure, but it actually writes to a DB, sends an email, or mutates a global. The refactor removes the side effect silently.

**Do:**
- Put side-effecting functions in files named for the effect: `mailer.ts`, `writer.ts`, `publisher.ts`.
- Name side-effecting functions with imperative verbs: `sendWelcomeEmail`, `writeAuditLog`, `publishOrderEvent`.
- Functions returning a value should have no side effects. If they must, name accordingly: `createUserAndNotify`.
- Never hide I/O inside a getter or a `use*` hook body without a clear name.

---

## Tier 2 — Reduce context load

### 6. Keep files short enough to fit in a single read

**Failure mode:** When a file exceeds ~500 lines, agents read it in chunks and miss cross-references. They add a duplicate helper at the bottom because they did not see the existing one at the top.

**Do:**
- Soft cap files at 300 lines, hard cap at 500.
- If a file is long because it contains many small related functions (e.g. a router), add a table-of-contents comment at the top listing exported names.
- Split by feature, not by layer within a feature.

### 7. Put imports and exports at the file boundaries, not scattered

**Failure mode:** Dynamic `require()` calls mid-function, re-exports through deep barrel files (`index.ts` re-exporting `index.ts` re-exporting `index.ts`), and circular deps break agent navigation. `Go to definition` jumps to the barrel, not the implementation.

**Do:**
- All imports at the top of the file. No conditional imports unless absolutely required (and then comment why).
- One level of barrel file maximum. Prefer direct imports: `import { X } from './users/repo'` over `import { X } from './users'`.
- Export each symbol from exactly one place. Agents get confused when the same symbol is importable from three paths.

### 8. Keep public interfaces small and documented inline

**Failure mode:** An agent asked to add a new method to a class reads only the class declaration. If the public contract is spread across base classes, mixins, and declaration merging, the agent adds a method that conflicts with an existing inherited one.

**Do:**
- Prefer composition to inheritance. Flat objects of functions beat class hierarchies.
- If you use classes, keep them shallow — no base-class-of-base-class.
- Document the public API with a single JSDoc block per exported symbol. Include a one-line usage example in the comment.

### 9. Write tests that serve as executable examples

**Failure mode:** Agents writing new features look at existing tests to learn the patterns. If tests are heavy on mocks, indirection, and shared setup helpers, the agent writes new tests that diverge wildly and fail CI.

**Do:**
- Prefer simple arrange-act-assert. One assertion focus per test.
- Keep fixtures inline or in a `__fixtures__/` sibling folder, not in a deep `testutils/` tree.
- Name tests as full sentences: `it('returns 404 when user is not found')`.
- Avoid shared mutable test state. Every test should be readable standalone.

### 10. Make configuration declarative and centralized

**Failure mode:** Environment variables read in 12 different files, with inconsistent defaults and parsing, mean the agent cannot confidently add a new one without breaking a subset of call sites.

**Do:**
- One `env.ts` (or `config.ts`) that reads and validates all env vars once (e.g. with Zod), exports a typed object.
- Everywhere else imports from that object. Never `process.env.FOO` outside `env.ts`.
- Same rule for feature flags, constants, URLs.

---

## Tier 3 — Agent-specific affordances

### 11. Keep a machine-readable project map

**Failure mode:** Agents spend their context budget exploring the tree. In a large repo, they run out of tokens before making changes.

**Do:**
- Maintain a `CLAUDE.md` / `AGENTS.md` / `.cursorrules` at the root listing: the stack, where to find things, how to run tests, house style quirks (e.g. "we use tabs", "never commit to main").
- Include a 10-line map: "HTTP handlers live in `src/routes/`. Domain logic in `src/services/`. DB access in `src/repo/`."
- Keep it under 200 lines. Longer and it stops getting read fully.

### 12. Make the "how to run it" trivial

**Failure mode:** An agent tries `npm test` when the project uses `pnpm test`, or runs one test file directly when the runner expects `vitest run path`. It gets an error, interprets it as a code bug, and "fixes" code that was correct.

**Do:**
- Document the exact commands in the agent rules file: install, dev, test, typecheck, lint, single-test.
- Make `make test` or `npm test` work without arguments. If the project needs `docker-compose up -d` first, say so in two adjacent lines.
- Have typecheck and lint return fast and with clear error locations. Agents parse tool output — if your linter prints banners and progress bars, it is harder to parse.

### 13. Prefer plain data structures over clever abstractions

**Failure mode:** An agent asked to add a field to a resource breaks three decorator-based code generators, a metaprogrammed DI container, and a runtime proxy — all invisible from the file it was editing.

**Do:**
- Avoid decorators for domain types unless the framework requires them (NestJS, TypeORM). Plain objects and functions are easier to reason about.
- Avoid runtime metaprogramming (`Proxy`, dynamic property access via strings) in anything the agent might edit.
- Favor boring imperative code in the core domain. Save cleverness for genuine infrastructure layers.

### 14. Make errors carry enough context to self-diagnose

**Failure mode:** Agents read stack traces to decide what to edit. A generic `Error: validation failed` sends the agent on a wild goose chase; a structured error with the offending field name points straight at the fix.

**Do:**
- Throw errors with the specific value and location: `throw new Error(\`Expected number for user.age, got \${typeof age}: \${age}\`)`.
- Use error classes (`NotFoundError`, `ValidationError`) so callers and the agent can pattern-match.
- Log in structured JSON in production code paths; humans and agents both parse it faster.

### 15. Use comments for "why", and mark agent pitfalls explicitly

**Failure mode:** An agent refactors away a load-bearing `setTimeout(0)` or a try/catch-around-nothing because it looks like dead code.

**Do:**
- Comment non-obvious invariants: `// Must run synchronously — React batches state updates outside event handlers`.
- When you write code that looks wrong but is right, say so: `// eslint-disable-next-line no-await-in-loop — rate limit requires sequential`.
- Do not write comments restating what the code obviously does. Agents skip those and they add noise.

### 16. Pin and document external contracts

**Failure mode:** Agent upgrades a package minor version as part of an unrelated change; an API signature changed; runtime breaks on the next deploy.

**Do:**
- Pin exact versions in `package.json` for anything that crosses a network boundary (SDKs, API clients). Or use a lockfile and commit it — but tell the agent not to regenerate it casually.
- When you integrate with an external API, store the OpenAPI/GraphQL schema in the repo, not just at runtime. Agents can grep a file; they cannot grep a live endpoint reliably.
- Prefer generated clients over hand-written HTTP calls for any third-party API — the types force correctness.

### 17. Prefer schemas over convention for data at boundaries

**Failure mode:** Agent edits a handler, adds a field to the response, forgets to update the frontend type. Runtime: `undefined is not a function` two weeks later in production.

**Do:**
- Every HTTP endpoint has a request + response schema (Zod, Valibot, TypeBox).
- The schema is the single source of truth: backend parses requests with it, frontend imports the inferred type.
- Same for queue messages, webhook payloads, config files.

---

## Tier 4 — Codebase hygiene that compounds

### 18. Delete dead code aggressively

**Failure mode:** Agent reads a commented-out block or unused export and assumes it is relevant context. Spends tokens "preserving" patterns that the team abandoned.

**Do:**
- Remove commented-out code. Use git history instead.
- Remove exported functions nobody imports. Use a tool: `ts-prune`, `knip`, or your linter's `no-unused-exports`.
- Remove deprecated flags and legacy branches immediately after migration — do not leave them for "later".

### 19. One convention per concern, enforced by tooling

**Failure mode:** Codebase has three patterns for error handling (`Result<T, E>`, thrown errors, callbacks). Agent picks one uniformly; half the codebase breaks because it relied on a different one.

**Do:**
- Pick one: error handling style, async style (promises vs async/await), state management, form library, date library.
- Enforce with ESLint / Biome rules where possible.
- If you have an intentional exception, put a comment at the top of that file explaining why.

### 20. Write type-safe code end-to-end

**Failure mode:** Agent generates code that typechecks locally but breaks at the network boundary because `any` leaked through. Types are the agent's primary feedback signal.

**Do:**
- No `any` in committed code. Use `unknown` and narrow.
- Turn on `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` in `tsconfig.json`.
- Run `tsc --noEmit` in CI and tell the agent to run it before committing.

### 21. Keep diffs small and commits semantic

**Failure mode:** Agent given a branch with a 2000-line diff can't distinguish intent from incidental change and reproduces the mess.

**Do:**
- One logical change per commit. Commits should describe "why", not just "what".
- Separate formatting commits from behavior commits. Configure Prettier/Biome so agents don't fight with it.
- If a refactor is mechanical (rename, move), do it in its own commit so the agent can skip it during review.

### 22. Provide seeds, fixtures, and a repeatable local environment

**Failure mode:** Agent can't verify its changes because the dev DB is empty or the integration test requires credentials. It commits blind.

**Do:**
- `make dev` (or equivalent) should bring up the full stack on a clean machine. Seed data included.
- Integration tests against real services use containers or recorded fixtures; never hit production-like endpoints by default.
- If something requires a secret to test, document the minimum viable fake and provide it.

---

## Anti-patterns to avoid

These patterns are individually survivable but compound badly for agents:

- **String-based routing and event names.** `emit('user:created')` scattered across the codebase with no central registry. Agents miss subscribers on rename.
- **Implicit globals.** Singletons initialized on import, prototype extensions, monkey-patched built-ins. Invisible dependencies break agent reasoning.
- **Macros, codegen, and magic.** If a file is generated, say so in the first line and mark it read-only. If decorators rewrite method bodies, the agent will not know.
- **Framework cleverness as the public API.** Exposing `React.memo(forwardRef(...))` HOC stacks makes the signature unreadable. Wrap with a named component.
- **Inconsistent path aliases.** `@/utils` in one file, `../../utils` in another, `~/utils` in a third. Pick one. Configure once. Use everywhere.
- **"Private" naming conventions that are not enforced.** If `_internal` is imported from outside, it is public. Make it private with tooling or accept that it is public.

---

## A minimum viable checklist

If you do only ten things:

1. One concern per file, filenames predict contents.
2. Types live next to the code that uses them.
3. Flat control flow, named intermediates, early returns.
4. Descriptive names, not `data` / `result` / `tmp`.
5. Files under 300 lines; no dynamic imports.
6. One env.ts, one config source.
7. `CLAUDE.md` with stack, layout, commands.
8. Strict TypeScript, no `any`, schemas at every boundary.
9. One convention per concern, enforced by linter.
10. `make dev` and `make test` work on a clean clone.

An agent editing a codebase that follows these ten rules will spend its context on the actual problem, not on figuring out your project.
