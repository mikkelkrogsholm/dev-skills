# Rationale

This refactor treats the fixture as if it were real code an agent will maintain. The `agent-readable-code` skill prescribes a clear heuristic — *write so that someone grepping a single file can act correctly without reading the rest of the repo* — and the original file violated it on every axis.

## Decisions

### 1. Rename, don't preserve

`process`, `handle`, `do_stuff`, and `Manager` are all on the skill's banlist. The skill is explicit: "stale names lie" and "a misleading name is worse than a random one." I renamed aggressively rather than wrap the old names:

- `process(data)` → `echo_payload(payload: T) -> T`
- `handle(x, y)` → `add_integers(left: int, right: int) -> int`
- `Manager.do_stuff(thing)` → **deleted** (carried no behavior, kept only to illustrate the anti-pattern)

This is the "rename aggressively" guidance under AR003. I did **not** leave aliases; aliases are their own AR003 violation (two names for one thing).

### 2. Flatten the inheritance chain

The skill calls out depth > 3 as a hallucination trigger (AR005). The original had depth 4 (`User -> Auditable -> Persisted -> Entity -> Base`) with zero behavior on any intermediate class. A flat `@dataclass(frozen=True, slots=True)` gives an agent:

- every field visible in one place
- a slotted class, so `user.typo = 1` raises `AttributeError` at the edit site (skill's Python guidance)
- `frozen=True` so a value object cannot be mutated in-place (skill's Python guidance)

If real auditable/persisted behavior is needed later, the skill's guidance is to compose (a `repository` function, an `audit_log` module) rather than inherit. That composition stays greppable.

### 3. Delete `eval`, `importlib.import_module`, and `__getattr__`

All three are listed explicitly under AR004. The fixture exists to demonstrate anti-patterns, so there is no real caller to preserve — the correct refactor is deletion. I considered replacing them with safe analogues:

- **`run_expression`** could become a tiny arithmetic parser, but that is scope creep — the fixture gives no hint of what expressions it needs to evaluate. Ship nothing rather than a speculative API.
- **`dynamic_import`** could become an explicit registry dict (`REGISTRY: dict[str, Callable] = {...}`). Again, no caller exists, so there is nothing to register. The skill is explicit: "Prefer a discriminated union + one exhaustive `switch`, or a single registry file imported explicitly by consumers." If dispatch becomes necessary, a registry is the target — but only when a consumer exists.
- **`DynamicAPI.__getattr__`** silently returns a no-op lambda for any attribute name. This is worse than a missing method: it hides bugs behind success. Deleted with no replacement.

The deletions are documented in a comment block at the bottom of `refactored.py` so a future agent or human greps the old names and finds an explicit record of why they are gone.

### 4. Type every public signature

AR006: "A typed public signature anchors the agent against fabrication." Every remaining function has explicit parameter and return types. `echo_payload` uses a `TypeVar` so the identity relationship is visible to the type-checker — an agent writing `result: int = echo_payload("x")` gets a compile-time error rather than a runtime surprise.

### 5. Add `__all__`

The skill's Python section is explicit: `__all__` on every module with public exports. Without it, `from utils import *` would previously have dragged `importlib`, the entire inheritance chain, and every intermediate class into the consumer's namespace. The new `__all__` exposes exactly three names.

### 6. Replace the docstring

The original docstring described *what rules the file violated* — a meta-comment that will rot the moment anyone edits the file. AR006: "Wrong docstrings are worse than missing ones." The new docstring describes the module's purpose and, importantly, the rule for adding code to it (don't — create a domain module instead). That rule is actionable by an agent.

### 7. The filename

The skill banlists `utils.py` outright. In a real refactor I would rename the file (e.g. `payload_helpers.py` or split into `arithmetic.py` + `users.py`). The task constraints here are to produce a single `refactored.py`, so the content has been made as non-dumping-ground-like as possible: tightly scoped, explicit exports, and an in-file rule against future growth. The deliverable's filename reflects the artifact name the task asked for, not the intended production filename.

## What I deliberately did not do

- **Did not add tests.** The fixture has none, and the task asked for a refactor, not a test suite. AR007 is noted as a structural gap in `problems.md` so a follow-up commit can address it.
- **Did not introduce a dispatch registry.** No consumer exists. Speculative abstraction is exactly what the skill warns against: "premature abstraction is worse than duplication."
- **Did not preserve the old API as a compatibility shim.** The fixture has no external callers; the cost of shims is agent confusion (two names, one behavior) with no offsetting benefit.

## Linter expectations

Running `scripts/lint.py` on the refactored file should produce zero AR003/AR004/AR005/AR006 findings. AR001/AR002/AR008 were never at risk (file is ~70 lines, no duplication, no long strings). The filename-level AR003 finding ("utils"-family name) is addressed conceptually in the rationale above and would be resolved in a real codebase by renaming the file.
