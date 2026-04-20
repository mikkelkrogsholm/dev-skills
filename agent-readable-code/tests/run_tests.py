#!/usr/bin/env python3
"""Falsifiability harness for the agent-readable-code linter.

Runs the linter against the bundled fixtures and asserts that documented behavior matches
actual behavior. Fails loudly if a rule drops a case it's supposed to catch or starts
flagging a case it's supposed to ignore.

Usage:
    python tests/run_tests.py              # run all
    python tests/run_tests.py --verbose    # show all findings per fixture
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
LINT = REPO / "scripts" / "lint.py"
FIX = REPO / "scripts" / "fixtures"


# For each fixture, the exact rule-count expectation.
# Keep these tight — a drift is either a real bug or an intentional change that
# deserves a test update.
EXPECTATIONS: dict[str, dict[str, int]] = {
    "bad_py/utils.py": {
        "AR003": 5,   # utils filename + process + handle + Manager class + do_stuff method
        "AR004": 3,   # eval, importlib.import_module, __getattr__
        "AR005": 1,   # User depth=4
        "AR006": 5,   # process, handle, run_expression, dynamic_import, Manager.do_stuff
    },
    "bad_py/untyped.py": {
        # AR006 on every public function (not __init__)
        # positional_only, with_varargs, returns_but_untyped_param, typed_but_no_return, Billing.__init__, Billing.charge
        "AR006": 6,
    },
    "bad_ts/orderManager.ts": {
        "AR003": 6,   # Manager, OrderManager(suffix), PaymentService(suffix), doStuff, process method, handle method
        "AR004": 2,   # Reflect., new Proxy
        "AR008": 1,   # long MINIFIED string
    },
    "bad_ts/orders.ts": {
        "AR002": 1,   # duplicates refunds.ts
    },
    "bad_ts/refunds.ts": {
        # orders.ts is reported as primary; refunds.ts is reported as peer only.
    },
    "bad_ts/huge.ts": {
        "AR001": 1,
    },
    "bad_ts/generated.min.js": {
        "AR008": 1,   # single file-level finding (not per-line)
    },
    "bad_ts/barrel.ts": {
        "AR011": 1,   # barrel-only re-exports
    },
    "good_py/refunds.py": {
        # clean
    },
    "good_py/suppressed.py": {
        # all findings suppressed via pragmas
    },
}


# Specific must-not-flag cases. These are regression guards.
NEGATIVE_CASES: list[tuple[str, str, str]] = [
    # (fixture_substring, rule, reason)
    ("orderManager.ts:ServiceWorker", "AR003",
        "ServiceWorker is a prefix-match, should not trigger — suffix-only matching"),
    ("suppressed.py:OrderManager", "AR003",
        "class OrderManager has inline # agent-lint: disable=AR003"),
    ("suppressed.py:use_eval", "AR004",
        "file has # agent-lint: disable-file=AR004"),
]


def run_lint_json(target: Path) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(LINT), str(target), "--json"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"linter crashed on {target}:\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return json.loads(result.stdout)


def rule_counts(findings: list[dict]) -> dict[str, int]:
    c: dict[str, int] = collections.Counter()
    for f in findings:
        c[f["rule"]] += 1
    return dict(c)


def test_expectations(verbose: bool = False) -> list[str]:
    """Lint each top-level fixture dir once; attribute findings by file.
    This ensures cross-file rules like AR002 can find their duplicates."""
    failures = []
    # group fixtures by top-level dir
    per_dir: dict[str, list[str]] = {}
    for rel in EXPECTATIONS:
        top = rel.split("/", 1)[0]
        per_dir.setdefault(top, []).append(rel)

    findings_by_file: dict[str, list[dict]] = {}
    for top in per_dir:
        dir_path = FIX / top
        if not dir_path.exists():
            failures.append(f"FIXTURE DIR MISSING: {top}")
            continue
        all_findings = run_lint_json(dir_path)
        for f in all_findings:
            rel = str(Path(f["file"]).relative_to(FIX))
            findings_by_file.setdefault(rel, []).append(f)

    for rel, expected in EXPECTATIONS.items():
        findings = findings_by_file.get(rel, [])
        actual = rule_counts(findings)
        if verbose:
            print(f"\n{rel}: findings={actual}")
            for f in findings:
                print(f"  {f['rule']} line {f['line']}: {f['message']}")
        for rule, want in expected.items():
            got = actual.get(rule, 0)
            if got != want:
                failures.append(f"{rel}: expected {rule}={want}, got {rule}={got}")
        if not expected:
            if actual:
                failures.append(f"{rel}: expected no findings, got {actual}")
        else:
            extra = set(actual) - set(expected)
            for rule in extra:
                failures.append(f"{rel}: unexpected rule {rule}={actual[rule]}")
    return failures


def test_negative_cases(verbose: bool = False) -> list[str]:
    """Run linter on specific fixtures and verify certain symbols never appear in findings."""
    failures = []
    # group by fixture file
    by_file: dict[str, list[tuple[str, str, str]]] = {}
    for spec, rule, reason in NEGATIVE_CASES:
        fixture_name, _, needle = spec.partition(":")
        by_file.setdefault(fixture_name, []).append((needle, rule, reason))

    for fixture_name, cases in by_file.items():
        matches = list(FIX.rglob(fixture_name))
        if not matches:
            failures.append(f"NEGATIVE FIXTURE MISSING: {fixture_name}")
            continue
        path = matches[0]
        findings = run_lint_json(path)
        for needle, rule, reason in cases:
            hit = [f for f in findings if f["rule"] == rule and needle in f["message"]]
            if hit:
                failures.append(
                    f"{fixture_name}: {rule} incorrectly flagged '{needle}' "
                    f"— should be suppressed ({reason}). Got: {hit[0]['message']}"
                )
    return failures


def test_json_schema(verbose: bool = False) -> list[str]:
    """Every JSON finding has the expected fields including evidence level."""
    failures = []
    findings = run_lint_json(FIX / "bad_py" / "utils.py")
    required = {"rule", "file", "line", "message", "why", "title", "evidence", "fix"}
    for f in findings:
        missing = required - set(f)
        if missing:
            failures.append(f"JSON schema: finding missing fields {missing}: {f}")
            break
        if f["evidence"] not in ("strong", "moderate", "heuristic"):
            failures.append(f"JSON schema: invalid evidence level '{f['evidence']}' for {f['rule']}")
            break
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print(f"linter: {LINT}")
    print(f"fixtures: {FIX}")
    print()

    all_failures: list[str] = []

    print("==> expectations (count per rule per fixture)")
    fails = test_expectations(args.verbose)
    print(f"    {'PASS' if not fails else f'FAIL ({len(fails)})'}")
    all_failures.extend(fails)

    print("==> negative cases (must-not-flag)")
    fails = test_negative_cases(args.verbose)
    print(f"    {'PASS' if not fails else f'FAIL ({len(fails)})'}")
    all_failures.extend(fails)

    print("==> JSON schema")
    fails = test_json_schema(args.verbose)
    print(f"    {'PASS' if not fails else f'FAIL ({len(fails)})'}")
    all_failures.extend(fails)

    print()
    if all_failures:
        print(f"FAILURES ({len(all_failures)}):")
        for f in all_failures:
            print(f"  - {f}")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
