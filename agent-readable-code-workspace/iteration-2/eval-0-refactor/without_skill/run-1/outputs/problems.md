# Problems in `utils.py` (AI-maintainability perspective)

This file is a "dumping-ground" module. Each problem below is something that
reliably causes AI coding agents (Claude Code, Cursor, Copilot, etc.) to
misunderstand the code, produce incorrect edits, or hallucinate behavior.

## 1. Meaningless module name (`utils.py`)

- `utils.py` gives an agent zero semantic signal about what belongs here.
- When asked "where should I put function X?", agents tend to dump anything
  vaguely helper-shaped into `utils.py`, which snowballs.
- Agents searching semantically (by filename) cannot find functionality because
  the filename does not describe the domain.

## 2. Generic, context-free function names (`process`, `handle`, `do_stuff`)

- Names like `process(data)`, `handle(x, y)`, `do_stuff(thing)` do not describe
  *what* is processed, *how*, or *why*.
- Agents infer behavior from names. Given `process(data)`, a downstream agent
  will guess at semantics and often pick the wrong one (e.g., mutate vs.
  return, sync vs. async, validation vs. transformation).
- Grep/semantic-search is polluted: searching for "process" across a codebase
  returns dozens of unrelated hits.

## 3. No type annotations on public functions

- `def process(data):`, `def handle(x, y):`, `def do_stuff(self, thing):` have
  no parameter or return types.
- Agents rely on type hints to: pick correct call sites, generate correct
  tests, and avoid passing the wrong shape. Without them, agents fabricate
  types based on the name — which is already generic.
- Static tools (mypy, pyright, IDE hovers that agents read) produce no useful
  signal.

## 4. No docstrings

- Zero function/class docstrings. Agents have no authoritative description of
  intent, invariants, or side effects. They invent one.

## 5. `eval()` on caller-supplied input (`run_expression`)

- `eval(expr)` is a security hole and an unbounded behavior surface. An agent
  tasked with "make `run_expression` handle dates" cannot reason about what
  the function currently accepts — it accepts *anything Python parses*.
- Agents often "fix" this by adding more `eval` paths, worsening the problem.

## 6. Dynamic `importlib.import_module` dispatch (`dynamic_import`)

- Dynamic import by string name hides the dependency graph. Agents cannot
  trace callers/callees, cannot update imports during refactors, and cannot
  detect dead code.
- Import errors happen at runtime, far from the code that caused them.

## 7. `__getattr__`-based dispatch (`DynamicAPI`)

- `__getattr__` returning a `lambda **kw: None` means *every attribute access
  succeeds* and silently does nothing.
- Agents cannot enumerate the API, cannot autocomplete, cannot type-check,
  and cannot tell a typo from a real call. Tests pass that should fail.
- This is the single most hostile pattern to AI maintenance in the file.

## 8. Deep, empty inheritance chain (`Base -> Entity -> Persisted -> Auditable -> User`)

- Five levels of inheritance, every intermediate class is empty (`pass`).
- Agents must read five files/classes to understand what `User` is. When they
  edit `User`, they often miss behavior that "should" live in `Auditable` or
  `Persisted` because those classes are empty but named as if they carry
  responsibility.
- Empty base classes suggest planned extension points that do not exist —
  agents will add code to the wrong level.
- Prefer composition or a single flat class with explicit fields.

## 9. Pass-through / no-op functions

- `process(data)` returns `data` unchanged. `do_stuff(thing)` returns `thing`.
- Agents see these as "probably a stub" and either delete them or fill them
  in with hallucinated behavior. Either action is likely wrong if the
  function is actually meant to be a no-op (identity) — which should be made
  explicit.

## 10. `handle(x, y)` returns `x + y` with untyped `x`, `y`

- `+` is overloaded (numbers, strings, lists, custom `__add__`). With no
  types, agents cannot tell whether this is arithmetic, concatenation, or
  something else. They guess, and half the time guess wrong.

## 11. Module-level docstring documents lint codes, not purpose

- The current docstring lists AR003/AR004/AR005/AR006 violations. This is
  meta-commentary for a linter, not information a maintainer (human or AI)
  can use to decide what goes in this module.

## 12. No `__all__`, unclear public surface

- Nothing signals which names are exported/public vs. internal. Agents
  importing from this module cannot tell if `Base` is meant to be used
  externally or is an internal detail.
