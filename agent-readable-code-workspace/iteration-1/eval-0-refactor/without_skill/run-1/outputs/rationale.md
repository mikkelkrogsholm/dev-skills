# Rationale: why each change matters for AI agents

Each change is tied to a concrete failure mode observed when LLM-based coding agents edit code like the original.

## Filename / module purpose

**Change:** The module is now the "User account domain model and safe expression/import helpers" — a single named concern, with `__all__` declaring the public surface. In a real refactor this file would be renamed (e.g. `user.py` plus `safe_exec.py`); here we keep `refactored.py` as required but the module docstring pins the concern.

**Failure mode avoided:** With a file called `utils.py`, an agent asked "add a new user field" will often create a second `user.py` elsewhere or dump the field into an unrelated `utils.py`. Cohesive, named modules stop that drift.

## Renamed functions with concrete verbs + nouns

- `process` → `normalize_user_payload`
- `handle` → `add_integers`
- `do_stuff` → removed; its work is `User.rename` / `User.deactivate` / `User.touch`
- `run_expression` → `safe_eval_arithmetic`
- `dynamic_import` → `load_allowed_module`

**Failure mode avoided:** Agents pattern-match on names. A function called `process` is a magnet for unrelated logic — over successive edits, agents will pile type-checks, I/O, and validation into it because "process" accepts anything. A function called `normalize_user_payload` resists that: when a new concern arrives, the agent is nudged to put it somewhere else.

## Full type annotations everywhere

**Failure mode avoided:** Without types, an agent generating a call site has to guess the shape of `data`, `thing`, `x`. Guesses are locally plausible but globally inconsistent (e.g., one caller passes a dict, another a list, nothing complains until runtime). Types turn "what does this take?" from an inference problem into a lookup.

## Docstrings that state intent, raises, and returns

**Failure mode avoided:** Agents use docstrings as the canonical description of behaviour when generating tests or call sites. Missing docstrings force the agent to infer intent from the body — which is circular when the agent is the one writing the body.

## `eval(expr)` → `safe_eval_arithmetic` (AST walker with allow-list)

**Failure mode avoided:**
1. Security: an agent wiring a config value or HTTP field to `eval` creates RCE. It happens.
2. Static analysability: `eval` hides the reachable code from every static tool the agent might use (grep, type checker, import graph). The AST walker makes the set of legal inputs fully enumerable — an agent can answer "can this expression do I/O?" by reading 20 lines.

## `importlib.import_module(name)` → `load_allowed_module(name)` with a frozenset allow-list

**Failure mode avoided:** Dynamic imports defeat rename refactors ("rename module X to Y" misses string-based imports) and defeat agent reasoning about what plugins exist. An explicit `_ALLOWED_PLUGIN_MODULES` set is a grep target. To add a plugin the agent must edit the set, which is a reviewable diff.

## Removed `DynamicAPI.__getattr__` entirely

**Failure mode avoided:** `__getattr__` returning a no-op lambda means `api.anything_at_all(...)` "works". An agent writing tests against such an API will produce passing tests for non-existent methods — the worst possible signal. Explicit methods on `User` make typos fail loudly.

## Collapsed `Base -> Entity -> Persisted -> Auditable -> User` into a single `User` dataclass

**Failure mode avoided:**
1. Context cost: to answer "what fields does `User` have?" an agent had to walk five classes and find nothing. Flat class, visible fields.
2. Wrong-level edits: with empty intermediates, agents guess where to put new behaviour (e.g., put `touch()` on `Auditable` or on `User`?). When the hierarchy is empty, the guess is arbitrary; future agents guess differently, and behaviour scatters.
3. The concerns the chain *named* (identity, persistence, audit) are preserved as fields (`id`, `created_at`, `updated_at`) and methods (`touch`), so nothing is lost — it is just visible.

## `@dataclass(slots=True)` with defaults

**Failure mode avoided:** Hand-rolled `__init__` is a common source of agent-introduced bugs (forgetting `self.foo = foo`, mis-ordering args). A dataclass is declarative and gives the agent one, enforced, typed constructor. `slots=True` also prevents a subtle failure where an agent "adds a field" by setting `user.new_attr = ...` at a call site instead of editing the class — with slots that raises immediately.

## Explicit `__all__`

**Failure mode avoided:** Without it, every helper looks equally public. Agents import internal helpers from across the codebase, and "refactor this internal function" becomes a breaking change. `__all__` pins the contract.

## Input validation that raises named exceptions

**Failure mode avoided:** The original `process(data)` returned input unchanged; `DynamicAPI` returned `None` for everything. Silent success is the hardest failure mode for agents to debug — there is nothing to grep for. `ValueError` / `TypeError` with a message that names the offending input gives future agents (and logs) a concrete string to trace.

---

Each of these is cheap in isolation. The point is that the *combination* is what lets an AI agent modify this file six months from now without drifting — every question the agent might ask ("what does this take?", "what does it do?", "where do I put a new field?", "what imports are allowed?") has a local, textual answer.
