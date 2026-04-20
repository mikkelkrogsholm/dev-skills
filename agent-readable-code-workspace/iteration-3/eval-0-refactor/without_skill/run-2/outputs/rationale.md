# Refactor Rationale

This document explains the changes made from `utils.py` to `refactored.py` and
why each change improves maintainability — particularly for AI agents that must
reason about the code statically.

## Scope change: module responsibility

**Before:** `utils.py` held unrelated helpers, an unsafe expression runner, a
dynamic importer, a catch-all dispatcher, and a 4-level domain hierarchy.

**After:** The refactored module is scoped to "user domain model + two tiny,
explicitly-typed helpers." The file name in a real codebase should be changed
from `utils.py` to something like `users.py` — `utils` is a non-name. The
docstring at the top now tells a reader exactly what is (and is not) provided.

Agents benefit because the module has one reason to change, and the import
graph becomes meaningful.

## Rename: `process(data)` → `identity(value)`

`process` implies transformation but performed none. Either the transformation
was missing (a bug) or the function was a no-op. The refactor:

- Renames to `identity` so the contract matches the behavior.
- Adds `TypeVar`-based typing so static analyzers know the return type equals
  the argument type.
- Documents in the docstring that callers who *did* want a transformation
  should call a purpose-named function instead.

If the original author actually intended a transformation, that logic must be
added explicitly at a specific call site — not hidden behind a generic name.

## Rename: `handle(x, y)` → `add_integers(left, right)`

`handle` is semantically empty. The body was `x + y`, which in Python is
overloaded across ints, floats, strings, lists, and custom `__add__`
implementations. The refactor:

- Chooses a concrete contract (integer addition) and names it accordingly.
- Adds `int` annotations so the caller gets a type error for wrong inputs.
- Makes the function trivially inlineable — if a caller only ever adds two
  ints, they can just write `a + b` and delete this helper.

## Deleted: `run_expression(expr)` (the `eval` wrapper)

`eval` is unsafe and opaque. Keeping a thin wrapper around it makes the
problem worse because it presents an innocent-looking API over arbitrary code
execution. The correct replacement depends on the real need:

- If callers pass arithmetic expressions from a trusted source, use
  `ast.literal_eval` or a dedicated expression parser.
- If callers pass a fixed set of commands, replace with a `dict` dispatch
  table of typed callables.
- If callers pass user input, parse it with a real grammar (e.g., `lark`,
  `pyparsing`) and never reach `eval`.

This function is intentionally omitted from `refactored.py` so that callers
are forced to make that choice explicitly at the call site.

## Deleted: `dynamic_import(name)` (the `importlib` wrapper)

Direct `import foo` statements are:

- Visible to bundlers, linters, dependency graphs, and LLM tooling.
- Statically analyzable for cycles, missing modules, and unused imports.

`importlib.import_module(name)` defeats all of that. Legitimate uses (plugin
discovery, optional dependencies) should happen at a well-defined plugin
boundary with a registry, not in a generic `utils` helper. Removing the
wrapper forces each caller to justify the dynamic import explicitly.

## Deleted: `DynamicAPI.__getattr__` catch-all

Returning a silent no-op lambda for any attribute access means any typo
succeeds and any future method addition may collide with an existing fake
attribute. This is the opposite of agent-readable: the "API surface" is
infinite and invisible.

The correct replacement is to enumerate the real methods as typed methods on
a class (or a `Protocol`). If the original code was scaffolding for a test
double, `unittest.mock.MagicMock` already provides that behavior with better
introspection — no bespoke class needed.

## Flattened: `Base → Entity → Persisted → Auditable → User` → single `@dataclass`

Each parent class in the original chain was empty (`pass`). The taxonomy
carried no behavior and no data, so it imposed cognitive cost without
benefit. The refactor collapses the chain into a single `@dataclass(frozen=True)`
with explicit fields:

- `id` captures what `Entity` was trying to mean.
- `created_at` captures what `Persisted` was trying to mean.
- `updated_at` captures what `Auditable` was trying to mean.
- `email` is a concrete field a real `User` needs.

Advantages:

- MRO is trivial (depth 1 from `object`).
- Fields are visible in one place; an agent reading `User` sees the whole
  contract without walking four parent classes.
- `frozen=True` makes instances hashable and prevents accidental mutation,
  which was likely the point of "Auditable" anyway.
- If shared behavior later becomes genuinely needed, it can be introduced via
  a `Protocol` or a mixin — additively, without committing to a taxonomy
  up-front.

## Added: `__all__`, `from __future__ import annotations`, module docstring

- `__all__` makes the public surface explicit, so `from module import *` and
  documentation generators agree with what the author considered public.
- `from __future__ import annotations` keeps runtime cost zero and lets the
  type checker evaluate forward references consistently.
- The module docstring states scope and explicitly calls out what was
  intentionally *not* re-implemented, so future maintainers (human or agent)
  do not re-introduce the unsafe patterns.

## What an agent can now do that it couldn't before

1. Read the top-of-file docstring and know the module's scope in seconds.
2. Predict the behavior of every public symbol from its name and signature
   alone, without reading the body.
3. Trace all imports statically — no `importlib.import_module` surprises.
4. Trust that attribute access on any object will raise on typos rather than
   silently succeed.
5. Inspect `User` as a single flat record rather than a 4-level hierarchy.
