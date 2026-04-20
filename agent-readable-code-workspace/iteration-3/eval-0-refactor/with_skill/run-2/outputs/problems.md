# Problems in `utils.py`

The file is a textbook anti-pattern for agent-readability. Issues are grouped by the `agent-readable-code` rule they violate.

## AR003 — Naming and file organization

1. **Dumping-ground filename.** `utils.py` is explicitly banlisted. An agent grepping for behavior cannot predict what lives here; all "miscellaneous" code eventually lands in the file and grows unbounded.
2. **Generic function `process(data)`.** No domain signal. The name does not tell the agent what is processed, what is returned, or when to call it.
3. **Generic function `handle(x, y)`.** `handle` is banlisted, `x`/`y` are single-letter parameters outside a tight loop. Cannot be grepped for intent.
4. **Generic class `Manager`.** `Manager` is banlisted. Reveals nothing about responsibility.
5. **Generic method `Manager.do_stuff(thing)`.** `do_stuff` is explicitly banlisted and `thing` is an unnamed parameter.

## AR004 — Static, explicit dependencies

6. **`eval(expr)` in `run_expression`.** Dynamic code execution cannot be traced by grep or AST walk. An agent reading callers cannot know what functions `expr` references.
7. **`importlib.import_module(name)` in `dynamic_import`.** String-keyed dispatch across the import graph. Agents cannot follow the reference chain.
8. **`DynamicAPI.__getattr__` dispatch.** Attribute access returns an ad-hoc lambda. No static signal for what methods exist; every `api.something(...)` call silently succeeds at runtime and silently no-ops.

## AR005 — Deep inheritance

9. **Five-level chain `User -> Auditable -> Persisted -> Entity -> Base`.** Depth > 3. Agents fabricate method resolution order and invent methods that do not exist on any class in the chain. None of the intermediate classes actually add behavior, so the chain is also pure ceremony.

## AR006 — Missing types at public boundaries

10. **`process(data)` has no annotations.** Public signature is untyped; the agent cannot infer input or return shape without reading callers.
11. **`handle(x, y)` has no annotations.** Same issue; `+` could mean numeric addition, string concatenation, list extension — all equally plausible.
12. **`Manager.do_stuff(self, thing)` has no annotations.** Public method with no typed boundary.
13. **`run_expression` / `dynamic_import` have no annotations.** Public API with untyped return.

## Language-specific (Python section of the skill)

14. **No `__all__`.** Any consumer doing `from utils import *` pulls in `importlib`, `Base`, `Entity`, `Persisted`, `Auditable`, and the dispatch lambdas — coupling an agent never intended.
15. **Module docstring describes violations, not the module's purpose.** A stale/misleading docstring is worse than none (AR006 principle).

## Structural

16. **No tests, no verification affordance.** An agent editing these functions has no feedback loop (AR007-adjacent, at the repo level).
17. **No side-effect injection.** `eval` and `import_module` reach into globals; there is no way for a test to sandbox them.

## Summary of what must change

- Delete or inline the `Manager` / `DynamicAPI` / `Base..User` ceremony that carries no behavior.
- Rename functions to domain verbs, add type annotations, and split the file by domain (the fixture is tiny, so a single well-named module suffices — but the filename `utils.py` must go).
- Replace `eval` and `importlib.import_module` with explicit registries if dispatch is genuinely needed, or delete them if the fixture only exists to illustrate the anti-pattern.
