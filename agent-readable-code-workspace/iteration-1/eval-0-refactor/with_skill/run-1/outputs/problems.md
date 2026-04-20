# Problems in `utils.py` (AI-maintainability perspective)

Source: `/Users/mikkelfreltoftkrogsholm/Projekter/dev-skills/agent-readable-code/scripts/fixtures/bad_py/utils.py`

The linter (`agent-readable-code/scripts/lint.py`) reports **14 findings** across **4 rules** (AR003, AR004, AR005, AR006). Below each finding is mapped to the concrete failure mode it induces in an AI coding agent (Claude Code, Cursor, Aider, Copilot, Devin).

## 1. Dumping-ground filename (`AR003`)

| # | Location | Problem |
|---|---|---|
| 1 | `utils.py` (filename) | `utils` is on the banlist. The file's purpose cannot be inferred from its name — agents cannot localize behavior by grepping meaningful paths, and any new symbol dumped here reinforces the pollution. |

**Failure mode:** When an agent needs to find "the code that charges customers" or "the user model," `utils.py` returns false positives or, worse, silently hides the real code because the agent does not think to look in a file called `utils`.

## 2. Generic symbol names (`AR003`)

| # | Line | Symbol | Problem |
|---|---|---|---|
| 2 | 9 | `process(data)` | Verb `process` on the banlist. No domain anchor — could mean anything. |
| 3 | 14 | `handle(x, y)` | Verb `handle` on the banlist. `x`, `y` are single-letter args. |
| 4 | 29 | `class Manager` | Noun `Manager` on the banlist. The only well-known "manager" symbol in a codebase is usually wrong. |
| 5 | 31 | `Manager.do_stuff(thing)` | `do_stuff` is the canonical placeholder; `thing` is untyped. |

**Failure mode (strong evidence, Liu et al. 2025):** Obfuscated names drop model comprehension from ~87% to ~59%. Misleading or generic names are worse than random ones because the agent builds a confidently wrong mental model and ships code against it.

## 3. Missing type annotations at public boundaries (`AR006`)

| # | Line | Signature | Problem |
|---|---|---|---|
| 6 | 9 | `def process(data):` | No param types, no return type. |
| 7 | 14 | `def handle(x, y):` | No param types, no return type. |
| 8 | 19 | `def run_expression(expr):` | No param types, no return type. |
| 9 | 24 | `def dynamic_import(name):` | No param types, no return type. |
| 10 | 31 | `def do_stuff(self, thing):` | No param types, no return type. |

**Failure mode:** Without types, agents fabricate call sites — e.g., calling `process({"user_id": 1})` when the real caller passes a list, or `.upper()` on what is actually an `int`. Type-constrained generation research (2025) shows annotations measurably reduce API-retrieval hallucination.

## 4. Metaprogramming / invisible dispatch (`AR004`)

| # | Line | Pattern | Problem |
|---|---|---|---|
| 11 | 20 | `eval(expr)` | Arbitrary string evaluation. Grep for `foo(` will never find calls that pass through `eval`. |
| 12 | 25 | `importlib.import_module(name)` | Dynamic import by string. No static import graph. |
| 13 | 59 | `DynamicAPI.__getattr__` | Every attribute access synthesizes a no-op lambda. No method a tool can jump to. |

**Failure mode:** Agents traverse codebases with grep + simple AST walks. Any call resolved at runtime through a string, a proxy, or `__getattr__` is invisible — so the agent either (a) hallucinates a method it thinks "must be there," or (b) breaks behavior by removing code it cannot see being used. Documented in the ETH SRI "Fixing Correct Code" postmortem and the 693-line Gemini spiral.

## 5. Deep inheritance chain (`AR005`)

| # | Line | Problem |
|---|---|---|
| 14 | 52 | `User -> Auditable -> Persisted -> Entity -> Base` (depth 4, limit 3). |

**Failure mode:** Agents fabricate method resolution paths. In the Surge HQ spiral, Gemini invented `super()` calls to nonexistent parents and then spent 39 turns patching the consequences. Each level added to a chain multiplies the surface area the agent must keep in its context.

## 6. Cross-cutting: the module has no feedback loop (`AR007`, implicit)

There is no colocated test file, no type checker config signal, and no single entrypoint a reader can use to verify a change. Combined with the generic names and untyped signatures, an agent editing this file has no way to tell whether its change broke anything until a human reviews it — the setup that produced the documented 693-line hallucination spiral.

## Summary

| Rule | Count | Severity for agents |
|---|---|---|
| AR003 (generic/dumping-ground names) | 5 | high — strong empirical evidence |
| AR004 (metaprogramming) | 3 | high — documented spiral triggers |
| AR005 (deep inheritance) | 1 | medium — review prompt |
| AR006 (untyped public boundaries) | 5 | high — seam hallucination |
| AR007 (no verification affordance) | implicit | high — compounds every other failure |

Net effect: the file is a worst-case miniature of every pattern the research literature flags as agent-hostile. An agent asked to change anything here would be forced to guess semantics from placeholder names, trace runtime behavior it cannot see, and ship without being able to verify the result.
