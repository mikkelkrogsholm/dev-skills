# Structuring Code for AI Agent Maintainers

A prioritized, failure-mode-grounded list of things that measurably improve how well Claude Code, Cursor, Copilot, and Aider read and modify a codebase. Each item names the concrete failure it prevents, not a generic virtue.

The ordering reflects real impact in agent workflows: items near the top prevent the most common categories of broken edits; items near the bottom are refinements.

---

## Tier 1 — The highest-leverage changes

### 1. Make the repo navigable by grep and filename, not by memory

**Failure it prevents:** Agents open the wrong file, invent symbols that don't exist, or edit a duplicate of the thing the user meant. This happens because the agent's first move is almost always `Grep` or `Glob` — and if the result is ambiguous, it guesses.

**Do:**
- Give every concept exactly one home. If `User` is defined in `src/domain/user.ts`, do not also export a `User` alias from `src/types/index.ts`. Agents will pick the wrong one.
- Name files after the primary exported symbol: `createCheckoutSession.ts`, not `utils.ts` or `helpers.ts`.
- Avoid `index.ts` barrel files that re-export everything. They make `Grep "createCheckoutSession"` return the definition AND five re-export hits, and agents often edit the barrel instead of the source.
- Keep filenames globally unique across the repo where possible. Ten files called `types.ts` is a navigation tax paid on every turn.

**Concrete example:**
```
# Bad — agent greps "sendEmail", gets 4 hits, edits the wrong one
src/lib/email.ts          # defines sendEmail
src/utils/index.ts        # re-exports sendEmail
src/server/mailer.ts      # wraps sendEmail and re-names it
src/jobs/notify.ts        # imports from ../utils

# Good — one definition, direct imports
src/email/sendEmail.ts    # the only place sendEmail lives
src/jobs/notify.ts        # imports from "@/email/sendEmail"
```

---

### 2. Co-locate the contract with the code

**Failure it prevents:** Agents write code that compiles but fails at runtime because types, validators, and the actual behavior drift apart. The agent reads the types, trusts them, and ships a bug.

**Do:**
- Put the Zod schema, the inferred TypeScript type, and the function that uses them in the same file. Agents read top-to-bottom; scattered contracts break this.
- Validate at boundaries (HTTP handlers, queue consumers, DB reads from untyped sources) and let the validator be the source of truth for the type — `z.infer` the type instead of writing a parallel interface.
- Do not hand-write types that duplicate schema output. Agents will update one and not the other.

**Concrete example:**
```ts
// Good — one source of truth, co-located
export const CreateOrderInput = z.object({
  userId: z.string().uuid(),
  items: z.array(z.object({ sku: z.string(), qty: z.number().int().positive() })),
});
export type CreateOrderInput = z.infer<typeof CreateOrderInput>;

export async function createOrder(raw: unknown): Promise<Order> {
  const input = CreateOrderInput.parse(raw); // validated + typed
  ...
}
```

---

### 3. Write function signatures that are self-sufficient

**Failure it prevents:** Agents don't open every file they call into. If a function takes `(ctx, opts)` where `opts` is `any`, the agent will invent fields. If it takes `(userId: string, orgId: string)`, the agent will pass them in the wrong order (this happens constantly).

**Do:**
- Prefer object parameters for anything with more than one argument of the same primitive type. `transfer({ fromUserId, toUserId, amountCents })` is far safer than `transfer(fromId, toId, amount)`.
- Use branded or nominal types for IDs: `UserId`, `OrgId`, `Cents`. Plain `string` and `number` IDs get swapped.
- Return discriminated unions for anything that can fail in distinct ways, not `throw` + comments. Agents handle `if (result.ok)` correctly; they frequently forget try/catch.
- Avoid optional positional parameters. `fn(a, b?, c?)` leads to agents passing `undefined` in the wrong slot.

---

### 4. Keep files small enough that an agent can hold one in working context

**Failure it prevents:** When a file exceeds a few hundred lines, agents start editing with partial context. The classic symptom: a function near the top uses a helper defined at the bottom, the agent edits the top without reading the bottom, and breaks the helper's invariants.

**Do:**
- Target ~200–400 lines per file. Above 600, agents read the first chunk and guess the rest.
- One exported concept per file where feasible. "God files" that hold a router + its handlers + its helpers force the agent to re-read the whole thing every edit.
- Put type definitions near the code that uses them, not 500 lines away.

---

### 5. Make side effects and I/O obvious at the call site

**Failure it prevents:** Agents refactor a "pure-looking" function and silently break a network call, a DB write, or a cache invalidation. They cannot see effects that hide behind innocuous names like `getUser()` that actually writes to an audit log.

**Do:**
- Name functions after what they do, including the side effect: `fetchUserAndLogAccess`, not `getUser`.
- Pass I/O clients explicitly rather than importing globally. `createOrder(db, stripe, input)` is safer to refactor than `createOrder(input)` that reaches into a module-level singleton.
- Mark async functions that do writes vs reads distinctly in naming: `readOrder` vs `insertOrder` vs `updateOrder`.
- Keep effectful code at the edges; pure functions in the middle. Agents refactor pure code correctly far more often.

---

## Tier 2 — Large reductions in common error classes

### 6. Prefer explicit imports over magic

**Failure it prevents:** Agents trip on anything that resolves at runtime rather than by reading the file. Auto-imports, dependency injection by string key, decorator magic, dynamic requires — all lead to agents adding an import that isn't how the rest of the project works.

**Do:**
- Pick one import style and enforce it. If the project uses `@/` path aliases, don't mix in relative imports for the same modules.
- Avoid frameworks that register things by filesystem convention alone without an explicit registry (or at least keep a generated `routes.ts` / `registry.ts` that an agent can grep).
- Prefer explicit dependency passing over DI containers keyed by strings. The agent cannot see what `container.get("UserService")` returns.

---

### 7. Give the agent a `README.md` and `CLAUDE.md`/`AGENTS.md` that answer its first three questions

**Failure it prevents:** The agent wastes its first several turns trying to figure out how to run tests, how to run the dev server, what the package manager is, and what the project structure means. It often guesses wrong (runs `npm` in a `bun` project) and produces changes that don't match your conventions.

**Do — include at the top:**
- How to install deps (exact command, including package manager)
- How to run tests for a single file and for the whole suite
- How to run the dev server / typecheck / lint — the fast feedback loops
- Directory map: one line per top-level folder explaining what lives there
- "House rules" that override defaults: "we don't use barrel files", "all new routes go in `src/routes/`", "prefer `type` over `interface`"
- Anything an agent would otherwise have to learn by failing

Keep it terse. 150 lines of accurate orientation beats 1000 lines of philosophy.

---

### 8. Make invariants executable, not documented

**Failure it prevents:** Comments that say "must be called before X" get ignored. Agents trust types and tests; they often skim prose.

**Do:**
- Encode invariants in types: `NonEmptyArray<T>`, `Brand<string, "Email">`, `Result<T, E>`.
- Encode them in assertions that throw loudly: `assert(user.verified, "sendWelcome requires verified user")`.
- Use exhaustiveness checks on unions: a `default: assertNever(x)` branch prevents agents from adding a new variant and forgetting to handle it.
- Prefer `readonly`, `as const`, and immutability. Mutations are a common source of agent-introduced bugs.

---

### 9. Tests that pin behavior, not implementation

**Failure it prevents:** Agents modify code, the tests pass, and something still breaks — because the tests mocked everything and only verified that the code called itself in a particular way. Or: the agent cannot tell if its refactor is safe because tests are too coupled to fail meaningfully.

**Do:**
- Write integration-ish tests at module boundaries. Testcontainers or sqlite-in-memory beats mocking the ORM.
- Each test name should describe a user-observable outcome ("rejects order when inventory is zero"), not a function name.
- Keep fixtures short and in-file when possible. An agent adding a test should not have to discover 4 fixture files.
- Tests that take >1 second discourage agents (and you) from running them. Keep the fast suite fast.

---

### 10. Errors that tell the agent what to do

**Failure it prevents:** Agents see an error, guess a fix, and introduce a second bug. Good errors short-circuit this.

**Do:**
- Throw `Error` subclasses with structured fields, not string messages alone: `throw new ValidationError({ field: "email", code: "invalid_format" })`.
- Include the offending value in the error (scrubbed if sensitive). "Invalid input" tells the agent nothing; "Invalid input: expected ISO date, got '2024/01/30'" tells it exactly what to fix.
- Keep stack traces intact — no `catch (e) { throw new Error("something failed") }` patterns that swallow the origin.

---

## Tier 3 — Removes friction on every edit

### 11. One way to do each thing

**Failure it prevents:** Agents copy the nearest example they find. If there are three patterns for "how we do a DB transaction" in the codebase, the agent will use all three over time, and each edit makes the inconsistency worse.

**Do:**
- Pick a data-fetching pattern, an error-handling pattern, a logger, a config loader, a date library, an HTTP client — and delete the alternatives.
- When introducing a new pattern, migrate the old one or add a lint rule against it. Do not leave two patterns coexisting "for now".
- Keep a short `CONVENTIONS.md` (or a section in `AGENTS.md`) listing the canonical pattern for each recurring decision.

---

### 12. Deterministic formatting and lint, enforced in CI

**Failure it prevents:** Agents producing diffs that re-format unrelated lines, which creates noisy PRs and hides real changes. Without lint/format, agents will inconsistently apply style across turns.

**Do:**
- Prettier + ESLint (or equivalents) with autofix on save, wired into a pre-commit hook or CI.
- Make `npm run typecheck && npm test && npm run lint` one command (e.g. `npm run check`). Agents run whatever is easy.
- Remove legacy lint disables that are no longer needed — agents copy them.

---

### 13. Keep the dependency graph shallow and acyclic

**Failure it prevents:** When A imports B imports C imports A, agents modify A, break C, and cannot figure out why. Circular imports also defeat many static analyses the agent relies on.

**Do:**
- Enforce layer boundaries with a tool like `eslint-plugin-boundaries` or `dependency-cruiser`.
- Domain → infrastructure → app, one direction only. Domain code that imports from `@/http` is a smell.
- Prefer composition at the edges. Functions that take their dependencies as arguments flatten the graph.

---

### 14. Configuration is typed, centralized, and fails fast

**Failure it prevents:** Agents add a new env var, forget to document it, and the app crashes in production with `undefined`. Or they read `process.env.FOO` inline in five places.

**Do:**
- One `env.ts` that parses `process.env` through a Zod (or equivalent) schema at startup. Everything else imports the parsed object.
- Crash on missing required config at boot, not at first use. Agents catch this immediately; lazy failures hide for weeks.
- Document every env var next to its definition, in the schema.

---

### 15. Keep a migration/change log that is machine-readable

**Failure it prevents:** Agent modifies a DB schema without running a migration, or runs a migration that conflicts with an in-flight one.

**Do:**
- Use a migration tool with timestamped filenames (Drizzle Kit, Prisma Migrate, etc.). Never hand-edit past migrations.
- Keep an `CHANGELOG.md` or generated changelog the agent can grep for "when did field X change".
- Name migrations after the change, not the ticket: `2026_04_12_add_user_email_verified_at.sql`.

---

## Tier 4 — Power-ups for agent workflows

### 16. Small, composable scripts in `package.json` / a `scripts/` folder

**Failure it prevents:** Agents inventing one-off bash that subtly differs from how you actually do the thing (especially for DB resets, seed data, codegen).

**Do:**
- Every repeatable operation gets a named script. `db:reset`, `db:seed`, `codegen`, `test:one`, `test:e2e`.
- Scripts should be idempotent and print what they did.
- Prefer small scripts in a real language (TS, Python) over long bash. Agents read and modify those more reliably.

---

### 17. Generated code lives in a clearly marked, lint-ignored folder

**Failure it prevents:** Agents edit generated files by hand. The next codegen run silently wipes the change. This is a classic high-confidence failure.

**Do:**
- All generated output under one folder (e.g. `src/generated/`) with a banner comment on every file: `// @generated — do not edit. Run \`npm run codegen\`.`
- Add to `.prettierignore` / lint ignores / `.gitattributes linguist-generated=true`.
- Mention it in `AGENTS.md` explicitly.

---

### 18. Observability hooks that the agent can use to verify its work

**Failure it prevents:** Agents say "I think this works" without running the code. If the only feedback loop is "the user ships it to prod", the agent cannot self-correct.

**Do:**
- Cheap, fast reproducible dev environment (Docker compose, `bun run dev`, seed data) the agent can hit.
- A way to call any endpoint or job locally (an HTTP request snippet, a CLI command). REST clients with checked-in `.http` files help.
- Structured logs the agent can grep in its own output.

---

### 19. Comments explain "why", never "what" — and only when non-obvious

**Failure it prevents:** Stale comments that mislead. Agents trust comments that contradict code, and they generate more of them.

**Do:**
- A comment that explains a workaround, a regulatory constraint, a perf cliff, or a non-obvious ordering is gold.
- A comment that restates the next line is noise and will go stale.
- If you must describe behavior, put it in a test name, not a comment.

---

### 20. Avoid metaprogramming that defeats static analysis

**Failure it prevents:** Agents cannot reason about code they cannot read.

**Do / avoid:**
- Avoid runtime proxies, dynamic `this` tricks, `eval`, computed import paths, and auto-registered plugins without a manifest.
- Avoid heavy class inheritance chains. Agents track "where does this method come from" far better in flat, composed code.
- If you need magic, confine it to a single well-documented module and provide typed facades everywhere else.

---

## Things that sound useful but aren't (and why)

- **"Add a lot of comments so the AI understands."** Redundant comments decay and mislead. Types, tests, and good names beat comments every time.
- **"Split things into many tiny files."** Over-fragmentation forces the agent to open 20 files to make one change. Aim for "cohesive units", not "smallest possible".
- **"Write a long architectural doc."** Agents skim long docs. A 100-line `AGENTS.md` with rules and pointers outperforms a 50-page architecture document.
- **"Use popular frameworks the AI knows."** True on average, but weighted far less than the above. A bespoke codebase with sharp conventions is easier for an agent than a popular framework used inconsistently.

---

## A one-page checklist

- [ ] One definition per concept; filenames match exported symbols; no barrel re-exports
- [ ] Schemas, types, and the code using them live in the same file
- [ ] Function signatures use object params, branded IDs, discriminated union results
- [ ] Files under ~400 lines, one exported concept each
- [ ] Side effects visible at call sites; I/O passed explicitly
- [ ] Explicit imports; no string-keyed DI; one import style
- [ ] `AGENTS.md` answers: install, test, run, directory map, house rules
- [ ] Invariants live in types/asserts, not comments
- [ ] Tests describe behavior and run fast; integration over mocks
- [ ] Structured errors with offending values
- [ ] One pattern per recurring decision
- [ ] Autoformat + lint + typecheck in one `check` command
- [ ] Acyclic, layered dependency graph
- [ ] Config parsed through a schema, fails at boot
- [ ] Timestamped migrations; changelog greppable
- [ ] Every repeatable op is a named script
- [ ] Generated code in one folder, banner-commented
- [ ] Fast local dev loop the agent can exercise
- [ ] Comments only for "why" and only when non-obvious
- [ ] Minimal metaprogramming; typed facades around any magic
