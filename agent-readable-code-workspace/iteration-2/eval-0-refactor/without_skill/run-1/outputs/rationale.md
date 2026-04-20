# Rationale

Each change below is paired with the concrete failure mode it prevents when
an AI coding agent maintains this code.

## Renamed intent, not the file

The original filename `utils.py` is not renamed here because the task is to
refactor the *file contents*; but the module docstring now states the actual
domain ("User account domain model and simple arithmetic/identity helpers").

**Failure mode avoided:** agents asked "where does the user model live?"
previously could not find it by semantic search. Now the docstring makes the
module discoverable by `grep "user account"` and by embedding-based search.

## Replaced `process(data)` with `identity(value: T) -> T`

A no-op must be *named* as a no-op. The generic name `process` tricks agents
into believing the function does something domain-specific and inventing
behavior during edits. `identity` + a `TypeVar` + a docstring that says
"use as an explicit no-op callback" tells the agent exactly what this is for
and what it is not for.

**Failure mode avoided:** agent sees `process(data)`, assumes it validates or
sanitizes, silently removes a caller's own validation, introduces a bug.

## Replaced `handle(x, y)` with `add_integers(left: int, right: int) -> int`

`handle` is meaningless; `x + y` with untyped operands is ambiguous
(arithmetic? string concat? list merge?). The new function:

- Has a name that describes the operation.
- Constrains types at the signature.
- Enforces the constraint at runtime (and rejects `bool`, which is a
  subclass of `int` and a classic source of silent bugs).

**Failure mode avoided:** agent generates a test like
`handle("a", "b") == "ab"` and a test like `handle(1, 2) == 3` and both pass,
locking in contradictory behavior.

## Removed `run_expression` (was `eval(expr)`)

`eval` is deleted outright. The module docstring explicitly states that it
was removed and tells future agents *not to reintroduce it*. If a narrow
expression evaluator is later required, the module now signals the correct
approach (a typed, allow-listed implementation).

**Failure mode avoided:** agent "fixes" `run_expression` by adding more
`eval` branches, expanding the attack surface. Also prevents agents from
fabricating what `eval`-based behavior "probably" does.

## Removed `dynamic_import` (was `importlib.import_module`)

Dynamic imports hide the dependency graph. They are removed with a note in
the module docstring explaining why. If a plugin system is later needed, a
registry with explicit entries is preferable and the docstring hints at
that.

**Failure mode avoided:** agent performs a rename refactor (e.g., renames a
module) and the string-based dynamic import breaks only at runtime, outside
the agent's edit window.

## Removed `DynamicAPI.__getattr__`

A `__getattr__` that returns `lambda **kw: None` makes every attribute
access succeed silently. This is the single worst pattern in the original
file for AI maintenance: it defeats static analysis, autocomplete, type
checking, and testing simultaneously.

**Failure mode avoided:** agent writes `api.delete_user(id=42)` to a class
that never implemented `delete_user`; the call succeeds, returns `None`,
and the bug ships. Tests covering the call also pass trivially.

## Replaced the 5-level inheritance chain with a single `@dataclass User`

`Base -> Entity -> Persisted -> Auditable -> User` had four empty parent
classes. The refactor collapses them into one `@dataclass` with explicit
fields (`id`, `email`, `created_at`, `updated_at`, `is_persisted`) that
make the concepts the empty classes *hinted at* concrete.

**Failure modes avoided:**
- Agent reads five classes to understand one, then edits the wrong level.
- Agent adds a method to `Auditable` assuming it is the "audit layer," but
  `Auditable` is empty and nothing actually calls it.
- Agent cannot tell whether `Persisted` is a mixin, an ABC, or an interface,
  because it is just `class Persisted(Entity): pass`.

A dataclass also gives agents a machine-readable schema (via
`dataclasses.fields`) and works with static analyzers out of the box.

## Added `__all__`

Explicitly lists the public surface. Agents now know that `_utcnow` and
`T` are internal and that `User`, `add_integers`, `identity` are the API.

**Failure mode avoided:** agent imports `_utcnow` from another module,
creating a cross-module dependency on an internal helper.

## Added type annotations and docstrings on every public symbol

Every public function and class has:
- Full type annotations (including a `TypeVar` where genericity is real).
- A docstring stating intent, invariants, and side effects.

**Failure modes avoided:**
- Agent guesses types from names and passes wrong shapes.
- Agent cannot determine whether a method mutates `self` (now stated
  explicitly, e.g., `mark_persisted` documents that it is idempotent).
- IDE hovers that agents read during edits now carry real information.

## Factored `_utcnow` helper

Rather than calling `datetime.now(timezone.utc)` inline, the refactor uses
a named module-level helper. This is standard practice for test-patching
time, and it makes the "current time" dependency explicit.

**Failure mode avoided:** agent writing tests monkey-patches
`datetime.datetime.now` globally (hazardous), instead of patching a single
named helper.

## Used `datetime.now(timezone.utc)`, not `datetime.utcnow()`

`datetime.utcnow()` returns a naive datetime and is deprecated in Python
3.12+. A timezone-aware UTC datetime is unambiguous.

**Failure mode avoided:** agent mixes naive and aware datetimes across the
codebase, causing `TypeError: can't compare offset-naive and offset-aware
datetimes` at runtime.
