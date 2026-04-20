# Problems in `utils.py`

The file is a classic "dumping-ground" module: unrelated helpers, generic names,
runtime metaprogramming, and deep inheritance chains. For an AI agent trying to
navigate, modify, or extend the code, this creates ambiguity at every step.

## 1. Generic / meaningless module name (`utils.py`)

- "utils" tells an agent nothing about what lives in the file.
- There is no single responsibility, so future edits cannot be reliably routed
  here by name alone. Anything plausibly belongs, nothing specifically does.
- Related symbols (math helpers, dynamic dispatch, domain entities) are colocated
  only because they had no better home.

## 2. Generic function and method names

- `process(data)` — "process" how, into what? The name carries no intent.
- `handle(x, y)` — "handle" is a non-verb; the body is actually addition.
- `do_stuff(thing)` on `Manager` — maximally generic; an agent cannot predict
  behavior from the signature.

Generic names force agents to read the body before every call site, and they
collide easily during refactors ("which `process` did you mean?").

## 3. Missing type annotations on public API

- `process`, `handle`, `do_stuff`, `run_expression`, `dynamic_import`, and
  `DynamicAPI.__getattr__` have no parameter or return types.
- Without types, static analysis, IDE navigation, and agent reasoning all
  degrade to "read every caller and every return statement".

## 4. Runtime metaprogramming that defeats static analysis

- `eval(expr)` in `run_expression` — arbitrary code execution, unanalyzable,
  and a security hazard. An agent cannot reason about what the function returns
  or what side effects it may have.
- `importlib.import_module(name)` in `dynamic_import` — the imported module is
  only knowable at runtime, so symbol resolution, type checking, and
  dependency tracking all fail.
- `DynamicAPI.__getattr__` returns a no-op lambda for *any* attribute access.
  Every call site looks legal but does nothing; typos are silently swallowed.

## 5. Deep inheritance chain (`User -> Auditable -> Persisted -> Entity -> Base`)

- Five levels, each adding nothing (`pass`). The chain exists only to express
  tags that could be attributes, protocols, or composition.
- To understand `User`, an agent must open five files-worth of classes and
  confirm none of them override behavior. MRO surprises are a real risk if
  anyone ever adds a method.

## 6. No docstrings, no examples, no contracts

- None of the functions/classes document inputs, outputs, invariants, or
  failure modes. The only documentation is the module-level comment listing
  lint codes, which is metadata about the file, not about the code.

## 7. Mixed concerns in one module

- Arithmetic helper (`handle`)
- Identity passthrough (`process`, `Manager.do_stuff`)
- Dynamic code execution (`run_expression`, `dynamic_import`)
- Domain model hierarchy (`Base`..`User`)
- Dynamic proxy (`DynamicAPI`)

These do not belong together. Splitting them produces files whose names
themselves communicate purpose.
