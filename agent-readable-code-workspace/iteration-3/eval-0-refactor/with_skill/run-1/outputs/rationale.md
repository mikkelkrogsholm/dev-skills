# Rationale

This refactor applies the six practices from `agent-readable-code/SKILL.md` to the fixture `bad_py/utils.py`. The key move is that most of the original file is **deleted, not renamed** — each function was either unsafe, trivially inlinable, or an agent-hostile facade.

## Per-practice decisions

### Practice 1 — Name for localization (`AR003`)

**What changed.**

- `utils.py` is replaced by a domain-named module (`user.py` in a real repo, written here as `refactored.py` per the task's file-naming constraint). The filename itself now tells an agent greping for "user" that this is where it lives.
- `process`, `handle`, `Manager`, `do_stuff` are deleted. They communicated nothing. When the real action behind a call is knowable, a domain verb (`issue_refund_and_notify_customer`, `reverse_stripe_charge`) goes in; when the action is not knowable, the function should not exist.

### Practice 3 — Small, unique files (`AR001`, `AR002`, `AR008`)

The original was already short, but its *scope* was unbounded — an agent would pile more unrelated helpers into it. Restricting this file to the `User` value object keeps the module's purpose discoverable and prevents future AR001/AR002 drift.

### Practice 4 — Static, explicit dependencies (`AR004`, `AR005`)

**Deleted outright:**

- `eval(expr)` — executing arbitrary strings is both a security hole and untraceable. No well-formed replacement; the caller should be audited and rewritten to a named operation.
- `importlib.import_module(name)` — hides the module graph. Real callers should use `from x.y import z` so the dependency shows up in grep and in every static analysis tool.
- `DynamicAPI.__getattr__` — the canonical AR004 anti-pattern. Per `references/patterns.md`, the fix is one explicit method per endpoint with typed parameters and return types. The "duplication" is the price of being searchable.

**Inheritance.** The `Base -> Entity -> Persisted -> Auditable -> User` chain is replaced by a single `User` dataclass. Auditing, persistence, and entity metadata — if they had content — belong as composed fields (`self.audit = AuditLog(...)`), exactly as shown in `patterns.md` under AR005. Here the original classes were empty, so there is nothing to port.

### Practice 5 — Types at boundaries (`AR006`)

The surviving `User` has typed fields (`id: str`, `email: str`). If this were a real codebase, these would become branded types — `UserId = NewType("UserId", str)` — so that agents cannot swap a user id and an org id at a call site. That upgrade is flagged here rather than invented from thin air, because nothing in the fixture tells us which other ID types exist.

Docstrings state only the *why* (why `frozen=True`, why `slots=True`). They do not restate the fields — the type signature is the spec. An accurate short comment beats a verbose stale one.

### Practice 6 — Verification affordances (`AR007`)

A colocated `refactored_test.py` / `user_test.py` would accompany this module in a real repo. It is omitted here because the task asked for three named files, not a full module layout; the problems.md entry flags this as outstanding work.

### Practice 8 — Python-specific idioms

- `__all__ = ["User"]` — makes the public surface explicit so agents do not start importing private helpers.
- `@dataclass(frozen=True, slots=True)` — two distinct agent-safety wins:
  - `frozen=True`: an agent "fixing" a call site by assigning `user.email = new_email` fails at runtime instead of silently diverging from the value-object contract.
  - `slots=True`: a typo like `user.emial = "x"` raises `AttributeError` at the edit site rather than creating a ghost attribute.
- `from __future__ import annotations` — defers evaluation so forward references (common in larger type graphs) do not break imports.

## What was *not* done, and why

- **No generic "utility" helpers were kept.** `process(data) -> return data` is either dead code or a shim whose real intent lives at the call site. Removing it forces the call site to be explicit. If keeping it were required by an external API, it would stay under its *external* name and be annotated with a `# agent-lint: disable=AR003` suppression per SKILL.md's "When NOT to apply this skill" guidance.
- **No `Manager` replacement class.** The original contained no behavior. Creating an empty `UserService` would reintroduce the same AR003 problem under a different name.
- **No dynamic-import shim.** Callers should `from package import symbol` directly. Central re-export modules ("barrels") trigger the same agent-navigation pathology AR004 describes.
- **Inheritance was flattened, not rebuilt with mixins.** Mixins are a softer version of the same MRO puzzle; composition via fields wins on grep-ability.

## Expected lint result

Running `scripts/lint.py` against `refactored.py` should produce no findings under `AR001`, `AR002`, `AR003`, `AR004`, `AR005`, `AR006`, or `AR008`. `AR007` would still flag the absence of a colocated test file; that is the single known remaining gap, called out in `problems.md`.
