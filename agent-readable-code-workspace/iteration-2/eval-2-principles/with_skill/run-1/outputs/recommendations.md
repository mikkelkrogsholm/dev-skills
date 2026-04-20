# Writing Code That AI Agents Can Maintain

Prioritized, failure-mode-grounded recommendations for structuring a codebase whose primary maintainers will include Claude Code, Cursor, Copilot, and Aider.

**Guiding heuristic:** write so that someone grepping a single file can act correctly without reading the rest of the repo. Humans get lost in *complexity*; agents get lost in *indirection*. Many classical principles (SOLID, aggressive DRY, deep inheritance, dependency inversion) were calibrated for human readers with persistent mental models. Agents navigate by grep, embeddings, and bounded context windows. Some of those principles invert.

Each recommendation below specifies the concrete failure mode it prevents. If a rule doesn't map to a failure you've seen or can anticipate, skip it.

---

## Tier 1 — Highest leverage (do these first)

### 1. Give the agent a single verification command

**Failure mode:** Without a fast feedback loop, agents hallucinate into spirals. A documented case: 693 lines of wrong fixes across 39 turns because the agent couldn't confirm whether its changes worked. They then either disable the failing test or declare success.

**Do this:**
- One command that runs lint + typecheck + tests: `bun run check`, `pnpm verify`, `make ci`.
- Put it in `CLAUDE.md` / `AGENTS.md` at the repo root.
- Make it fast (< 30 seconds ideal, < 2 minutes hard ceiling). Agents time out long runs and give up.
- Make type errors fail loudly at the edit site, not at runtime.

**Anti-example:**
> "Run the tests by starting docker-compose, then `cd backend && pytest`, then in another terminal `cd frontend && npm test`, then check the staging deploy logs."
> The agent will skip steps 2-4.

---

### 2. Eliminate flakiness and inject side effects

**Failure mode:** Agents cannot debug a test that fails 1-in-10 runs. They retry until context runs out, then delete the test or add `.skip` and call the task done. Time-dependent tests, unseeded randomness, and global singletons all produce this.

**Do this:**
- Seed every random source: `faker.seed(1)`, `Math.random` replaced with a seeded PRNG in tests, frozen UUIDs in fixtures.
- Freeze time. Inject `clock: () => Date` as an argument; in tests pass `() => new Date('2024-01-01')`.
- Pass `fetch`, `logger`, `env`, `db` as function arguments rather than reading `process.env` from inside the function body.

**Concrete signature pattern:**

```ts
// Bad: side effects invisible to the agent
export async function chargeCustomer(userId: string, amountCents: number) {
  const stripe = new Stripe(process.env.STRIPE_KEY!);
  const now = new Date();
  // ...
}

// Good: dependencies are visible at the call site
export async function chargeCustomer(
  userId: UserId,
  amountCents: number,
  deps: { stripe: Stripe; now: () => Date; db: DB }
): Promise<Charge> {
  // ...
}
```

An agent reading the signature of the good version can test it; for the bad version it has to reverse-engineer what to mock.

---

### 3. Name things the way an agent would grep for them

**Failure mode:** Agents localize code by grepping names. Obfuscated names drop model comprehension accuracy from ~87% to ~59% in controlled studies. Misleading names are worse than random ones — the agent confidently acts on the wrong mental model.

**Do this:**
- Domain-specific names: `chargeCustomerAndEmitReceipt` beats `process`.
- Ban these generic suffixes in names of new files and classes: `Manager`, `Service`, `Helper`, `Handler`, `Util`, `Wrapper`, `Processor`. They communicate nothing searchable.
- Ban dumping-ground filenames: `utils.py`, `helpers.ts`, `misc.py`, `common.js`, `shared.ts`.
- When refactoring, **rename aggressively**. A stale name is a confident lie.

**Concrete test:** Pick a function. Ask "if I were the agent and I only knew the user story, what would I grep for?" If the answer isn't in the function name, rename it.

---

### 4. Colocate features; don't scatter across layers

**Failure mode:** The most-cited systemic agent failure across all platforms is the cross-layer feature: a single change spans `controllers/orders.ts` + `services/OrderService.ts` + `middleware/validate.ts` + `jobs/sendReceipt.ts` + `events/handlers.ts`. The agent fixes three of five touchpoints and ships a subtle bug because it never saw the other two.

**Do this:** Prefer vertical feature slices over horizontal layers when the framework permits.

```
Bad (horizontal layers):
src/controllers/orders.ts
src/services/OrderService.ts
src/repositories/OrderRepo.ts
src/jobs/orderReceipt.ts
src/events/orderCreated.ts
tests/unit/controllers/orders.test.ts

Good (vertical slice):
src/billing/refunds/
├── index.ts              // public surface
├── types.ts              // Refund, RefundReason, RefundStatus
├── issue-refund.ts       // the work + HTTP handler
├── issue-refund.test.ts
├── reverse-charge.ts
└── reverse-charge.test.ts
```

**Caveat:** when the framework dictates layout (Next.js `app/`, Rails, Django apps, NestJS modules), follow the framework. Fighting it costs more than the agent-unfriendliness it causes.

---

### 5. Colocate tests with source

**Failure mode:** With `tests/` in a distant mirror tree, the agent edits `src/billing/refunds.ts`, doesn't see adjacent tests, and either skips testing or fabricates a new test file in the wrong place. You catch it in CI one turn later.

**Do this:**

```
src/billing/refunds.ts
src/billing/refunds.test.ts        // unit
src/billing/refunds.integration.ts // integration, if any
```

The agent sees tests in the same `ls` output as the source. "How do I run tests for this feature?" answers itself.

---

## Tier 2 — High leverage

### 6. Keep files small enough for apply-models to succeed

**Failure mode:** Files > ~800 lines regularly fail apply-model merges. Mid-file content is used far worse than top-or-bottom content — the documented "lost in the middle" effect. A 2,000-line file is a file the agent will silently get wrong.

**Do this:**
- Soft ceiling: 400 lines.
- Hard ceiling: 800 lines.
- Split at natural seams (one route per file, one entity per file, one job per file) — not arbitrarily by line count.

---

### 7. Eliminate near-duplicates at tooling seams

**Failure mode:** Claude Code's `str_replace` fails when the surrounding lines aren't unique. Thirty copy-pasted `try/catch` blocks mean the agent either rewrites the whole file (and drops half of it from context) or edits the wrong one.

**Do this:**
- Factor out the *repeated structural chrome* — error handlers, logging wrappers, response shapes.
- Tolerate duplication inside leaves (three similar `if` checks in one file is cheap; one wrong abstraction across ten files is expensive).

**Concrete example:**

```ts
// Bad: 30 copies of this catch block across the file
} catch (err) {
  if (err instanceof ValidationError) { logger.warn(...); return res.status(400)... }
  logger.error(...); return res.status(500)...
}

// Good: one helper, one seam
} catch (err) { return handleError(err, req, res); }
```

---

### 8. Prefer static, grep-traceable code over metaprogramming

**Failure mode:** Agents trace code with grep and a simple AST walk. Anything that binds behavior at runtime — and therefore has no static reference an agent can follow — becomes a black box the agent hallucinates around.

**Avoid or heavily isolate:**
- `__getattr__`, `eval`, `exec`, `importlib.import_module` (Python)
- `Proxy`, `Reflect`, runtime monkey-patching (JS)
- Magic-string dispatch: `registerHandler("user.created", ...)` spread across 40 files, event buses keyed by arbitrary strings
- Deep inheritance chains > 3 levels — agents fabricate MROs that don't exist
- Barrel re-exports (`export * from './foo'` with nothing else) — adds a grep hop, breaks tree-shaking
- Decorator stacks that rewrite behavior silently

**Prefer:**
- Discriminated unions + one exhaustive `switch` over a string-keyed registry
- Composition over inheritance
- Explicit imports from the defining file, not a barrel

**Concrete swap — magic strings → discriminated union:**

```ts
// Bad: agent must grep the whole repo to find handlers for "user.created"
bus.emit("user.created", { id });
bus.on("user.created", (payload) => ...); // in some other file

// Good: exhaustive switch the compiler checks, all variants listed in one file
type DomainEvent =
  | { kind: "user.created"; userId: UserId }
  | { kind: "user.deleted"; userId: UserId }
  | { kind: "order.refunded"; orderId: OrderId };

function handle(event: DomainEvent) {
  switch (event.kind) {
    case "user.created":   return onUserCreated(event.userId);
    case "user.deleted":   return onUserDeleted(event.userId);
    case "order.refunded": return onOrderRefunded(event.orderId);
  }
}
```

---

### 9. Use types as anti-hallucination anchors at boundaries

**Failure mode:** At module seams, untyped or loosely-typed boundaries let agents fabricate signatures. Parallel hand-maintained type declarations drift — the agent updates one; the others silently lie.

**Do this:**
- Typed public signatures on every exported function.
- One source of truth per type: `z.infer<typeof Schema>`, `typeof table.$inferSelect`. Don't maintain a `User` type in three places.
- Branded types for IDs that look alike:

```ts
type UserId = string & { readonly __brand: "UserId" };
type OrgId  = string & { readonly __brand: "OrgId" };
// Now swapping them is a compile error, not a production bug.
```

- `as const` on literal tuples so types narrow to the literal:

```ts
export const ROLES = ["admin", "member", "guest"] as const;
export type Role = typeof ROLES[number]; // "admin" | "member" | "guest"
```

---

### 10. Accurate comments only, or none at all

**Failure mode:** In controlled tests, *incorrect* documentation crashed model success rates far below the no-docs baseline. *Missing* documentation had no measurable effect. Wrong docstrings are oracles the agent trusts and then acts on.

**Do this:**
- Delete stale comments when you refactor. If you rename a function, audit every comment nearby.
- Comment the **why**, not the **what**: hidden constraints, past incidents, non-obvious invariants.
- The type signature is the spec. Don't restate it in prose.

```py
# Bad (restates the signature, might drift)
def charge(user, amount):
    """Charges a user and returns True on success. Sends email receipt."""

# Good (adds a why that you couldn't infer from types)
def charge(user: User, amount: Money, *, idempotency_key: str) -> Charge:
    # Stripe returns 200 with status=failed for some card declines (incident #427).
    # Check charge.status even when the HTTP call succeeds.
    ...
```

---

## Tier 3 — Meaningful refinements

### 11. Language-specific hallucination-closers

**Python:**
- `__all__` on every module with public exports. Python's only reliable signal for "import this, not that"; without it, agents import private helpers and create coupling you didn't intend.
- `@dataclass(slots=True)` when dynamic attributes aren't needed. `user.foo = bar` on a typo hits `AttributeError` immediately instead of silently succeeding and surfacing the bug three edits later.
- `frozen=True` on value objects. Prevents the agent from mutating what it thinks is immutable.

**TypeScript:**
- Branded IDs (see rec. 9).
- Discriminated unions over string enums.
- `as const` on literal records.
- `z.infer<>`, `typeof table.$inferSelect` — derive types from the one place they're defined.

---

### 12. Choose boring, well-trained frameworks

**Failure mode:** Agents are better at code that resembles their training data. A bespoke internal DSL with 0 GitHub stars is one the agent has never seen; it will confabulate APIs.

**Do this:**
- Prefer frameworks with large public footprints: Hono, Drizzle, Prisma, Zod, React, Bun, Postgres. The agent has seen the canonical patterns thousands of times.
- Treat "boring stack" as a legitimate agent-performance axis. A Postgres + Drizzle + Hono + React app will get better agent edits than an equivalently powerful EffectTS + XState + custom-DSL setup — even if the latter is technically superior.
- Pin dependency versions on load-bearing packages. An agent's memory of `stripe@v14` is wrong for `stripe@v18`; pinning makes the docs it fetches match the version you run.

---

### 13. Keep generated and vendored junk out of the searchable tree

**Failure mode:** A 38,000-character line in `vendor/analytics.min.js` lands in `ripgrep` output and corrupts the agent's context. Build artifacts in-tree pollute every grep.

**Do this:**
- Generated files go in `dist/`, `build/`, `.next/` — and those go in `.gitignore`, `.claudeignore`, `.cursorignore`.
- Vendored JS minified bundles go in `public/vendor/`, not `src/`.
- Hard rule: any line > 400 chars in source is a smell. Either it's generated (move it) or it's a literal that should be externalized.

---

### 14. Make the dependency graph a DAG, not a web

**Failure mode:** Cyclic imports confuse both the agent and the tooling. Dynamic imports hide edges entirely.

**Do this:**
- Enforce direction: `domain → application → infrastructure`, never the reverse.
- Avoid `index.ts` barrels that re-export everything. Consumers should import from the defining file.
- No conditional `require()`/`import()` to break cycles — fix the cycle instead.

---

### 15. Write an `AGENTS.md` / `CLAUDE.md` with the irreducible context

**Failure mode:** Agents land cold in a repo and either spend context discovering conventions, or guess them wrong.

Include (and keep short — agents read this every session):
- The one verification command.
- The stack, with pinned versions.
- Naming conventions (kebab-case filenames? PascalCase types?).
- Known gotchas ("our custom migration script must run before tests").
- Where each feature lives (`src/billing/...`, `src/auth/...`).

Don't include: tutorials, motivation, history. This is a map, not a book.

---

## When NOT to apply these

These are one lens, not the only lens. Push back when:

- **Framework dictates layout.** Next.js app router, Rails MVC, Django apps. The framework wins.
- **Public API compatibility constrains naming.** A published `process()` can't be renamed just to satisfy rec. 3.
- **Metaprogramming *is* the product.** ORMs, DI frameworks, validation libraries. Don't try to purge dynamism from them.
- **Some duplication is inherent.** Data models, DTOs, migrations, fixtures have shape repetition. That's the domain, not a refactor target.
- **The code is throwaway.** One-off scripts, migration one-shots, research notebooks. Skip the ceremony.
- **Human readers have different constraints.** These recs don't replace SOLID/DRY/KISS — they re-weight them. SRP is still portable. DRY is still right *in spirit* (one source of knowledge) and often wrong *in letter* (deduplicate anything that rhymes).

**Decide by lifetime and blast radius.** A demo script has one reader; skip most of this. A payments module maintained for ten years across dozens of human and agent contributors earns every clarity investment.

---

## Priority summary

If you can only do five things:

1. One fast `check` command that runs lint + typecheck + tests.
2. Seed randomness and freeze time in tests; inject side effects as arguments.
3. Rename aggressively toward domain-specific, greppable names; ban `Manager`/`Helper`/`utils.py`.
4. Colocate features (source + tests + types) in one directory.
5. Keep files under 400 lines, with no near-duplicate blocks that defeat `str_replace`.

Everything else compounds on top of these.
