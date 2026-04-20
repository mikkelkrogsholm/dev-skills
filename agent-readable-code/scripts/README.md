# Agent-readable-code linter

Zero-dependency Python script that flags code patterns known to cause AI coding agents to fail.

## Usage

```bash
python scripts/lint.py <path>                         # full report
python scripts/lint.py <path> --json                  # JSON output
python scripts/lint.py <path> --quiet                 # summary only
python scripts/lint.py <path> --rules AR001,AR003     # subset
python scripts/lint.py <path> --config custom.yaml    # override thresholds
python scripts/lint.py <path> --max 10                # exit nonzero if >10 findings
```

## Rules

| ID | What it flags | Languages | Evidence |
|---|---|---|---|
| `AR001` | Files > 800 lines | all | heuristic |
| `AR002` | Near-duplicate 6-line blocks (coalesced into ranges) | all | moderate |
| `AR003` | Generic class/function/method names (exact `Manager` + suffix `OrderManager`, `UserService`) and dumping-ground filenames (`utils.py`, `helpers.ts`...) | all | strong |
| `AR004` | Metaprogramming hotspots (`__getattr__`, `eval`, `Proxy`, `Reflect`, dynamic `type()` class construction…) | all | moderate |
| `AR005` | Class inheritance depth > 3 — review prompt, not a hard rule | Python (via ast) + TS/JS (regex, single-inheritance chain within a file) | heuristic |
| `AR006` | Public function without type annotations (Python: params + return; TS: params only — return inference is idiomatic) | Python (via ast) + TS only (regex on exported functions and arrow-const exports; `.js`/`.mjs`/`.cjs` skipped — no type system) | strong |
| `AR007` | Tests scattered in `tests/` dirs instead of colocated | all | moderate |
| `AR008` | Lines longer than 400 chars (minified files, monster string literals) | all | heuristic |
| `AR011` | Barrel re-export files (>70% of content is `export * from` / `from X import *`) | all | moderate |

Evidence strength: **strong** = controlled empirical study or first-hand vendor postmortem. **moderate** = case studies + vendor guidance. **heuristic** = directionally right, threshold is tunable. Full citations in `../references/research.md`.

## Suppressions

Suppress per-line with a trailing or preceding comment:

```python
class OrderManager:  # agent-lint: disable=AR003
    ...

# agent-lint: disable=AR004
def use_eval(s):
    return eval(s)
```

```ts
// agent-lint: disable=AR003
export class OrderManager {}
```

Suppress for an entire file with a header directive (anywhere in the file):

```python
# agent-lint: disable-file=AR001,AR004
```

Omit the `=RULE_IDS` part to suppress *all* rules on that line or file. Multiple rules are comma-separated.

## Adoption path

Don't enable all rules as hard errors on day one. Recommended rollout:

1. **Warnings only, advisory.** Run `python scripts/lint.py src/` locally; skim the output.
2. **Hard-enforce the `heuristic` rules first** — they have the lowest false-positive rate and catch the highest-impact breakage: `--rules AR001,AR002,AR008 --max 0` in CI.
3. **Add `AR003` as a warning.** Suppress framework-mandated names (see "When NOT to apply this skill" in `../SKILL.md`). Once suppressions are in place, promote to error.
4. **Consider `AR004`, `AR005`, `AR006`, `AR007` case-by-case.** These are more context-dependent; some codebases will have many legitimate exceptions.

This staged approach is why the linter ships with per-rule `--rules` filtering and inline suppressions: adoption fails when every finding is a hard block.

## Configuration

The linter has sensible defaults. To override, pass `--config path/to/config.yaml`:

```yaml
file_size_lines: 600
long_line_chars: 500
duplicate_min_lines: 8
max_inheritance_depth: 2

banlist_names: [Manager, Service, Helper, Handler]
banlist_functions: [process, handle]
banlist_filenames: [utils, helpers, misc, common]

ignore_dirs: [.git, node_modules, dist, build, .venv, __pycache__]
```

See `config.example.yaml` for the full schema.

## Output

Default text format:

```
src/services/orderManager.ts
  AR001 [line 1247] file is 1247 lines (threshold: 800)
       why: apply-model merges fail; mid-file content ignored
  AR003 [line 1] class name 'OrderManager' is generic; name by what it does
       why: pollutes grep; agents pick wrong symbol

3 findings across 2 files (AR001=1, AR003=2)
see references/research.md for the rationale behind each rule
```

JSON format:

```json
[
  {
    "rule": "AR001",
    "file": "src/services/orderManager.ts",
    "line": 1247,
    "message": "file is 1247 lines (threshold: 800)",
    "why": "apply-model merges fail; mid-file content ignored",
    "title": "file too large"
  }
]
```

## CI integration

Most findings are advisory. A conservative CI setup:

```bash
# Hard errors — definitely breaking for agents
python scripts/lint.py src/ --rules AR001,AR002,AR008 --max 0

# Soft warnings — print but don't fail
python scripts/lint.py src/ --rules AR003,AR004,AR005,AR006,AR007
```

## Tests

The linter ships with a falsifiability harness:

```bash
python tests/run_tests.py              # assert fixtures produce expected findings
python tests/run_tests.py --verbose    # show every finding per fixture
```

Every documented example has a fixture; every fixture has an asserted expected output. If the documented behavior drifts from the actual behavior, the tests fail.

## Limitations

- `AR005` and `AR006` support Python (via stdlib `ast`) and TypeScript (via regex — fast, zero-dep, good for common idioms but not a full parser). TS class-method AR006 and cross-file inheritance chains are not yet covered; flagged at declaration site only. For exotic TS (decorator metadata, conditional types, mapped types) the regex may under-report; it errs on the side of false negatives over false positives.
- `AR002` uses exact-match hashing on normalized lines. It catches copy-paste duplicates well; it does not detect *near*-duplicates that differ semantically.
- `AR003` class detection uses exact + suffix matching against a banlist (`OrderManager` fires, `ServiceWorker` does not). Prefix-only matches (`ServiceWorker`) are intentionally excluded to avoid noise on legitimate compound nouns.
- `AR004` uses regex heuristics and can occasionally flag legitimate uses (e.g., intentional proxies in library code). Use inline/file suppressions.
- `AR007` is a repo-wide heuristic; it can over-trigger on monorepos with separate test packages. Consider disabling in those contexts.
- `AR009` (circular imports) and `AR010` (stale TODOs via git blame) are deferred to v2.
- Baseline mode (`--baseline baseline.json` to accept existing debt while preventing new debt) is deferred to v1.2.
- SARIF output for GitHub code-scanning is deferred to v1.2.
