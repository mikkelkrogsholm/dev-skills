# Rationale

This document explains each refactor decision in terms of what it buys an
AI agent reading, editing, or extending the code.

## Module split and rename

**Before:** one file called `utils.py` holding arithmetic, dynamic imports,
dynamic attribute dispatch, and a domain hierarchy.

**After:** a single module whose docstring names its responsibility —
"User domain model and a small, explicit helper surface." The name still
lives under `utils.py` in this fixture (the file path is fixed), but the
module-level docstring and `__all__` make its scope explicit. In a real
codebase the file would be renamed to `users.py` and the helpers moved to
`arithmetic.py` / `operations.py` accordingly.

**Why it helps agents:** discoverability. An agent that wants "the user
model" no longer has to read every symbol to confirm it is in the right
place.

## Renamed `process` -> `identity`, `handle` -> `add_integers`

**Why:** verbs like `process` and `handle` tell neither humans nor agents
what the function does. Concrete names ("identity", "add_integers") are
self-describing and collision-resistant across the codebase.

## Added full type annotations

Every public function and method now has parameter and return types, and
`User` / `AuditRecord` are declared as dataclasses so their field types
are visible to both `mypy` and any agent doing structural reasoning.

**Why:** types let an agent answer "what does this return?" without
reading the body, and let refactoring tools move symbols safely.

## Removed `eval` and `importlib.import_module`

`run_expression` and `dynamic_import` were deleted outright. They were
AR004 red flags for good reason: they make it impossible to statically
determine what code runs. The file now includes a comment block pointing
callers to safer alternatives (`asteval`, `importlib.metadata`
entry_points with an allow-list).

**Why:** agents reasoning about call graphs, security posture, or
dependency trees need the imported/executed symbols to be visible
in source. Dynamic dispatch by arbitrary string defeats all of that.

## Replaced `DynamicAPI.__getattr__` with `OperationRegistry`

The old `DynamicAPI` swallowed every attribute access and returned a
no-op lambda, so typos produced silent success. The new
`OperationRegistry`:

- requires explicit registration,
- raises `KeyError` listing the registered operations on an unknown name,
- takes typed keyword arguments via a `Protocol`.

**Why:** loud failure beats silent no-ops. An agent that misspells an
operation now sees the mistake at runtime, and a reader can enumerate
the full surface by inspecting the registry.

## Flattened the inheritance chain

The five-level chain `User -> Auditable -> Persisted -> Entity -> Base`
has been replaced by a single `User` dataclass composing an
`AuditRecord`. None of the intermediate classes added behavior, so
nothing was lost — but the number of files/classes an agent has to hold
in working memory dropped from five to two.

**Why:** deep inheritance (AR005) multiplies the number of places
behavior can come from. Composition keeps the state flat and visible in
one place. If cross-cutting concerns emerge later, prefer `Protocol`s
or mixins added intentionally, not inherited "just in case".

## Added docstrings and `__all__`

Every public symbol now has a one-paragraph docstring that states its
purpose, and `__all__` pins the public surface. This gives agents a
crisp, authoritative answer to "what is exported from this module?"
without having to diff against callers.

## What was intentionally *not* done

- **Not** kept `run_expression` / `dynamic_import` behind a flag. If you
  need them, you are better served by an explicit, audited mechanism;
  leaving a disabled version invites re-enablement.
- **Not** kept `Manager` as a shell class. An empty class with one
  identity method is noise; `identity()` is enough.
- **Not** introduced a framework (pydantic, attrs). Stdlib `dataclasses`
  is sufficient and keeps the dependency surface minimal.
