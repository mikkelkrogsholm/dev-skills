# Structuring Code for AI Coding Agents

How to structure a codebase so that agents (Claude Code, Cursor, Copilot, Aider, Devin) can read and modify it correctly. Grounded in observed agent failure modes, not generic clean-code advice.

**Core heuristic:** write so that an agent grepping a single file can act correctly without reading the rest of the repo.

Humans get lost in **complexity**. Agents get lost in **indirection**. Several classical principles (deep DRY, heavy DI, abstract base classes) invert when the reader is an agent with a limited context window navigating by `grep` and file reads.

---

## Priority 1 — The non-negotiables

These have the strongest evidence base and the largest effect on agent success. Fix these first.

### 1. Name things for localization, rename on refactor

**Failure mode it prevents:** Agents localize code by grepping names. In controlled studies, obfuscating identifiers drops comprehension accuracy from ~87% to ~59%. Worse: *shuffled* (misleading) names perform worse than *random* names — the agent confidently acts on the wrong mental model. Aider's repo-map and Cursor's retrieval both rank code by symbol references; a well-named function surfaces automatically, a `process()` does not.

**Do:**

- Use domain-verb names: `issueRefundAndNotifyCustomer`, `reverseStripeCharge`, `chargeCustomerAndEmitReceipt`.
- Rename aggressively during refactors. Stale names are load-bearing lies.
- Make the filename answer "where does this live": `billing/refunds.ts`, not `services/BillingService.ts`.

**Don't:**

- Use banlist names: `Manager`, `Service`, `Helper`, `Handler`, `Util`, `process`, `handle`, `doStuff`, single-letter variables outside tight loops.
- Create dumping-ground files: `utils.py`, `helpers.ts`, `common.js`, `misc.py`.

**Before:**

```python
# utils.py (1,200 lines of unrelated functions)
def process(data): ...
def handle_it(x, y): ...
class Manager:
    def do_stuff(self, thing): ...
```

An agent asked "where is the refund logic?" greps for `refund`, finds nothing, scans `utils.py` and `Manager.py`, and runs out of context before finding it.

**After:**

```python
# billing/refunds.py
def issue_refund_and_notify_customer(order_id: str, reason: RefundReason) -> Refund: ...
def reverse_stripe_charge(charge_id: str) -> None: ...
```

`grep refund` now returns one file. The name answers "what does it do?" before the agent opens the file.

**Exception:** Published library names that consumers depend on. Don't rename `process()` in a public API just for internal agent hygiene — evolve it or wrap it.

---

### 2. Colocate by feature (vertical slices), not by technical layer

**Failure mode it prevents:** The most common systemic bug across all agent platforms: a feature that spans `controllers/` + `services/` + `middleware/` + `triggers/` + `workers/`. The agent patches three of five touchpoints and ships a subtle regression. SWE-Bench Pro data: frontier models score under 45% Pass@1 on multi-file edits — semantic correctness across files is where they fail.

**Do:**

```
src/billing/refunds/
├── index.ts              # 40 lines: public API + re-exported types
├── types.ts              # 30 lines: Refund, RefundReason, RefundStatus
├── issue-refund.ts       # 120 lines: one exported function, typed
├── issue-refund.test.ts  # colocated unit test
├── reverse-charge.ts
└── reverse-charge.test.ts
```

Everything an agent needs to reason about "refunds" loads as a single coherent unit.

**Don't:**

```
src/controllers/BillingController.ts
src/services/RefundService.ts
src/middleware/BillingAuth.ts
src/workers/RefundWorker.ts
tests/unit/services/RefundService.test.ts
```

To change refund behavior, an agent must load five files from five directories and hope it found all of them.

**Exception:** Framework-enforced layouts (Next.js `app/`, Rails MVC, Django apps, NestJS modules). Don't fight the framework. Instead, build feature directories *within* each framework slot and cross-link them with clear imports.

---

### 3. Types and accurate docs at module boundaries; no stale comments

**Failure mode it prevents:** A controlled study found that *incorrect* docstrings crashed GPT-3.5 task success to 22% and GPT-4 to 68%. Missing docstrings had no significant effect. Stale comments are confidently-wrong oracles; agents trust them.

**Do:**

- Annotate every public function signature. Types are the contract retrievers and constrained-generation systems trust.
- Write `// why:` comments — hidden constraints, past incidents, non-obvious invariants. Delete any comment that restates the code.
- When you change behavior, update or delete the adjacent comment *in the same commit*.

**Before:**

```python
def charge(user, amount, **opts):
    """Charges a user and returns True on success. Sends email receipt."""
    # (code no longer sends email; now returns a Charge object)
    ...
```

Agent trusts the docstring, writes `if charge(...)`, which is truthy for any `Charge` object, silently masking failures.

**After:**

```python
def charge(user: User, amount: Money, *, idempotency_key: str) -> Charge:
    # why: Stripe rejects duplicate charges within 24h; idempotency_key must be stable per intent.
    ...
```

The signature is the spec. The one comment is non-obvious context the agent cannot infer.

---

### 4. Give the agent a verification loop

**Failure mode it prevents:** Without feedback, agents hallucinate into spirals. Documented case (Surge HQ, 2025): Gemini produced 693 lines of wrong patches over 39 turns because it had no way to verify between edits. Anthropic's own guidance frames "if you can't verify it, don't ship it" as the single highest-leverage rule.

**Do:**

- Colocate tests with the file under test: `refunds.ts` + `refunds.test.ts` in the same directory.
- Provide **one command** in a top-level `Makefile`, `justfile`, or `package.json` script that runs lint + typecheck + tests. Document it in `AGENTS.md` / `CLAUDE.md`.
- Prefer compile-time failures over runtime failures. Type errors that fire at the edit site are feedback the agent reads immediately.

**Don't:**

```
src/billing/refunds.ts
tests/unit/billing/refunds.test.ts         # distant mirror
tests/integration/billing/refunds.integ.ts
```

Agent edits `refunds.ts`, doesn't see adjacent tests, skips testing or invents a new test file in the wrong place. CI catches it a turn later, after wasted context.

**Exception:** Deliberate integration/e2e directories — keep those top-level, but keep unit tests colocated.

---

## Priority 2 — Structural rules with strong tool-behavior evidence

### 5. Keep files under ~800 lines and free of near-duplicate blocks

**Failure mode it prevents:** Two separate problems that both break string-replacement edits:

- **File size:** Morph LLM (a vendor building apply models) reports predictable merge failures on files over ~1,000 lines. Combined with the "lost in the middle" position bias (Liu et al., 2023), mid-file content is retrieved much worse than content at the start or end.
- **Near-duplicates:** Claude Code's `str_replace` and Aider's SEARCH/REPLACE both require unique context lines. Thirty identical catch blocks mean zero usable edit targets; the agent falls back to rewriting the whole file and truncates.

**Do:**

- Target files under 800 lines. Break by responsibility *inside* a feature directory, not across layers.
- Factor repeated error handling, validation, and logging into one helper **at the seam**.

**Before (one 1,400-line `api/routes.ts`, 30 handlers with the same catch block):**

```ts
export async function createOrder(req, res) {
  try { /* 40 lines */ }
  catch (err) {
    if (err instanceof ValidationError) {
      logger.warn({ err, path: req.path });
      return res.status(400).json({ error: err.message });
    }
    logger.error({ err, path: req.path });
    return res.status(500).json({ error: "Internal error" });
  }
}
// ...29 more handlers with identical catch
```

Agent's `str_replace` on any catch block matches 30 places and fails.

**After (files per resource + shared error helper):**

```ts
// api/orders/create.ts (70 lines)
import { handleError } from "../errors";
export async function createOrder(req, res) {
  try { /* logic */ } catch (err) { return handleError(err, req, res); }
}
```

One seam, zero duplicates, every file under ~200 lines.

**Exception:** Data models, DTOs, migrations, fixtures. Their repetitive shape is the domain, not a refactor opportunity. A little duplication *inside a leaf function* is fine too — premature abstraction is worse than duplication.

---

### 6. Prefer static, grep-traceable dependencies over metaprogramming

**Failure mode it prevents:** Code the agent can't trace with grep or a shallow AST walk is code the agent hallucinates around. Documented: ETH SRI Lab caught an agent literally asking itself "has `get_str_vals` been monkey-patched?" before producing a wrong fix. DAPLab's 2026 failure-pattern study ranks reflection, metaprogramming, and heavy DI among the top agent-failure triggers across Claude Code, Cursor, and Devin.

**Do:**

- Prefer composition and explicit imports.
- Keep decorators declarative (logging, routing, validation). Avoid decorators that rewrite behavior.
- If you must use DI, wire it at the edges of the app — not threaded through every layer.

**Don't:**

- `__getattr__`, `eval`, `exec`, `importlib.import_module`, JS `Proxy`, `Reflect`, runtime monkey-patching.

**Before — dynamic dispatch via `__getattr__`:**

```python
class API:
    def __getattr__(self, name):
        endpoint = name.replace("_", "-")
        return lambda **kw: self._request(endpoint, **kw)

api.refund_payment(id=...)   # grep for "refund_payment" returns nothing
```

Agent invents a definition or rewrites the call in a way the dispatcher can't handle.

**After — explicit methods:**

```python
class API:
    def refund_payment(self, payment_id: str) -> Refund:
        return self._request("refund-payment", payment_id=payment_id)
```

Grep works. Types flow. The "duplication" is the price of searchability.

**Exception:** When metaprogramming *is* the product — ORMs, validation libraries, DI frameworks, DSLs. Don't linter-clean these; document them heavily in `AGENTS.md`.

---

### 7. Flatten inheritance; prefer composition beyond ~3 levels

**Failure mode it prevents:** Agents fabricate method resolution paths on deep chains. Surge HQ's 693-line spiral: Gemini invented `super().__init__` signatures into parents it had never seen. ACL 2025's SWE-Bench study: ~52% of failures are "incorrect implementation," a meaningful fraction involving wrong inheritance assumptions.

**Before — five-level chain:**

```python
class Base: ...
class Entity(Base): ...
class Persisted(Entity): ...
class Auditable(Persisted): ...
class User(Auditable): ...
```

Agent asked to add `last_login` fabricates a `super().__init__` signature from `Persisted` it has never actually read.

**After — composition:**

```python
class User:
    def __init__(self, id: str, email: str):
        self.id = id
        self.email = email
        self.audit = AuditLog(entity_id=id)
        self.persistence = PersistenceMeta()
```

Each collaborator is a field the agent can grep for. No MRO puzzle.

**Threshold note:** 3 levels is a heuristic, not a hard limit. Framework base classes (`React.Component`, `Django Model`) don't count toward your own depth.

---

### 8. Keep minified, generated, and very-long-lined files out of the source tree

**Failure mode it prevents:** `ripgrep` matches on a 38,000-character single line spill the entire line into the agent's context and can break tool-output parsing. Agents end up with dropped matches or truncated reasoning.

**Do:**

- Put vendored/minified assets in `public/vendor/`, `dist/`, or `build/`.
- Add them to `.gitignore`, `.claudeignore`, `.cursorignore`, and `.aiderignore` as appropriate.
- Wrap long string literals or extract them into JSON/YAML beside the source.

---

## Priority 3 — Meta-level scaffolding

### 9. Provide an `AGENTS.md` / `CLAUDE.md` that answers "where things live and how to verify"

**Failure mode it prevents:** DAPLab's 2026 analysis of 2,500+ agent-instruction files: agents don't need project history, they need *where things live and what rules to follow*. Narrative README prose can actively mislead.

Include:

- The one command that lints + typechecks + tests.
- The top 5-10 directories and what lives in each.
- Framework conventions that override general advice (e.g., "in this repo, Next.js routing wins over feature-colocation").
- Safety rails: what the agent must not touch (secrets, migrations, public API).
- A small set of canonical code examples to imitate.

Skip: project history, philosophical manifestos, anything that restates code.

---

### 10. Make error signals point at the edit site, not downstream

**Failure mode it prevents:** Agents need feedback in the turn they made the change. A `TypeError` at runtime, three files away, arrives too late — by the time it surfaces, the agent has moved on or context has been consumed.

**Do:**

- Validate inputs at module boundaries (Zod, Pydantic, class-validator) so a misuse fails loudly at the call site.
- Prefer `readonly` / `Literal` / branded types that make invalid states unrepresentable.
- In Python, run `mypy --strict` on new code. In TS, keep `strict: true`.

---

## What still applies from classical principles

This is not "SOLID and DRY are dead." Humans still read code; agents are one reader, not the only reader.

- **KISS, YAGNI** — unchanged. Simple code helps both audiences.
- **DRY** — right *in spirit* (one source of knowledge), frequently wrong *in letter* (deduplicate anything that rhymes). For agents, premature abstraction is worse than duplication: three similar lines in one file are cheap; one wrong abstraction shared across ten files is expensive.
- **SRP** — the most portable letter of SOLID. A function that does one thing has one name, and the name can be specific.
- **DIP / ISP** — often push toward indirection that hurts both agents and humans on small teams. Apply only where swap-out is a real, near-term need.

**Decide by lifetime and blast radius.** A throwaway script has a reader of ~1; skip the ceremony. A payments module maintained for ten years earns every clarity investment you make.

---

## Quick audit checklist for an existing codebase

Use these in order; each finds a concrete class of agent failure.

1. `find . -type f -name '*.py' -o -name '*.ts' | xargs wc -l | sort -rn | head -20` — anything over 800 lines is on the shortlist to split.
2. Grep for banned names: `rg -w '(Manager|Service|Helper|Handler|Util|process|handle|doStuff)'` — candidates for rename.
3. Grep for metaprogramming: `rg '__getattr__|\beval\(|\bexec\(|importlib|new Proxy|Reflect\.'` — candidates to replace with explicit calls.
4. Check test location: are `*.test.*` files adjacent to their source, or in a distant tree?
5. `ls` the repo root: is there a single command that runs lint + typecheck + tests? Is there an `AGENTS.md` / `CLAUDE.md`?
6. Open three "public entry points" at random (e.g. a route handler, a job handler, a CLI command). Is every public signature typed? Do the docstrings match the current behavior?

Fix in this order: types on public boundaries (#6) → verification loop (#5) → rename banlist (#2) → split big files (#1) → remove metaprogramming (#3) → colocate tests (#4). This ordering front-loads the cheap, high-leverage wins.
