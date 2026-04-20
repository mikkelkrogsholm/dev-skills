# Problems in `bad_py/utils.py`

Linter output: 14 findings (AR003=5, AR004=3, AR005=1, AR006=5). Below groups them by rule and adds the maintainability implications the linter cannot surface.

## 1. Dumping-ground filename (`AR003`, strong evidence)

- The file is literally named `utils.py`. `utils` is on the banlist for a reason: it is a grep sinkhole. A query for "where do we do X" returns every `utils.py` in the tree, and the agent has no retrieval cue telling it which file owns which behavior.
- The module docstring reinforces the problem ("Dumping-ground module"). Nothing in the name tells a future agent what domain this module serves.

## 2. Generic / banlist names (`AR003`, strong evidence)

- `process(data)` — `process` is the canonical banlist verb. It says the function does something to something. That is not a retrieval cue; it is a retrieval anti-cue.
- `handle(x, y)` — same class of problem. Plus `x, y` give no hint about the domain.
- `class Manager` — banlist class name. `Manager` is interchangeable with `Service`, `Handler`, `Helper`.
- `Manager.do_stuff(self, thing)` — `do_stuff` is verbatim on the banlist. `thing` is the parameter equivalent.
- Controlled studies show naming drives comprehension accuracy from ~87% to ~59%. Misleading names are worse than random ones because the agent *confidently* acts on the wrong model.

## 3. Metaprogramming / invisible control flow (`AR004`, moderate evidence)

- `eval(expr)` — arbitrary code the agent cannot trace by grep or AST. Also a security hole, but the agent-readability problem is that call sites of `run_expression(...)` tell the agent nothing about what actually runs.
- `importlib.import_module(name)` — dynamic import keyed on a runtime string. Static code graphs (Aider's repo-map, Cursor's embeddings) do not follow this. An agent asked "where is module X imported?" will miss this file.
- `DynamicAPI.__getattr__` — the class has no discoverable surface. `api.anything_at_all(**kw)` silently succeeds. An agent will invent method names that don't exist and write tests that pass against a proxy that accepts everything.

## 4. Missing type annotations at the public boundary (`AR006`, strong evidence)

Every top-level function and the public method are untyped:

- `process(data)` — no param type, no return type.
- `handle(x, y)` — no param types, no return type.
- `run_expression(expr)` — no param type, no return type.
- `dynamic_import(name)` — no param type, no return type.
- `Manager.do_stuff(self, thing)` — no param type, no return type.

Typed boundaries measurably reduce hallucination at module seams. Untyped public signatures give the agent nothing to anchor against, so it fabricates call shapes.

## 5. Deep inheritance chain (`AR005`, heuristic)

- `User -> Auditable -> Persisted -> Entity -> Base` is 4 levels deep. The linter's threshold is 3, and the direction is well-motivated: agents fabricate `super()` calls and invent method resolution orders that don't exist (Surge HQ 693-line spiral case study). None of these intermediate classes carry any behavior — the hierarchy is pure ceremony.

## 6. Structural / module-level problems (not individually flagged)

- **No `__all__`.** Python's one signal for "import this, not that." Without it, an agent will import `Base` or `Persisted` from this module and create coupling you did not intend.
- **Stateless "marker" base classes.** `Base`, `Entity`, `Persisted`, `Auditable` carry no methods or fields. They exist only to justify the inheritance tree. Agents will try to call inherited methods that were never defined.
- **No behavior, no tests, no verification affordance** (`AR007` spirit). Every function is either a pass-through, an unsafe eval, or an identity. There is nothing an agent can run to confirm its edits are correct.
- **Wrong oracle docstring.** The module docstring describes what is *wrong* with the file, not what the file does. A future agent reading it will be more confused, not less. Incorrect docstrings are empirically worse than missing ones.
- **Dataclass-shaped data modeled as empty classes.** `User` should be a frozen dataclass with fields, not a subclass with no attributes.

## Summary of failure modes this file will cause

1. Agent greps for a domain concept, lands on `utils.py`, picks `process` or `Manager`, and attaches wrong behavior to the wrong seam.
2. Agent edits a caller of `run_expression` or `dynamic_import`, cannot trace what actually runs, guesses, ships a silent bug.
3. Agent writes `api.some_method(...)` against `DynamicAPI`, test passes because `__getattr__` returns a no-op, production fails.
4. Agent adds a method to `User`, calls `super().<method>()`, invents a parent that does not exist.
5. Agent changes a call signature, runtime tolerates it because there are no type annotations, the caller breaks three edits later.
