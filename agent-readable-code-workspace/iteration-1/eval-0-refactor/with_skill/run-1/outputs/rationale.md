# Rationale

Every change below is grounded in a concrete AI-agent failure mode documented in `agent-readable-code/references/research.md`. The refactor is not cosmetic — each fix closes a class of bug that agents are empirically observed to ship.

## 1. Filename: `utils.py` -> `refactored.py` (AR003)

**Failure mode it closes:** Dumping-ground filenames defeat grep-based localization. SweRank 2025 identifies file localization as the #1 bottleneck across agent platforms — when the agent cannot find the file, it either invents a new one (duplication) or edits the wrong one (silent bug).

**Why this matters concretely:** An agent asked "add a new audit event type" greps for `audit` and finds the module immediately. If the same code lived in `utils.py`, it would grep for `utils` (unhelpfully broad) or miss the file entirely.

**Scope of change:** In a real project the file would live at `user_audit/events.py`. The task only required one file named `refactored.py`, so that's what was produced, with a docstring note on real-world placement.

## 2. Renamed `process`, `handle`, `Manager`, `do_stuff` to concrete verbs/nouns (AR003)

**Failure mode it closes:** Liu et al. 2025 ("When Names Disappear") measured a drop from **87.3% -> 58.7%** in class-summarization accuracy when identifiers are obfuscated. The 2024 naming-effect study further found that **misleading names are worse than random names** — an agent reads `process` and confidently assumes it can substitute a call to another `process` elsewhere, producing silent semantic breakage.

**Concrete renames:**
- `process(data)` -> `normalize_email(email)` — states the effect.
- `handle(x, y)` -> `sum_event_counts(a, b)` — states both the effect and the domain.
- `class Manager` -> deleted; its sole method moved into the domain type `AuditTrail.record`.
- `do_stuff(thing)` -> `AuditTrail.record(action, actor_id)`.

**Caveat:** The original file was a fixture with no real domain, so concrete names were inferred from the class names (`Entity`, `Persisted`, `Auditable`, `User`) that already pointed at an audit-log domain. In a real refactor, the existing call sites determine the names — but the *strategy* is identical: every name must tell the reader what the code does.

## 3. Added type annotations to every public signature (AR006)

**Failure mode it closes:** Type-Constrained Code Generation 2025 shows explicit annotations measurably reduce API-retrieval hallucination. And per the 2024 docstring study, **incorrect** annotations are worse than **missing** ones — so the refactor adds types only where they are correct and load-bearing.

**Concrete impact:** An agent considering a call site of `normalize_email` now sees `(email: str) -> str` and cannot legitimately pass a `dict` or expect `None` back. The compile-time signature replaces runtime archaeology.

## 4. Removed `eval`, removed `importlib.import_module`, replaced with a static registry (AR004)

**Failure mode it closes:** The ETH SRI "Fixing Correct Code" postmortem documents an agent asking itself "has `self.data.get_str_vals` been monkey-patched?" before shipping a wrong fix. When dispatch is dynamic, grep-based traversal cannot see the call graph — the agent fills the gap with confabulation.

**What the refactor does:**
- `eval(expr)` is deleted outright. It is not safe to expose, has no legitimate non-REPL use in an audit module, and is the canonical example the linter flags.
- `importlib.import_module(name)` is replaced by `AUDIT_EVENT_FORMATTERS`, a `Mapping[str, AuditEventFormatter]`. The only legitimate use of dynamic import in the original — "look up a behavior by string name" — is preserved, but every possible value of the string is now visible in a single grep-able dict.
- `DynamicAPI.__getattr__` is deleted. Its behavior (synthesize a no-op callable for any attribute) is exactly the "invisible method" pattern the research flags; if callers really need a null object, they should instantiate a typed one with explicit methods.

**Concrete agent benefit:** To add a new formatter, an agent edits one dict. To understand what formatters exist, an agent reads one dict. No runtime tracing required.

## 5. Collapsed 5-level inheritance into composition (AR005)

**Failure mode it closes:** The Surge HQ 693-line-spiral postmortem documents Gemini inventing `super()` calls into nonexistent parents and then patching the consequences for 39 turns. Deep chains force the agent to hold an MRO in its head; it fabricates instead.

**What changed:** `Base -> Entity -> Persisted -> Auditable -> User` (depth 4) became a single dataclass `User` that *composes* an `AuditTrail` via a `audit_trail: AuditTrail` field. The audit-event capability is now a method call on a collaborator — an agent can jump to its definition in one grep, with no MRO puzzle.

**Why composition and not "just shorten the chain":** The chain encoded three orthogonal capabilities (identity, persistence, auditability). Persistence is not implemented anywhere and should not be a base class — that's the bug agents would actually ship, adding fake `save()` methods inherited from `Persisted`. Composition forces each capability to be explicit and wire-visible.

## 6. Added a `_self_check` verification affordance (AR007)

**Failure mode it closes:** Anthropic's "Best Practices for Claude Code" frames "if you can't verify it, don't ship it" as the single highest-leverage rule. Without a verification loop, Surge HQ's Gemini spiraled into 693 lines of wrong patches.

**What it provides:** A zero-dependency smoke test runnable with `python refactored.py`. An agent that edits this file gets immediate feedback on whether it broke the basic invariants — no test framework, no config, no human in the loop. In a real project this would be a `refactored_test.py` colocated in the same directory, but a single-file artifact gets the same affordance via `__main__`.

## 7. A note on *what was not changed*

- The `dataclass` decorator remains even though `AR004` flags some decorators. `dataclass` is **declarative** and visible to every static tool; it is the kind of metaprogramming the skill explicitly permits ("If you use decorators, keep them declarative — don't rewrite behavior"). This is a case where the skill's "When NOT to apply" guidance applies.
- Docstrings are intentionally sparse. The skill warns that **wrong docstrings are worse than missing ones** (22.1% task success vs. baseline, 2024 study). Every docstring in the refactor is a *why* (rationale, invariant, caveat), never a restatement of what the code already says.
- The `KeyError` raised by `format_audit_event` on an unknown format name is documented but not wrapped. Exceptions are a verification signal — swallowing them would hide the kind of input error an agent needs to see.

## Summary table

| Rule | Original lines | Refactor | Failure it prevents |
|---|---|---|---|
| AR003 (filename) | `utils.py` | `refactored.py` (+ docstring note on feature-dir placement) | Localization failure; dumping-ground pollution |
| AR003 (names) | `process`, `handle`, `Manager`, `do_stuff` | `normalize_email`, `sum_event_counts`, `AuditTrail.record` | Misleading-name confabulation (worse than random) |
| AR006 | 5 untyped public signatures | All typed; `from __future__ import annotations` | Seam hallucination; wrong call-site construction |
| AR004 | `eval`, `importlib.import_module`, `__getattr__` | Deleted or replaced by a static `Mapping` registry | Invisible dispatch; agent spirals |
| AR005 | 4-deep inheritance chain | Single dataclass composing `AuditTrail` | Fabricated MRO; fake inherited methods |
| AR007 (implicit) | No verification | `_self_check()` runnable as `__main__` | 693-line hallucination spiral pattern |
