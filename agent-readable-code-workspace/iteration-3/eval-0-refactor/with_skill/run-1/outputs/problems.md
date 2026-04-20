# Problems in `bad_py/utils.py`

Audit against the six practices in `agent-readable-code/SKILL.md`. Rule codes map to the linter (`scripts/lint.py`).

## 1. Dumping-ground filename (`AR003`)

`utils.py` is on the banlist. It tells the agent nothing about domain, so anything can be dropped here and nothing can be located by grep on a domain term. An agent asked "where is the user auditing logic?" cannot find it by name.

## 2. Generic function and method names (`AR003`)

- `process(data)` — does not say what is processed or what happens.
- `handle(x, y)` — neither the action nor the operands are named.
- `run_expression(expr)` — "run" is a filler verb; the real hazard (arbitrary code execution) is hidden.
- `dynamic_import(name)` — "dynamic" is about the mechanism, not the intent.
- `Manager` — on the banlist; manages nothing specific.
- `Manager.do_stuff(self, thing)` — textbook banlist name; pure noise.

Misleading/empty names drop comprehension from ~87% to ~59% in controlled studies and are worse than random ones because the agent acts confidently on the wrong mental model.

## 3. Missing type annotations at the public boundary (`AR006`)

Every public function and method here is untyped: `process`, `handle`, `run_expression`, `dynamic_import`, `Manager.do_stuff`, `DynamicAPI.__getattr__`. Without typed signatures the agent has no anchor against fabrication at the module seam.

## 4. Metaprogramming the agent cannot trace (`AR004`)

- `eval(expr)` in `run_expression` — dynamic code execution; also a security hazard.
- `importlib.import_module(name)` in `dynamic_import` — module graph is invisible to grep and AST walkers.
- `DynamicAPI.__getattr__` returns a generic lambda for any attribute name. Callers like `api.refund_payment(...)` are invisible to grep; the agent either invents a definition or rewrites the call in a way the dispatcher cannot handle.

## 5. Deep inheritance chain (`AR005`)

`User -> Auditable -> Persisted -> Entity -> Base` is 4 levels deep (threshold is typically 3). Agents fabricate MRO-dependent signatures on chains they cannot hold in context. The classes are also empty — the chain expresses no behavior, only taxonomy.

## 6. No module surface declaration (Python idiom from Practice 8)

There is no `__all__`. Agents importing from this file will import private helpers and tighten coupling the author did not intend.

## 7. No verification affordances (`AR007`)

There are no colocated tests. Even if the functions were well-named, an agent modifying this file has no local feedback loop.

## 8. Missing `__all__`, `slots=True`, `frozen=True` opportunities

The empty data-model classes are prime candidates for frozen dataclasses with slots. As written, an agent assigning `user.foo = bar` silently succeeds and introduces a latent bug rather than failing loudly.

## Summary of triggered lint rules

| Rule | Reason |
| --- | --- |
| `AR003` | Dumping-ground filename, generic names on `process`, `handle`, `Manager`, `do_stuff` |
| `AR004` | `eval`, `importlib.import_module`, `__getattr__` dynamic dispatch |
| `AR005` | 4-level inheritance chain ending at `User` |
| `AR006` | Public functions/methods without type annotations |
| `AR007` | No colocated tests |
