# Writing Code That AI Coding Agents Can Read and Modify Correctly

Recommendations for structuring a codebase so agents (Claude Code, Cursor, Copilot, Aider, Devin) make correct edits with minimal human supervision.

**Underlying heuristic:** write so that someone grepping a single file can act correctly without reading the rest of the repo. Humans get lost in complexity; agents get lost in *indirection*. Classical principles (SOLID, DRY) were calibrated for humans juggling cognitive load — several of them invert when the reader has a limited context window and navigates by grep + file reads.

Recommendations are ordered by leverage: the first group prevents the most common and most destructive agent failures.

---

## Tier 1 — High leverage, backed by controlled studies

### 1. Use descriptive, domain-specific names at every call site

**Failure mode it prevents.** Agents localize code by grepping names. Obfuscating identifiers drops model comprehension accuracy from ~87% to ~59% in controlled studies. Worse: misleading names hurt more than random ones — the agent acts confidently on a wrong mental model.

**What to do.**
- Avoid a banlist of generic words in filenames, classes, and functions: `Manager`, `Service`, `Helper`, `Handler`, `Util`, `process`, `handle`, `doStuff`, single-letter vars outside tight loops.
- Avoid dumping-ground files: `utils.py`, `helpers.ts`, `misc.py`, `common.js`.
- When you refactor a function's behavior, rename it aggressively. A stale name is a confidently wrong oracle.

**Concrete example.**

```python
# Bad — agent greps for "refund" and finds nothing
# utils.py
def process(data): ...
class Manager:
    def do_stuff(self, thing): ...

# Good — grep "refund" returns exactly the right file
# billing/refunds.py
def issue_refund_and_notify_customer(order_id: str, reason: RefundReason) -> Refund: ...
def reverse_stripe_charge(charge_id: str) -> None: ...
```

### 2. Type public boundaries; delete stale comments

**Failure mode it prevents.** In controlled tests, incorrect docstrings crashed GPT-3.5 task success from baseline to 22.1% and GPT-4 to 68.1%. Missing docstrings had *no significant effect*. A wrong comment is an actively wrong oracle; a missing one is benign.

**What to do.**
- Annotate every exported function, class, and public API with types. The type signature *is* the spec.
- Only comment the *why* (non-obvious invariant, past incident, hidden constraint). The code shows the *what*.
- On any change that affects behavior, update or delete the docstring *in the same commit*. Never "update later."
- In TypeScript, use branded types for IDs and discriminated unions over magic strings so the compiler catches an agent's swap:

```ts
type UserId = string & { readonly __brand: 'UserId' };
type OrgId  = string & { readonly __brand: 'OrgId' };
// fn(userId: UserId, orgId: OrgId) — swapping them is a compile error.

type Event =
  | { kind: 'created'; userId: UserId }
  | { kind: 'deleted'; userId: UserId };
// Agent cannot invent a third variant — switch is exhaustive.
```

- In Python, use `dataclass(frozen=True, slots=True)` for value objects. `user.foo = bar` on a slotted dataclass fails loudly; on a normal class it silently succeeds and surfaces three edits later.

### 3. Provide a verification loop at the file level

**Failure mode it prevents.** Agents without an in-loop verification signal hallucinate into long wrong-patch spirals — one documented case: Gemini produced 693 lines of wrong fixes over 39 turns before a human intervened. "If you can't verify it, don't ship it" is the highest-leverage rule in every vendor's best-practices doc.

**What to do.**
- Colocate tests: `billing/refunds.ts` + `billing/refunds.test.ts` in the same directory, not in a mirrored `tests/` tree. When an agent opens the source file it sees the tests in the directory listing.
- Expose a single command that runs lint + typecheck + tests (`bun test`, `make check`, `npm run ci`). Document it in `CLAUDE.md` / `AGENTS.md`.
- Prefer loud failures at the edit site: TypeScript errors, Python `AttributeError`, schema validation — over silent fallthrough.

```
# Bad
src/billing/refunds.ts
tests/unit/billing/refunds.test.ts          # agent never sees it
tests/integration/billing/refunds.int.ts

# Good
src/billing/refunds.ts
src/billing/refunds.test.ts                 # same directory listing
src/billing/refunds.integration.ts
```

---

## Tier 2 — High leverage, supported by vendor reports and postmortems

### 4. Organize by feature (vertical slices), not by layer

**Failure mode it prevents.** The dominant systemic failure across all agent platforms: a feature spans controller + service + middleware + trigger + background job. The agent fixes three of five touchpoints and ships a subtle bug. SWE-Bench Pro reports that top frontier models are still under 45% Pass@1 on multi-file edits; failures cluster on semantic correctness across files.

**What to do.** Colocate a feature's code, types, and tests in one directory the agent can load as a coherent unit:

```
src/billing/refunds/
  index.ts               # 40 lines: public API + types re-export
  types.ts               # 30 lines: Refund, RefundReason, RefundStatus
  issue-refund.ts        # 120 lines: one exported function
  issue-refund.test.ts   # colocated unit test
  reverse-charge.ts
  reverse-charge.test.ts
```

Avoid the `controllers/` + `services/` + `repositories/` split in greenfield code unless a framework dictates it. Where the framework dictates it (Next.js `app/`, Rails, NestJS, Django apps), the framework wins — the cost of fighting conventions is higher than the agent-unfriendliness.

### 5. Prefer static, grep-visible dispatch over dynamic tricks

**Failure mode it prevents.** Code that can't be traced with grep or a simple AST walk is code the agent fabricates around. ETH SRI documented an agent literally asking itself "has `self.data.get_str_vals` been monkey-patched?" before producing a wrong fix. Reflection, metaprogramming, and heavy DI are consistently in the top failure triggers across Claude Code, Cursor, and Devin.

**What to avoid.**
- `__getattr__`, `eval`, `exec`, `importlib.import_module`, JS `Proxy`, `Reflect`, runtime monkey-patching.
- Magic-string event dispatch: `registerHandler("user.created", ...)` spread across 40 files. Agents can't trace a string across a repo the way they trace a typed reference.
- Deep inheritance chains (>3 levels). Agents fabricate method resolution orders that don't exist.
- Decorator stacks that silently rewrite behavior.
- Heavy dependency injection where control flow is invisible to grep.

**What to prefer.**

```python
# Bad — api.refund_payment(...) is invisible to grep
class API:
    def __getattr__(self, name):
        endpoint = name.replace("_", "-")
        return lambda **kw: self._request(endpoint, **kw)

# Good — explicit methods, grep works, types flow, autocomplete works
class API:
    def refund_payment(self, payment_id: str) -> Refund:
        return self._request("refund-payment", payment_id=payment_id)
```

For event dispatch, prefer a discriminated union + one exhaustive switch in a single registry file imported explicitly by consumers.

### 6. Keep files small and remove near-duplicates at seams

**Failure mode it prevents.** Files over ~800–1000 lines regularly fail apply-model merges, and mid-file content is used far worse than content near start or end of context (the "lost in the middle" effect, Liu et al. 2023). Near-duplicate blocks defeat exact-match string replacement — Claude Code's `str_replace` fails when surrounding lines aren't unique, and the probability of duplicates rises with file size.

**What to do.**
- Target files under 800 lines. Break up by responsibility inside the feature directory.
- Factor repeated error handling, validation, logging into one helper *at the seam*:

```ts
// Bad — 30 identical catch blocks across a 1400-line routes.ts
try { ... } catch (err) {
  if (err instanceof ValidationError) { logger.warn(...); return res.status(400)...; }
  logger.error(...); return res.status(500)...;
}

// Good
// api/errors.ts
export function handleError(err: unknown, req: Request, res: Response) { ... }

// api/orders/create.ts  (70 lines)
import { handleError } from '../errors';
export async function createOrder(req, res) {
  try { /* logic */ } catch (err) { return handleError(err, req, res); }
}
```

Inside a single leaf function, a little duplication is fine — it's cross-file repetition that breaks edits.

### 7. Avoid barrel re-export files

**Failure mode it prevents.** An `index.ts` whose only content is `export * from './foo'` forces the agent to make an extra grep hop: find the barrel, read the `from` clause, grep again. On a large tree this doubles tool-call count before the agent starts working. Aider's own tips and Cursor's rule docs explicitly advise referencing the defining file.

**What to do.** Consumers import from the defining file: `import { createUser } from '@/billing/refunds/issue-refund'`, not from an intermediate barrel. Keep barrels only where a tool *requires* one (Drizzle's `db/schema/index.ts`, package entry points).

### 8. Keep generated / minified content out of the source tree

**Failure mode it prevents.** Lines longer than ~400 characters (minified bundles, inline SVGs) break ReAct-formatted tool outputs. `ripgrep` matches dump the entire line, truncating parsing and burning context.

**What to do.** Put vendored/minified files in `dist/`, `build/`, `public/vendor/`. Add to `.gitignore`, `.claudeignore`, `.cursorignore`. If a long literal is unavoidable, wrap it or load from a file.

---

## Tier 3 — Lower leverage, still pay for themselves

### 9. Inject side effects; seed all randomness; freeze time in tests

**Failure mode it prevents.** Agents cannot debug a test that fails 1-in-10 runs. They retry until context runs out, then either disable the test or declare success. Non-determinism also makes snapshot-based verification flaky.

**What to do.**
- Pass `clock`, `fetch`, `logger`, `env`, `db` as function arguments. A signature that reveals side effects is one an agent can test; a function that reaches into `process.env` is one the agent will quietly call wrong.
- Seed everything: frozen UUIDs, seeded `Math.random`, `faker.seed()`. UUID-in-snapshots is a near-guaranteed flake source.
- Never let a test depend on `new Date()` or `time.time()` without an injected clock.

```ts
// Bad
export function signToken(payload: Payload): string {
  const exp = Date.now() + 3600_000;
  ...
}

// Good
export function signToken(payload: Payload, now: () => number): string {
  const exp = now() + 3600_000;
  ...
}
```

### 10. Language-specific closures of hallucination surface

**Python.**
- `__all__` on every module with public exports. Without it, agents import private helpers and quietly couple modules.
- `@dataclass(frozen=True, slots=True)` for value objects.

**TypeScript.**
- Branded types for IDs (see recommendation 2).
- Discriminated unions with exhaustive `switch` over magic strings.
- `as const` on literal tuples/records so types narrow to the literal rather than widening to `string`.
- Infer from one source of truth: `z.infer<typeof Schema>`, `typeof table.$inferSelect`. Parallel hand-maintained types drift; an agent updates one, the others silently lie.

### 11. Write for "training-data gravity"

**Failure mode it prevents.** Agents work best with code that looks like the code they were trained on — orders-of-magnitude more examples of standard Hono/Drizzle/Zod/React/Prisma idioms than bespoke internal DSLs. This isn't aesthetic; it's retrieval quality.

**What to do.**
- Prefer frameworks with large, stable public presence.
- Pin dependency versions on load-bearing packages (no `^` on `stripe`, `drizzle-orm`, `next`, etc.). An agent's memory of `stripe@v14` is wrong for `stripe@v18`; pinning makes the docs the agent can fetch match the version you run.
- Treat "boring stack" as a legitimate agent-performance axis. A vanilla Postgres + Drizzle + Hono + React app will get better agent edits than an equivalently powerful Effect + XState + custom-DSL setup.

### 12. Provide an agent-readable context file

**Failure mode it prevents.** Agents need "where things live and what rules to follow," not project history. Prose READMEs can actively mislead an agent who treats them as ground truth.

**What to do.** Add a `CLAUDE.md` / `AGENTS.md` at the repo root containing:
- The single command that runs lint + typecheck + tests.
- Where features live (`src/<feature>/`).
- Hard rules (no `any`, no `--force`, do not touch `migrations/`).
- Links to one canonical example feature to imitate.

Keep it short. Long agent-context files crowd out actual task context.

---

## When NOT to apply these

Agent-readability is one lens. Push back on individual recommendations when:

- **The framework dictates the layout.** Next.js `app/`, Rails MVC, Django apps, NestJS modules — framework conventions win.
- **Public API compatibility matters more than naming purity.** A published library function called `process()` cannot be renamed. Evolve it.
- **Metaprogramming is the product.** ORMs, validation libraries, DI frameworks, DSLs are supposed to be dynamic.
- **Some duplication is inherent.** Migrations, fixtures, DTOs — don't refactor the domain away.
- **The code is throwaway.** One-off scripts, notebooks, demo prototypes. Skip the ceremony.

**Decide by lifetime and blast radius.** A throwaway script has one reader; skip the rules. A payments module maintained for ten years across dozens of contributors (human and agent) earns every clarity investment.

---

## Classical principles — which still apply

- **KISS, YAGNI** — unchanged. Simple code helps both audiences.
- **DRY** — right in spirit (single source of knowledge), often wrong in letter (deduplicate anything that rhymes). For agents, premature abstraction is worse than duplication; three similar lines in one file are cheap, one wrong abstraction shared across ten files is expensive.
- **SOLID** — most applicable to OO-heavy enterprise codebases with long-lived human teams. DIP and ISP often push toward indirection that hurts both agent navigation and human comprehension. SRP is the most portable letter.

---

## A quick audit checklist

Run through this on an unfamiliar codebase before proposing agent-driven changes:

- [ ] Any file over 800 lines? Split by responsibility inside the feature dir.
- [ ] Any `utils.py` / `helpers.ts` / `Manager` / `Service` dumping ground? Rename by domain.
- [ ] Tests alongside source, or in a distant mirror tree? Colocate.
- [ ] Single command that runs lint + typecheck + tests? Document it.
- [ ] `__getattr__`, `eval`, string-keyed event bus, deep inheritance? Replace with composition + explicit calls.
- [ ] Barrel `index.ts` files with only `export *`? Import from defining files.
- [ ] Minified / generated files in `src/`? Move to `dist/` and ignore.
- [ ] Stale docstrings that don't match code? Delete or update.
- [ ] `new Date()`, `Math.random`, `process.env` inside business logic? Inject.
- [ ] `^` on load-bearing dependencies? Pin.
- [ ] `CLAUDE.md` / `AGENTS.md` present with the run command and the canonical example? Add one.
