# Rationale: why each change reduces a concrete AI failure mode

Each section names the change, the rule from the `agent-readable-code` skill,
and the specific failure mode the change prevents — not the aesthetic
preference it satisfies.

## 1. Renamed the file in spirit (`utils.py` → audit/expression module)

**Rule:** AR003 (dumping-ground filenames).

**Failure mode prevented:** an agent greps for a domain concept across the
tree, hits several `utils.py`, and picks the wrong one. `utils.py` carries
zero retrieval signal. The replacement has a narrow, grep-targetable
responsibility stated in its docstring ("user audit records and a small
safe-expression evaluator"). A future agent scanning file names now knows
whether this file is relevant without opening it.

Note: the artifact is still named `refactored.py` because that is the
requested output filename. In a real repo it would live at something like
`src/audit/user_record.py` and `src/reporting/safe_expression.py` — the
module docstring states that intent explicitly so the next agent knows this
is a transition state, not the endgame.

## 2. Replaced `process`, `handle`, `Manager.do_stuff` with named functions

**Rule:** AR003 (generic names).

**Failure mode prevented:** controlled studies (Shin et al., Tian & Treude)
show that method/function names are the single largest driver of model
comprehension accuracy. `process`/`handle`/`do_stuff` are three of the most
common misleading-name anti-patterns because they appear everywhere in
training data attached to *different* behaviors. A misleading name is worse
than a random one — the agent confidently acts on the wrong mental model.

Concrete replacements:

- `process(data)` — deleted; it was an identity function and not load-bearing.
- `handle(x, y)` → `sum_integers(left: int, right: int) -> int`.
- `Manager.do_stuff` → deleted; there was no behavior to preserve.

## 3. Replaced `run_expression(eval(...))` with `evaluate_arithmetic`

**Rule:** AR004 (metaprogramming / invisible dispatch), plus security.

**Failure mode prevented:**

1. `eval` is invisible to grep and AST traversal. An agent asked "what can
   this expression do?" cannot answer without running the program.
2. The replacement uses an explicit AST walk with a visible dispatch table
   (`_BINARY_OPERATORS`, `_UNARY_OPERATORS`). An agent adding a new operator
   now has exactly one place to edit, and the set of allowed nodes is
   enumerated — so the agent cannot hallucinate unsupported operators.
3. `UnsafeExpressionError` is a named, typed exception. Callers can catch it
   precisely; an agent writing a test has a concrete class to assert on.

## 4. Replaced `dynamic_import(importlib.import_module(name))`

**Rule:** AR004 (metaprogramming).

**Failure mode prevented:** `importlib.import_module(name)` defeats static
code graphs. Aider's repo-map, Cursor's embedding retriever, and Claude
Code's grep loop all rely on resolvable imports. A runtime-string import is
invisible to all three. In the refactor the function is simply gone; the
module docstring explicitly forbids reintroducing it under a new name so
that a future agent does not "helpfully" restore it.

If a real caller needed dynamic loading, the replacement would be an
explicit `dict[str, Callable]` registry in one file that consumers import
directly — the pattern the skill recommends in AR004.

## 5. Removed `DynamicAPI.__getattr__`

**Rule:** AR004 (metaprogramming via `__getattr__`).

**Failure mode prevented:** `__getattr__` returning a no-op lambda is the
worst kind of invisible surface. An agent writes `api.some_method(x=1)`,
the test passes (because anything resolves to a no-op), and the bug ships.
The class had no real surface to preserve, so it is deleted. The skill's
AR004 guidance — "prefer a discriminated union or a single registry file" —
is what we would apply if real dispatch were needed.

## 6. Flattened `User -> Auditable -> Persisted -> Entity -> Base`

**Rule:** AR005 (deep inheritance) and Python-specific guidance on
dataclasses.

**Failure mode prevented:**

- The Surge HQ 693-line spiral case study documented Gemini inventing
  `super()` calls into parents that did not exist. The deeper the chain,
  the higher the probability of fabricated method resolution.
- None of `Base`, `Entity`, `Persisted`, `Auditable` carried any behavior.
  They existed only to provide an ancestry. That is pure hallucination bait.

The replacement is one `@dataclass(frozen=True, slots=True)` with the
audit fields inlined. Benefits:

- `frozen=True` stops an agent from mutating what is supposed to be an
  immutable audit record.
- `slots=True` turns `user.foo = bar` into an immediate `AttributeError`
  instead of silently adding an attribute that causes a downstream bug.
- Composition ("audit metadata as fields") beats inheritance ("audit
  metadata as ancestor classes") for grep-first readers.

## 7. Added full type annotations on every public signature

**Rule:** AR006 (typed boundaries).

**Failure mode prevented:** untyped public signatures are empirically the
largest contributor to cross-module hallucination. Every public function
now carries parameter and return types: `evaluate_arithmetic(expression: str) -> float`,
`sum_integers(left: int, right: int) -> int`, etc. The dispatch tables
have explicit `dict[type[ast.operator], Callable[[float, float], float]]`
annotations so an agent adding an entry sees the expected shape without
reading call sites.

## 8. Added `__all__`

**Rule:** Python-specific guidance in SKILL.md section 8.

**Failure mode prevented:** without `__all__`, agents import whatever they
see (e.g., internal `_evaluate_node`) and create coupling to private
helpers. `__all__` is the one explicit "public surface" signal Python
offers. Private helpers keep their `_` prefix for belt-and-suspenders.

## 9. Replaced the wrong-oracle module docstring

**Rule:** AR006 (accurate documentation; wrong docs are worse than none).

**Failure mode prevented:** the original docstring described what was
*wrong* with the file ("Dumping-ground module. Should trigger AR003..."). A
future agent reading it would conclude the file's purpose is to be a bad
example, which is wrong in any real codebase. The new docstring states
actual responsibilities and calls out deleted symbols by name so that an
agent does not reintroduce them.

## 10. Added a security invariant as a *why* comment

**Rule:** AR006 ("only comment the why").

**Failure mode prevented:** an agent extending `evaluate_arithmetic` might
"helpfully" add `ast.Call` support to allow function calls. The explicit
invariant in the docstring — "this function must never execute arbitrary
attribute access, function calls, or name lookups" — makes the constraint
visible at the edit site, not hidden in a distant security document.

## What this refactor does *not* try to do

- **It does not add tests.** The task was to refactor the file, not to set
  up a test harness. AR007 (verification affordances) would call for
  colocated `test_refactored.py`; a real repo rollout should add it.
- **It does not rename the output file.** `refactored.py` is the requested
  artifact name. The module docstring makes clear the real fix is to split
  the file by responsibility.
- **It does not preserve dead behavior.** `process`, `handle`, `do_stuff`,
  `DynamicAPI`, and the five-level class chain carried no real logic, so
  deleting them is strictly better than renaming them. Preserving them
  under better names would have created a different AR003 problem (names
  that lie about provenance).
