# Recommendations: Writing Code That AI Coding Agents Can Read and Modify Correctly

This is a prioritized, concrete list of changes that make your codebase easier for AI coding agents (Claude Code, Cursor, Copilot, Aider, Devin) to navigate, comprehend, and edit without introducing subtle bugs.

**Underlying heuristic:** write so that someone grepping a single file can act correctly without reading the rest of the repo. Humans get lost in complexity; agents get lost in *indirection*. Classical principles like SOLID and DRY were calibrated for human readers juggling cognitive load — several of them invert when the reader is an agent with a limited context window navigating by grep and file reads alone.

Recommendations are ordered by impact (highest first). Each one names the specific failure mode it prevents.

---

## Priority 1 — Highest impact, lowest effort

### 1. Name things for grep, not for elegance

**Failure mode.** Agents localize code by grepping identifiers. Names are retrieval cues, not labels. Controlled studies show obfuscated or generic names drop model comprehension accuracy from ~87% to ~59%. Crucially, **a misleading name is worse than a random one** — the agent confidently acts on the wrong mental model.

**Do.**
- Use domain-specific names: `chargeCustomerAndEmitReceipt` beats `process`.
- Rename aggressively when you refactor. Stale names are confidently-wrong oracles.
- Banlist in source code: `Manager`, `Service`, `Helper`, `Handler`, `Util`, `process`, `handle`, `doStuff`, and single-letter variables outside tight loops.
- Delete dumping-ground files named `utils.py`, `helpers.ts`, `misc.py`, `common.js`. Move the contents to a feature directory where they belong.

**Before (trap):**
```python
# utils.py (1200 lines of unrelated functions)
def process(data): ...
def handle_it(x, y): ...
class Manager:
    def do_stuff(self, thing): ...
```
Agent asked "where is the refund logic?" greps for `refund`, finds nothing, scans three helper files, runs out of context.

**After:**
```python
# billing/refunds.py
def issue_refund_and_notify_customer(order_id: str, reason: RefundReason) -> Refund: ...
def reverse_stripe_charge(charge_id: str) -> None: ...
```
`grep refund` returns one file. The name answers "what does it do?" without opening it.

---

### 2. Add a verification loop the agent can run without you

**Failure mode.** An agent without an in-loop feedback signal hallucinates into long wrong-patch spirals. A documented case: 693 lines of wrong fixes over 39 turns with no verification signal to stop the spiral.

**Do.**
- Colocate tests next to source (`foo.ts` + `foo.test.ts`), not in a distant `tests/` tree.
- Provide one command that runs lint + typecheck + tests: `npm run check`, `make verify`, `bun run ci`.
- Make type errors fail loudly at the edit site, not at runtime three layers deep.
- Write tests the agent can actually run: no live network, no time-of-day dependence, no UUIDs in snapshots.

**Before:**
```
src/billing/refunds.ts
tests/unit/billing/refunds.test.ts
tests/integration/billing/refunds.integration.ts
```
Agent edits `refunds.ts`, sees no adjacent tests, skips testing or invents a new file in the wrong place.

**After:**
```
src/billing/refunds.ts
src/billing/refunds.test.ts
src/billing/refunds.integration.ts
```
Running `bun test src/billing/` is obvious from the listing.

---

### 3. Delete wrong docstrings and comments — do not "update later"

**Failure mode.** In controlled tests, incorrect documentation crashed GPT-3.5 task success to 22.1% (from baseline); missing or partial docstrings showed no significant effect. **A stale comment is a confidently-wrong oracle.**

**Do.**
- Comment only the *why* (hidden constraint, past incident, non-obvious invariant). The code already shows the *what*.
- When behavior changes, delete the old comment in the same commit. If you don't have time to rewrite it, delete it — silence beats a lie.
- Type signatures are the spec. Prefer `def charge(user: User, amount: Money) -> Charge:` to a paragraph of prose.

**Trap:**
```python
def charge(user, amount, **opts):
    """Charges a user and returns True on success. Sends email receipt."""
    # (code no longer sends email; returns a Charge object now)
```
The agent trusts the docstring, writes `if charge(...)`, and masks failures because any `Charge` object is truthy.

---

## Priority 2 — Structural decisions that pay off continuously

### 4. Organize by vertical slice (feature), not horizontal layer

**Failure mode.** The dominant systemic failure across all agent platforms: a feature that spans `controllers/` + `services/` + `middleware/` + `triggers/` + background jobs. The agent fixes three of five touchpoints and ships a subtle bug. Multi-file edit benchmarks (SWE-Bench Pro) show top frontier models under 45% Pass@1 for exactly this reason.

**Do.** Colocate a feature's code, types, and tests in one directory the agent can load as a coherent unit.

**After (concrete example):**
```
src/billing/refunds/
├── index.ts              # 40 lines: public API + types re-export
├── types.ts              # 30 lines: Refund, RefundReason, RefundStatus
├── issue-refund.ts       # 120 lines: one exported function, typed
├── issue-refund.test.ts
├── reverse-charge.ts
└── reverse-charge.test.ts
```

**Exception.** When the framework dictates layout (Next.js `app/`, Rails controllers/views/models, Django apps, NestJS modules), follow the framework. The cost of fighting it exceeds the cost of agent-unfriendly structure.

---

### 5. Keep files small, keep lines short, keep blocks unique

**Failure mode — large files.** Files over ~800–1000 lines regularly fail apply-model merges. The "lost in the middle" effect means mid-file content is retrieved far worse than content near start or end; GPT-3.5 can score below its closed-book baseline when the needle is mid-context.

**Failure mode — duplicated blocks.** Agents' primary edit primitive is exact-match string replacement (`str_replace`). Near-duplicate blocks (30 identical catch blocks) defeat unique targeting. The agent either picks the wrong one, or falls back to rewriting the whole file and truncates.

**Failure mode — long lines.** Lines over ~400 chars (minified JS, inline SVGs, long string literals) break ReAct-formatted tool outputs. `ripgrep` matches spill the entire line into context, dropping or truncating real matches.

**Do.**
- Target files under 800 lines. Split by responsibility *inside* a feature directory, not by cross-feature layer.
- Factor repeated error-handling, validation, and logging into a single helper *at the seam*. Tolerate a little duplication inside a single leaf function.
- Keep minified / generated assets out of the source tree. Put them in `dist/`, `build/`, or add to `.gitignore` / `.claudeignore` / `.cursorignore`.

**Before (trap — both AR001 and AR002):**
```ts
// api/routes.ts — 1400 lines; 30 handlers each ending with this exact catch:
  } catch (err) {
    if (err instanceof ValidationError) {
      logger.warn({ err, path: req.path });
      return res.status(400).json({ error: err.message });
    }
    logger.error({ err, path: req.path });
    return res.status(500).json({ error: "Internal error" });
  }
```
Claude Code's `str_replace` cannot uniquely target one of those blocks.

**After:**
```ts
// api/orders/create.ts  (70 lines)
import { handleError } from "../errors";
export async function createOrder(req, res) {
  try { /* logic */ } catch (err) { return handleError(err, req, res); }
}
```
One seam, every file under 200 lines.

---

### 6. Make dependencies static and explicit — no magic

**Failure mode.** Code the agent can't trace with grep or a simple AST walk is code the agent invents around. Documented agent postmortems include Gemini imagining inheritance relationships that didn't exist, and an agent literally asking itself "has `self.data.get_str_vals` been monkey-patched?" before producing a wrong fix.

**Avoid.**
- Runtime metaprogramming: `__getattr__`, `eval`, `exec`, `importlib.import_module`, JS `Proxy`, `Reflect`, monkey-patching.
- **Magic-string dispatch**: `registerHandler("user.created", fn)` spread across 40 files, or event buses keyed by strings. Agents cannot trace a string across the repo the way they trace a typed reference.
- Inheritance chains > 3 levels deep. Agents fabricate method resolution paths that don't exist.
- Decorator stacks that rewrite behavior silently. Keep decorators declarative.
- Heavy dependency injection where control flow is invisible to grep. Wire DI at the edges, not throughout.
- **Barrel re-export files** (`export * from './foo'` files that contain nothing else). They add a grep hop between the consumer and the defining symbol. The agent greps for `createUser`, lands on the barrel, has to open it, read the `from` clause, grep again. Doubles the tool-call count on a large tree.

**Prefer.**
- Explicit method definitions over `__getattr__`.
- Discriminated unions + one exhaustive `switch` over a magic-string registry.
- Composition with explicit delegation over deep inheritance.
- Direct imports from the defining file, not from a barrel.

**Before (trap):**
```python
class API:
    def __getattr__(self, name):
        return lambda **kw: self._request(name.replace("_", "-"), **kw)

api.refund_payment(id=...)  # invisible to grep
```

**After:**
```python
class API:
    def refund_payment(self, payment_id: str) -> Refund:
        return self._request("refund-payment", payment_id=payment_id)
```

---

### 7. Type the boundaries, use one source of truth

**Failure mode.** Parallel hand-maintained type declarations drift. An agent updates one, the others silently lie. Untyped boundaries let the agent fabricate call shapes. Constrained-generation research shows type annotations measurably improve the agent's ability to retrieve and call the right API.

**Do.**
- Typed public signatures on every exported function — in Python use type hints, in TS avoid `any` and `unknown` at boundaries.
- **Infer from one source of truth**: `z.infer<typeof UserSchema>`, `typeof table.$inferSelect` (Drizzle). Never maintain a parallel interface declaration.
- Branded types for IDs: `type UserId = string & { readonly __brand: 'UserId' }`. Agents routinely swap `userId` and `orgId` when both are plain `string`; branded types make the swap a compile error.
- Discriminated unions over magic strings: `type Event = { kind: 'created'; ... } | { kind: 'deleted'; ... }`. The compiler enumerates cases; agents can't invent a variant.
- `as const` on literal tuples and records so types narrow to the literal.

---

## Priority 3 — Language-specific and stack-level choices

### 8. Make side effects visible in function signatures

**Failure mode.** A function that reaches into globals for `process.env`, `new Date()`, `Math.random()`, or `fetch` is a function the agent will quietly call wrong in tests, or a test the agent cannot make deterministic. Agents can't debug a test that fails 1-in-10 runs — they retry until context runs out, then either disable the test or declare success.

**Do.**
- Pass `clock`, `fetch`, `logger`, `env`, `db` as arguments to functions that need them. A function whose signature reveals its side effects is one an agent can test.
- Seed all randomness: frozen IDs, seeded `Math.random`, `faker.seed()`. UUID-in-snapshots is a near-guaranteed flake source.
- Freeze time in tests. Never let a test depend on `new Date()` without an injected clock.

**Before:**
```ts
export function expireStaleOrders() {
  const now = new Date();
  return db.orders.where("created_at", "<", subDays(now, 30)).delete();
}
```
**After:**
```ts
export function expireStaleOrders(deps: { now: Date; db: DB }) {
  return deps.db.orders.where("created_at", "<", subDays(deps.now, 30)).delete();
}
```

---

### 9. Python-specific idioms that close hallucination surface

- **`__all__` on every module with public exports.** The one signal Python has for "import this, not that." Without it, agents import private helpers and create coupling you didn't intend.
- **`@dataclass(slots=True)`** when you don't need dynamic attributes. An agent writing `user.foo = bar` on a slotted dataclass hits `AttributeError` immediately; on a normal class it silently succeeds and the bug surfaces three edits later.
- **`@dataclass(frozen=True)`** for value objects. Prevents an agent from mutating what it thinks is immutable.

---

### 10. TypeScript-specific idioms

Covered partly in #7 above. The trio that matters most in practice:
- Branded types for every domain ID.
- Discriminated unions for every "kind of thing" that has variants.
- `as const` + `z.infer` / `$inferSelect` as the only type source.

---

### 11. Pick a boring stack and pin it

**Failure mode.** An agent's memory of the API for `stripe@v14` is wrong for `stripe@v18`. Bleeding-edge or bespoke DSLs have less training-data coverage; the agent falls back to guessing.

**Do.**
- Prefer frameworks with large, stable public presence (Hono, Drizzle, Zod, Prisma, Bun, React, Postgres) over bespoke internal DSLs.
- Pin load-bearing dependency versions (no `^` on things like ORMs, auth, payments). Pinning makes fetched docs match the version you run.
- Treat "boring stack" as a legitimate agent-performance axis. Vanilla Postgres + Drizzle + Hono + React will get better agent edits than an equivalently-powerful EffectTS + XState + custom-DSL setup, even if the latter is technically superior.

---

## Priority 4 — Repo-level affordances

### 12. Write `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` for navigation, not prose

**Failure mode.** Agents don't benefit much from project-history README prose. They need "where things live and what rules to follow." A prose-heavy README that misleads about current structure can actively harm agent performance.

**Do.** The agent context file should answer, crisply:
- Where does each feature live? (`src/billing/` owns refunds; `src/notifications/` owns email)
- What is the one command that runs everything? (`bun run check`)
- What are the hard rules? ("Never import from `src/internal/`", "All IDs are branded types")
- What are canonical examples to imitate? (point at one exemplary feature directory)

Keep it short. Agents re-read it every session; every line costs context.

### 13. Make generated and vendored code invisible to agents

**Failure mode.** Agents grep `.min.js` bundles and waste context on them. Agents try to edit `schema.generated.ts` and get confused when changes vanish.

**Do.**
- Put minified and vendored assets in `dist/`, `build/`, or `public/vendor/`.
- Add them to `.gitignore`, `.claudeignore`, `.cursorignore`.
- Put a comment at the top of generated files: `// GENERATED — edit schema.ts and run bun run generate`.

### 14. Colocate tests and one-shot verification

Already covered in #2. Reinforce at the repo level: a `package.json` script or `Makefile` target that runs the full verification loop in one command. This is the single highest-leverage investment you can make for agent performance.

---

## When NOT to apply these rules

Agent-readability is one lens, not the only one. Push back — including on this list — when:

- **The framework dictates the layout.** Next.js, Rails, Django, NestJS. Framework conventions win.
- **Public API compatibility matters more than naming purity.** A published library function called `process()` cannot be renamed without breaking consumers.
- **Metaprogramming is the product.** ORMs, validation libraries, DI frameworks, DSLs exist to do dynamic behavior. Don't lint-clean them.
- **Some duplication is inherent.** Data models, DTOs, migrations, fixtures often have repetitive shape. That's the domain, not a refactor opportunity.
- **The code is throwaway.** One-off scripts, research notebooks, demo prototypes. Skip the ceremony.
- **A centralized test strategy is deliberate.** Some teams intentionally split unit (colocated) from integration/e2e (top-level). Fine — document the choice.

**Decide by lifetime and blast radius.** A throwaway script has ~1 reader; skip the ceremony. A payments module maintained for ten years across dozens of contributors (human and agent) earns every clarity investment you make.

---

## Classical principles: what still applies

This is not "SOLID and DRY are obsolete." Humans still read code.
- **KISS and YAGNI** — unchanged. Simple code helps both audiences.
- **DRY** — still right *in spirit* (single source of knowledge), frequently wrong *in letter* (don't deduplicate anything that rhymes). For agents, premature abstraction is worse than duplication; three similar lines in one file are cheap, one wrong abstraction shared across ten files is expensive.
- **SOLID** — most applicable in OO-heavy enterprise codebases with long-lived human teams. In small teams using AI agents heavily, DIP and ISP often push toward indirection that hurts both agent navigation and human comprehension. SRP is the most portable letter.

---

## Quick self-audit (15 minutes)

Run through this checklist on any codebase you'll maintain with agents:

1. Search the repo for files named `utils.*`, `helpers.*`, `misc.*`, `common.*`. Rename or relocate.
2. Search for functions named `process`, `handle`, `doStuff`, `run`. Rename to domain verbs.
3. List files by line count; flag anything over 800 lines for splitting.
4. Grep for `__getattr__`, `Proxy(`, `eval(`, `exec(`, `importlib.import_module`, `registerHandler(`. Each hit is a navigation trap.
5. Find any class that inherits through 4+ levels. Flatten.
6. Find any `export *` or `export { ... } from` files that are their only content. Inline the imports at consumers.
7. Run the test suite three times. Any flakes? Seed randomness; inject clocks.
8. Is there a single command that lints + typechecks + tests? If not, add one.
9. Are tests next to the source they test? If not, move them.
10. Open `CLAUDE.md` / `AGENTS.md`. Is it prose, or is it a map? Rewrite as a map.

Each item prevents a specific, documented agent failure mode. Items 1–3 and 8–9 are the highest leverage.
