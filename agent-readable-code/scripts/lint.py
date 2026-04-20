#!/usr/bin/env python3
# agent-lint: disable-file=AR001
"""
agent-readable-code linter.

Flags code patterns that cause AI coding agents to fail or hallucinate.
Zero dependencies — stdlib only.

Usage:
    python scripts/lint.py <path>
    python scripts/lint.py <path> --json
    python scripts/lint.py <path> --rules AR001,AR003
    python scripts/lint.py <path> --config custom.yaml
    python scripts/lint.py <path> --quiet      # summary line only
    python scripts/lint.py <path> --max=N      # exit nonzero if more than N findings

Rules: see scripts/README.md for the full table.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable


DEFAULT_CONFIG = {
    "file_size_lines": 800,
    "long_line_chars": 400,
    "duplicate_min_lines": 6,
    "max_inheritance_depth": 3,
    "banlist_names": [
        "Manager",
        "Service",
        "Helper",
        "Handler",
        "Util",
        "Utils",
        "Processor",
        "Wrapper",
    ],
    "banlist_functions": [
        "process",
        "handle",
        "doStuff",
        "do_stuff",
        "doWork",
        "run",
        "execute",
    ],
    "banlist_filenames": [
        "utils",
        "util",
        "helpers",
        "helper",
        "misc",
        "common",
        "stuff",
        "lib",
    ],
    "metaprog_python": [
        r"\b__getattr__\b",
        r"\bexec\s*\(",
        r"\beval\s*\(",
        r"\bimportlib\.import_module\b",
        r"\bsetattr\s*\(",
        r"\btype\s*\(\s*['\"][A-Za-z_]\w*['\"]\s*,",
    ],
    "metaprog_js": [
        r"\bnew\s+Proxy\s*\(",
        r"\bReflect\.",
        r"\beval\s*\(",
        r"\bFunction\s*\(\s*['\"]",
        r"\bObject\.defineProperty\s*\(",
    ],
    "ignore_dirs": [
        ".git",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
        "__pycache__",
        ".next",
        ".turbo",
        "coverage",
        ".pytest_cache",
    ],
    "python_extensions": [".py"],
    "js_extensions": [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"],
}


# evidence: "strong" = backed by empirical study or first-hand vendor postmortem.
#           "moderate" = case studies + vendor guidance + mechanistic reasoning.
#           "heuristic" = operational threshold; directionally right, number is tunable.
# 4-tuple: (title, why, evidence, fix_hint)
RULE_INFO = {
    "AR001": (
        "file too large",
        "apply-model merges fail; mid-file content ignored",
        "heuristic",
        "split by feature/responsibility; colocate what changes together",
    ),
    "AR002": (
        "near-duplicate block",
        "breaks exact-match str_replace edits",
        "moderate",
        "extract shared logic into a helper at the seam, not per call site",
    ),
    "AR003": (
        "generic name",
        "pollutes grep; agents pick wrong symbol",
        "strong",
        "rename to a concrete domain verb/object (e.g. 'issueRefund' instead of 'process')",
    ),
    "AR004": (
        "metaprogramming hotspot",
        "invisible to grep/AST; agents hallucinate",
        "moderate",
        "replace runtime dispatch with an explicit typed wrapper",
    ),
    "AR005": (
        "deep inheritance",
        "harder-to-trace behavior hierarchy — review manually",
        "heuristic",
        "flatten via composition; collaborators as fields beat method resolution puzzles",
    ),
    "AR006": (
        "untyped public boundary",
        "fuels hallucination at module seams",
        "strong",
        "add type annotations to parameters and return value",
    ),
    "AR007": (
        "scattered tests",
        "no in-loop verification — spiral risk",
        "moderate",
        "colocate tests next to source (foo.ts + foo.test.ts) so agents find them",
    ),
    "AR008": (
        "very long line",
        "breaks ReAct tool output; burns context",
        "heuristic",
        "wrap the literal; move minified/generated files to dist/ or .gitignore",
    ),
    "AR011": (
        "barrel re-export file",
        "adds a grep hop; hides defining file; breaks tree-shaking",
        "moderate",
        "import from the defining file; delete the barrel (keep only where tool requires it, e.g. Drizzle schema index)",
    ),
}


@dataclass
class Finding:
    rule: str
    file: str
    line: int
    message: str
    why: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        info = RULE_INFO[self.rule]
        d["title"] = info[0]
        d["evidence"] = info[2]
        d["fix"] = info[3]
        return d


@dataclass
class Config:
    data: dict = field(default_factory=lambda: dict(DEFAULT_CONFIG))

    def __getattr__(self, name: str):  # agent-lint: disable=AR004
        if name == "data":
            raise AttributeError(name)
        try:
            return self.data[name]
        except KeyError as e:
            raise AttributeError(name) from e


# ---------- File discovery ----------


def iter_source_files(root: Path, cfg: Config) -> Iterable[Path]:
    ignore = set(cfg.ignore_dirs)
    exts = set(cfg.python_extensions) | set(cfg.js_extensions)
    if root.is_file():
        if root.suffix in exts:
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore and not d.startswith(".") or d in {".claude", ".github"}]
        # re-filter with ignore_dirs explicitly
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in exts:
                yield p


def is_python(p: Path, cfg: Config) -> bool:
    return p.suffix in cfg.python_extensions


def is_js(p: Path, cfg: Config) -> bool:
    return p.suffix in cfg.js_extensions


# ---------- Rules ----------


def check_ar001_file_size(path: Path, lines: list[str], cfg: Config) -> list[Finding]:
    if len(lines) > cfg.file_size_lines:
        return [
            Finding(
                "AR001",
                str(path),
                len(lines),
                f"file is {len(lines)} lines (threshold: {cfg.file_size_lines})",
                RULE_INFO["AR001"][1],
            )
        ]
    return []


def check_ar008_long_lines(path: Path, lines: list[str], cfg: Config) -> list[Finding]:
    limit = cfg.long_line_chars
    nonempty = [ln for ln in lines if ln.strip()]
    long_count = sum(1 for ln in lines if len(ln) > limit)

    # Generated/minified-file heuristic: majority of non-empty lines exceed the limit.
    # Emit ONE file-level finding instead of a noisy per-line list.
    if nonempty and long_count / len(nonempty) > 0.5:
        return [
            Finding(
                "AR008",
                str(path),
                1,
                f"file appears generated/minified — {long_count}/{len(nonempty)} lines exceed {limit} chars",
                RULE_INFO["AR008"][1],
            )
        ]

    findings = []
    for i, line in enumerate(lines, start=1):
        if len(line) > limit:
            findings.append(
                Finding(
                    "AR008",
                    str(path),
                    i,
                    f"line is {len(line)} chars (threshold: {limit}); minified or overlong literal?",
                    RULE_INFO["AR008"][1],
                )
            )
            if len(findings) >= 3:
                break
    return findings


def check_ar003_filename(path: Path, cfg: Config) -> list[Finding]:
    stem = path.stem.lower()
    if stem in set(cfg.banlist_filenames):
        return [
            Finding(
                "AR003",
                str(path),
                1,
                f"file name '{path.name}' is a dumping-ground name; split by feature/domain",
                RULE_INFO["AR003"][1],
            )
        ]
    return []


_PY_CLASS_RE = re.compile(r"^[ \t]*class[ \t]+([A-Za-z_]\w*)[ \t]*[\(:]", re.MULTILINE)
_PY_FUNC_RE = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+([A-Za-z_]\w*)[ \t]*\(", re.MULTILINE)
_JS_CLASS_RE = re.compile(r"^[ \t]*(?:export[ \t]+(?:default[ \t]+)?)?(?:abstract[ \t]+)?class[ \t]+([A-Za-z_]\w*)", re.MULTILINE)
_JS_FUNC_RE = re.compile(
    r"^[ \t]*(?:export[ \t]+(?:default[ \t]+)?)?"
    r"(?:function[ \t]+([A-Za-z_]\w*)[ \t]*\(|"
    r"(?:const|let|var)[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*(?:async[ \t]*)?\(.*?\)[ \t]*=>|"
    r"(?:const|let|var)[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*function)",
    re.MULTILINE,
)
# JS/TS class methods: a line starting with optional modifiers, then name(...), then { on same or next line.
# Not perfect (can match object-literal shorthand), but restricted to banlist names so noise is low.
_JS_METHOD_RE = re.compile(
    r"^[ \t]+(?:public[ \t]+|private[ \t]+|protected[ \t]+|static[ \t]+|async[ \t]+|readonly[ \t]+|override[ \t]+|get[ \t]+|set[ \t]+)*"
    r"([A-Za-z_]\w*)[ \t]*\([^)]*\)[ \t]*(?::[ \t]*[^{=;]+)?[ \t]*\{",
    re.MULTILINE,
)
# For AR005 TS/JS: `class X extends Y`. Mixin form `extends mixin(Base)` still counts the parent token as depth+1 (conservative).
_JS_EXTENDS_RE = re.compile(
    r"^[ \t]*(?:export[ \t]+(?:default[ \t]+)?)?(?:abstract[ \t]+)?class[ \t]+([A-Za-z_]\w*)(?:<[^>]*>)?[ \t]+extends[ \t]+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# For AR006 TS: exported top-level function declarations and arrow-function const exports.
_TS_EXPORT_FN_RE = re.compile(
    r"^[ \t]*export[ \t]+(?:default[ \t]+)?(?:async[ \t]+)?function[ \t]+([A-Za-z_]\w*)[ \t]*(?:<[^>]*>[ \t]*)?\(",
    re.MULTILINE,
)
_TS_EXPORT_ARROW_RE = re.compile(
    r"^[ \t]*export[ \t]+(?:const|let)[ \t]+([A-Za-z_]\w*)[ \t]*(?::[ \t]*[^=\n]+)?=[ \t]*(?:async[ \t]+)?(?:<[^>]*>[ \t]*)?\(",
    re.MULTILINE,
)
# For AR006 TS class methods: an exported class header. The body is located by
# balanced-brace traversal after this match (not captured in the regex).
_TS_EXPORT_CLASS_HEADER_RE = re.compile(
    r"^[ \t]*export[ \t]+(?:default[ \t]+)?(?:abstract[ \t]+)?class[ \t]+([A-Za-z_]\w*)"
    r"(?:<[^>]*>)?(?:[ \t]+extends[ \t]+[\w$.]+(?:<[^>]*>)?)?"
    r"(?:[ \t]+implements[ \t]+[\w,\s<>.$]+?)?[ \t]*\{",
    re.MULTILINE,
)
# Method-like declaration inside a class body. Restricted to lines that begin with
# whitespace and have a parenthesised parameter list. False positives are filtered
# downstream (e.g. control-flow keywords, private/protected methods, constructor).
_TS_CLASS_METHOD_RE = re.compile(
    r"^[ \t]+"
    r"(?:(public|private|protected)[ \t]+)?"
    r"(?:(?:static|readonly|async|override|abstract)[ \t]+)*"
    r"(?:(?:get|set)[ \t]+)?"
    r"(#?[A-Za-z_$][\w$]*)[ \t]*(?:<[^>]*>[ \t]*)?\(",
    re.MULTILINE,
)
_TS_METHOD_SKIP_NAMES = {
    "if", "for", "while", "switch", "catch", "return", "throw",
    "else", "do", "try", "function", "new",
}


def _is_generic_class_name(name: str, banlist: set[str]) -> str | None:
    """Return the matching banlist word if name is generic, else None.
    Exact match flags; suffix match (≥2 chars before a banlist word in PascalCase) flags too.
    Prefix match does NOT flag: `ServiceWorker` is fine, `UserService` is not."""
    if name in banlist:
        return name
    for word in banlist:
        if len(name) > len(word) and name.endswith(word):
            prefix = name[: -len(word)]
            if len(prefix) >= 2 and prefix[0].isupper():
                return word
    return None


def check_ar003_symbols(path: Path, source: str, cfg: Config) -> list[Finding]:
    findings = []
    banlist_classes = set(cfg.banlist_names)
    banlist_funcs = set(cfg.banlist_functions)

    is_py = is_python(path, cfg)
    if is_py:
        class_re, func_re = _PY_CLASS_RE, _PY_FUNC_RE
    else:
        class_re, func_re = _JS_CLASS_RE, _JS_FUNC_RE

    seen: set[tuple[int, str]] = set()  # (line, name) — dedupe across overlapping regex matches

    for m in class_re.finditer(source):
        name = m.group(1)
        matched = _is_generic_class_name(name, banlist_classes)
        if matched is None:
            continue
        line = source[: m.start()].count("\n") + 1
        if (line, name) in seen:
            continue
        seen.add((line, name))
        msg = (
            f"class name '{name}' is generic ('{matched}' suffix); name by what it does"
            if name != matched
            else f"class name '{name}' is generic; name by what it does"
        )
        findings.append(Finding("AR003", str(path), line, msg, RULE_INFO["AR003"][1]))

    def record(kind: str, name: str, line: int):
        if (line, name) in seen:
            return
        seen.add((line, name))
        findings.append(
            Finding(
                "AR003", str(path), line,
                f"{kind} name '{name}' is generic; name the effect",
                RULE_INFO["AR003"][1],
            )
        )

    for m in func_re.finditer(source):
        if len(m.groups()) > 1:
            name = next((g for g in m.groups() if g), None)
        else:
            name = m.group(1)
        if not name or name not in banlist_funcs:
            continue
        record("function", name, source[: m.start()].count("\n") + 1)

    # JS/TS class methods — catch banlist names as methods (e.g. `process(data) {}` inside a class).
    if not is_py:
        for m in _JS_METHOD_RE.finditer(source):
            name = m.group(1)
            if name in {"if", "for", "while", "switch", "catch", "constructor", "return", "function"}:
                continue
            if name not in banlist_funcs:
                continue
            record("method", name, source[: m.start()].count("\n") + 1)

    return findings


def _strip_line_comment(line: str, is_py: bool) -> str:
    """Remove trailing // or # comments (rough — doesn't honor strings). Good enough for AR004."""
    # handle full-line comment
    stripped = line.lstrip()
    if is_py and stripped.startswith("#"):
        return ""
    if not is_py and stripped.startswith("//"):
        return ""
    marker = "#" if is_py else "//"
    idx = line.find(marker)
    if idx < 0:
        return line
    # crude: ignore if marker is inside a quoted string
    before = line[:idx]
    if before.count('"') % 2 == 1 or before.count("'") % 2 == 1:
        return line
    return before


def check_ar004_metaprog(path: Path, source: str, cfg: Config) -> list[Finding]:
    findings = []
    is_py = is_python(path, cfg)
    patterns = cfg.metaprog_python if is_py else cfg.metaprog_js
    lines = source.splitlines()
    for i, raw in enumerate(lines, start=1):
        code = _strip_line_comment(raw, is_py)
        if not code.strip():
            continue
        for pat in patterns:
            if re.search(pat, code):
                findings.append(
                    Finding(
                        "AR004",
                        str(path),
                        i,
                        f"metaprogramming pattern /{pat}/ — invisible to grep; prefer explicit calls",
                        RULE_INFO["AR004"][1],
                    )
                )
                break  # one finding per line
    return findings


def check_ar005_inheritance(path: Path, tree: ast.AST, module_classes: dict[str, ast.ClassDef], cfg: Config) -> list[Finding]:
    findings = []
    max_depth = cfg.max_inheritance_depth

    def depth(cls: ast.ClassDef, visiting: set[str]) -> int:
        if cls.name in visiting:
            return 0
        visiting = visiting | {cls.name}
        best = 0
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id in module_classes:
                best = max(best, 1 + depth(module_classes[base.id], visiting))
            else:
                best = max(best, 1)  # external base counts as 1
        return best

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            d = depth(node, set())
            if d > max_depth:
                findings.append(
                    Finding(
                        "AR005",
                        str(path),
                        node.lineno,
                        f"class '{node.name}' has inheritance depth {d} (limit: {max_depth}); prefer composition",
                        RULE_INFO["AR005"][1],
                    )
                )
    return findings


_PUBLIC_DUNDERS = {"__init__", "__call__"}


# ---------- TS/JS parser helpers (regex-level, no parser dependency) ----------


def _find_matching(s: str, open_idx: int, open_c: str, close_c: str) -> int:
    """Return the index of the closing bracket matching s[open_idx], or -1 if unbalanced.
    Respects string/template-literal state so nested quotes don't confuse the counter."""
    if open_idx >= len(s) or s[open_idx] != open_c:
        return -1
    depth = 0
    i = open_idx
    in_str: str | None = None
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        elif c in "'\"`":
            in_str = c
        elif c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _find_matching_paren(s: str, open_idx: int) -> int:
    return _find_matching(s, open_idx, "(", ")")


def _find_matching_brace(s: str, open_idx: int) -> int:
    return _find_matching(s, open_idx, "{", "}")


def _split_params(s: str) -> list[str]:
    """Split a parameter list by top-level commas, respecting parens/brackets/braces and strings."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_str: str | None = None
    for c in s:
        if in_str:
            current.append(c)
            if c == in_str:
                in_str = None
            continue
        if c in "'\"`":
            in_str = c
            current.append(c)
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(c)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _param_name_and_typed(param: str) -> tuple[str, bool]:
    """Return (display_name, is_typed) for a single TS parameter.
    A parameter is considered typed when it has an explicit `: Type` annotation,
    or a default value (`= expr`) — TS infers the type from the default."""
    p = param.strip()
    display = p
    # Strip leading modifiers (public/private/protected/readonly on constructor params)
    p = re.sub(r"^(?:public|private|protected|readonly)[ \t]+", "", p)
    # Strip leading rest operator
    if p.startswith("..."):
        p = p[3:].lstrip()
        display = "..." + p.split(":")[0].split("=")[0].strip()
    # Destructured name
    if p.startswith("{") or p.startswith("["):
        opener = p[0]
        closer = "}" if opener == "{" else "]"
        depth = 0
        i = 0
        while i < len(p):
            if p[i] == opener:
                depth += 1
            elif p[i] == closer:
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        after = p[i:].lstrip()
        name = "{destructured}" if opener == "{" else "[destructured]"
    else:
        m = re.match(r"^[A-Za-z_$][\w$]*", p)
        if not m:
            return (display, True)  # unparseable; don't flag
        name = m.group(0)
        after = p[m.end():].lstrip()
    if after.startswith("?"):
        after = after[1:].lstrip()
    return (name, after.startswith(":") or after.startswith("="))


def _return_type_after(source: str, close_paren_idx: int) -> bool:
    """Looking at source after the closing `)`, return True if there's a `: Type` before `{` or `=>`."""
    i = close_paren_idx + 1
    n = len(source)
    # skip whitespace
    while i < n and source[i] in " \t":
        i += 1
    if i >= n:
        return False
    return source[i] == ":"


# ---------- AR005 & AR006 for TS/JS ----------


def check_ar005_ts(path: Path, source: str, cfg: Config) -> list[Finding]:
    """Build a per-file parent map from `class X extends Y` and flag depth > threshold.
    External base classes (not defined in this file) count as depth 1 — same as the Python rule."""
    parent: dict[str, str] = {}
    first_line: dict[str, int] = {}
    for m in _JS_EXTENDS_RE.finditer(source):
        child, par = m.group(1), m.group(2)
        parent[child] = par
        first_line[child] = source[: m.start()].count("\n") + 1

    def depth(name: str, visiting: set[str]) -> int:
        if name in visiting or name not in parent:
            return 0
        visiting = visiting | {name}
        par = parent[name]
        if par in parent:
            return 1 + depth(par, visiting)
        return 1  # external parent

    findings = []
    max_depth = cfg.max_inheritance_depth
    for cls in parent:
        d = depth(cls, set())
        if d > max_depth:
            findings.append(
                Finding(
                    "AR005", str(path), first_line[cls],
                    f"class '{cls}' has inheritance depth {d} (limit: {max_depth}); prefer composition",
                    RULE_INFO["AR005"][1],
                )
            )
    return findings


def check_ar006_ts(path: Path, source: str) -> list[Finding]:
    """TS-only AR006. Flag exported top-level functions and arrow-const exports whose
    parameters lack types. Return-type inference is idiomatic in TypeScript and the
    inference is sound, so missing return types are NOT flagged here — the real
    hallucination surface is at the input seam. `.js`/`.mjs`/`.cjs` have no type
    system — skipped entirely."""
    if path.suffix not in (".ts", ".tsx"):
        return []

    findings: list[Finding] = []

    def untyped_params_from(text: str, paren_open_idx: int) -> list[str] | None:
        """Given text[paren_open_idx] == '(', parse the parameter list and return the
        labels of untyped parameters (or None on parse failure)."""
        close_idx = _find_matching_paren(text, paren_open_idx)
        if close_idx < 0:
            return None
        params = _split_params(text[paren_open_idx + 1 : close_idx])
        labels = []
        for p in params:
            pname, typed = _param_name_and_typed(p)
            if not typed:
                labels.append(pname)
        return labels

    def record(line: int, description: str) -> None:
        findings.append(
            Finding(
                "AR006", str(path), line,
                f"{description}",
                RULE_INFO["AR006"][1],
            )
        )

    for m in _TS_EXPORT_FN_RE.finditer(source):
        untyped = untyped_params_from(source, m.end() - 1)
        if untyped:
            line = source[: m.start()].count("\n") + 1
            record(line, f"exported function '{m.group(1)}' — params without types: {', '.join(untyped)}")
    for m in _TS_EXPORT_ARROW_RE.finditer(source):
        untyped = untyped_params_from(source, m.end() - 1)
        if untyped:
            line = source[: m.start()].count("\n") + 1
            record(line, f"exported arrow '{m.group(1)}' — params without types: {', '.join(untyped)}")

    # Public methods of exported classes: walk each class body via balanced braces,
    # then scan method-like declarations inside. Skip private/protected/# methods and
    # constructors. Constructor is skipped because it's easy for an agent to locate
    # via the class name and the typical failure mode (hallucinated methods) doesn't
    # apply there — the agent isn't going to invent a new constructor.
    for class_match in _TS_EXPORT_CLASS_HEADER_RE.finditer(source):
        class_name = class_match.group(1)
        brace_open = class_match.end() - 1
        if brace_open >= len(source) or source[brace_open] != "{":
            continue
        brace_close = _find_matching_brace(source, brace_open)
        if brace_close < 0:
            continue
        body = source[brace_open + 1 : brace_close]
        body_offset = brace_open + 1

        for mm in _TS_CLASS_METHOD_RE.finditer(body):
            visibility = mm.group(1)
            name = mm.group(2)
            if visibility in ("private", "protected"):
                continue
            if name.startswith("#") or name in _TS_METHOD_SKIP_NAMES or name == "constructor":
                continue
            untyped = untyped_params_from(body, mm.end() - 1)
            if not untyped:
                continue
            abs_start = body_offset + mm.start()
            line = source[:abs_start].count("\n") + 1
            record(line, f"public method '{class_name}.{name}' — params without types: {', '.join(untyped)}")

    return findings


def check_ar006_untyped(path: Path, tree: ast.AST, source_lines: list[str]) -> list[Finding]:
    """Python only: flag public module- and class-level functions lacking annotations on any
    parameter kind (positional, positional-only, keyword-only, *args, **kwargs) or without
    a return annotation. __init__/__call__ on public classes are treated as public boundaries;
    other dunders implement protocols and are skipped. Return annotation is not required on __init__."""
    findings = []

    def is_public_name(name: str) -> bool:
        return not name.startswith("_") or name in _PUBLIC_DUNDERS

    def check_func(fn: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str):
        args = fn.args
        all_args: list[tuple[ast.arg, str]] = []
        for i, a in enumerate(list(args.posonlyargs) + list(args.args)):
            if i == 0 and a.arg in ("self", "cls"):
                continue
            all_args.append((a, a.arg))
        for a in args.kwonlyargs:
            all_args.append((a, a.arg))
        if args.vararg is not None:
            all_args.append((args.vararg, f"*{args.vararg.arg}"))
        if args.kwarg is not None:
            all_args.append((args.kwarg, f"**{args.kwarg.arg}"))

        missing = [label for arg, label in all_args if arg.annotation is None]
        expect_return = not qualname.endswith(".__init__") and fn.name != "__init__"
        no_return = expect_return and fn.returns is None
        if missing or no_return:
            parts = []
            if missing:
                parts.append(f"params without types: {', '.join(missing)}")
            if no_return:
                parts.append("no return annotation")
            findings.append(
                Finding(
                    "AR006",
                    str(path),
                    fn.lineno,
                    f"public function '{qualname}' — {'; '.join(parts)}",
                    RULE_INFO["AR006"][1],
                )
            )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_public_name(node.name):
                check_func(node, node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if is_public_name(sub.name):
                        check_func(sub, f"{node.name}.{sub.name}")

    return findings


def check_ar002_duplicates(all_files: list[tuple[Path, list[str]]], cfg: Config) -> list[Finding]:
    """Hash sliding windows across all files, coalesce overlapping hits into range findings."""
    window = cfg.duplicate_min_lines
    index: dict[str, list[tuple[Path, int]]] = {}

    def normalize(line: str) -> str:
        s = line.strip()
        for marker in (" //", " #"):
            idx = s.find(marker)
            if idx >= 0:
                s = s[:idx].rstrip()
        return s

    _IMPORT_PREFIXES = ("import ", "from ", "require(", "#include ", "use ", "using ", "package ")
    _LICENSE_TOKENS = ("copyright", "licensed under", "apache license", "mit license", "spdx-", "all rights reserved")

    def is_boilerplate(chunk_lines: list[str]) -> bool:
        stripped = [ln for ln in chunk_lines if ln]
        if not stripped:
            return True
        # import-heavy block: >=70% of non-empty lines look like imports
        import_like = sum(1 for ln in stripped if ln.startswith(_IMPORT_PREFIXES))
        if import_like / len(stripped) >= 0.7:
            return True
        # license/copyright header
        lower = "\n".join(stripped).lower()
        if any(tok in lower for tok in _LICENSE_TOKENS):
            return True
        # struct/interface field declarations tend to look duplicated; keep them but don't flag
        # purely brace-and-keyword lines
        brace_like = sum(1 for ln in stripped if set(ln.strip()) <= set("{}()[];, "))
        if brace_like / len(stripped) >= 0.7:
            return True
        return False

    for path, lines in all_files:
        norm = [normalize(ln) for ln in lines]
        for i in range(len(norm) - window + 1):
            chunk_lines = norm[i : i + window]
            chunk = "\n".join(chunk_lines)
            meaningful = sum(1 for ln in chunk_lines if len(ln) > 3)
            if meaningful < window - 1:
                continue
            if is_boilerplate(chunk_lines):
                continue
            h = hashlib.sha1(chunk.encode("utf-8")).hexdigest()
            index.setdefault(h, []).append((path, i + 1))

    # Collect duplicate windows grouped by their peer signature so we can coalesce.
    # A "group" is a stable set of files participating in the same duplication.
    # For each group, merge adjacent/overlapping windows per file into ranges.
    hits_per_group: dict[tuple, list[tuple[Path, int]]] = {}
    for h, hits in index.items():
        if len(hits) < 2:
            continue
        group_key = tuple(sorted(str(p) for p, _ in hits))
        hits_per_group.setdefault(group_key, []).extend(hits)

    findings = []
    for group, hits in hits_per_group.items():
        # sort by (file, line); then merge runs within each file
        per_file: dict[Path, list[int]] = {}
        for p, ln in hits:
            per_file.setdefault(p, []).append(ln)
        # merge consecutive line starts (diff <= 1) into ranges
        ranges_per_file: dict[Path, list[tuple[int, int]]] = {}
        for p, starts in per_file.items():
            starts = sorted(set(starts))
            ranges: list[tuple[int, int]] = []
            cur_start = starts[0]
            cur_end = cur_start + window - 1
            for s in starts[1:]:
                if s <= cur_end + 1:
                    cur_end = max(cur_end, s + window - 1)
                else:
                    ranges.append((cur_start, cur_end))
                    cur_start, cur_end = s, s + window - 1
            ranges.append((cur_start, cur_end))
            ranges_per_file[p] = ranges

        files_ordered = sorted(ranges_per_file.keys(), key=lambda p: str(p))
        primary = files_ordered[0]
        primary_ranges = ranges_per_file[primary]
        for idx, (start, end) in enumerate(primary_ranges):
            peer_desc = []
            # other ranges in the same file
            for j, (os, oe) in enumerate(primary_ranges):
                if j == idx:
                    continue
                peer_desc.append(f"{primary.name}:{os}-{oe}")
            # ranges in other files
            for peer in files_ordered[1:]:
                for ps, pe in ranges_per_file[peer]:
                    peer_desc.append(f"{peer.name}:{ps}-{pe}")
            if not peer_desc:
                continue  # singleton — shouldn't happen since group has len>=2, but defensive
            peer_str = ", ".join(peer_desc)
            findings.append(
                Finding(
                    "AR002",
                    str(primary),
                    start,
                    f"near-duplicate block (lines {start}-{end}) also at: {peer_str}",
                    RULE_INFO["AR002"][1],
                )
            )
    return findings


_BARREL_TS_RE = re.compile(r"^\s*export\s+(?:\*|\{[^}]*\})\s+from\s+['\"]")
_BARREL_PY_RE = re.compile(r"^\s*from\s+\S+\s+import\s+\*\s*$")


def check_ar011_barrel(path: Path, lines: list[str], cfg: Config) -> list[Finding]:
    """Flag files whose non-trivial content is almost entirely re-exports.
    These add a grep hop between consumers and the defining file, and break tree-shaking."""
    meaningful = []
    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            continue
        if stripped.startswith(("//", "#", "/*", "*", "*/")):
            continue
        meaningful.append(stripped)
    if len(meaningful) < 5:
        return []
    is_py = is_python(path, cfg)
    barrel_re = _BARREL_PY_RE if is_py else _BARREL_TS_RE
    barrel_lines = sum(1 for ln in meaningful if barrel_re.match(ln))
    if barrel_lines / len(meaningful) > 0.7:
        return [
            Finding(
                "AR011",
                str(path),
                1,
                f"{barrel_lines}/{len(meaningful)} meaningful lines are re-exports; this is a barrel file",
                RULE_INFO["AR011"][1],
            )
        ]
    return []


def check_ar007_test_colocation(root: Path, all_files: list[tuple[Path, list[str]]], cfg: Config) -> list[Finding]:
    """Heuristic: if there's a top-level tests/ or __tests__ directory with >5 test files
    AND src/ has <5 colocated test files, flag it."""
    if not root.is_dir():
        return []

    distant_tests = 0
    colocated_tests = 0
    source_files = 0

    test_name_re = re.compile(r"(\.test\.|_test\.|\.spec\.)[jt]sx?$|^test_.*\.py$|.*_test\.py$")
    test_dir_names = {"tests", "test", "__tests__", "spec", "specs"}

    for path, _ in all_files:
        name = path.name
        parts = set(path.parts)
        is_test = bool(test_name_re.search(name))
        in_test_dir = any(part in test_dir_names for part in parts)

        if is_test or in_test_dir:
            if in_test_dir:
                distant_tests += 1
            else:
                colocated_tests += 1
        else:
            source_files += 1

    if distant_tests > 5 and colocated_tests < max(5, source_files // 10):
        return [
            Finding(
                "AR007",
                str(root),
                1,
                f"{distant_tests} tests in distant test dirs, only {colocated_tests} colocated; agents miss them",
                RULE_INFO["AR007"][1],
            )
        ]
    return []


# ---------- Suppressions ----------

_SUPPRESS_LINE_RE = re.compile(r"agent-lint:\s*disable(?:=([A-Z0-9,\s]+))?")
_SUPPRESS_FILE_RE = re.compile(r"agent-lint:\s*disable-file(?:=([A-Z0-9,\s]+))?")


def _suppressions_for_file(lines: list[str]) -> tuple[set[str] | None, dict[int, set[str] | None]]:
    """Return (file_disable, per_line_disable).
    file_disable: set of rule IDs disabled for whole file, or None if no disable-file directive.
                  An empty set means disable all (no arg).
    per_line_disable: map line_number -> set of rules disabled for that line and the next line.
                      None means disable all."""
    file_disable: set[str] | None = None
    per_line: dict[int, set[str] | None] = {}

    for i, raw in enumerate(lines, start=1):
        fm = _SUPPRESS_FILE_RE.search(raw)
        if fm:
            rules_str = fm.group(1)
            if rules_str is None:
                file_disable = set()  # disable all
            else:
                rules = {r.strip() for r in rules_str.split(",") if r.strip()}
                file_disable = (file_disable or set()) | rules
            continue
        lm = _SUPPRESS_LINE_RE.search(raw)
        if lm:
            rules_str = lm.group(1)
            rules: set[str] | None = None if rules_str is None else {
                r.strip() for r in rules_str.split(",") if r.strip()
            }
            # suppress the same line (if it's a trailing comment) and the next code line
            per_line.setdefault(i, rules)
            per_line.setdefault(i + 1, rules)
    return file_disable, per_line


def _apply_suppressions(
    findings: list[Finding], suppressions_by_file: dict[str, tuple[set[str] | None, dict[int, set[str] | None]]]
) -> list[Finding]:
    kept = []
    for f in findings:
        supp = suppressions_by_file.get(f.file)
        if supp is None:
            kept.append(f)
            continue
        file_disable, per_line = supp
        if file_disable is not None:
            # empty set = disable all; non-empty = disable listed
            if not file_disable or f.rule in file_disable:
                continue
        if f.line in per_line:
            rules = per_line[f.line]
            if rules is None or f.rule in rules:
                continue
        kept.append(f)
    return kept


# ---------- Orchestrator ----------


def lint_path(root: Path, cfg: Config, enabled_rules: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    all_files: list[tuple[Path, list[str]]] = []
    suppressions: dict[str, tuple[set[str] | None, dict[int, set[str] | None]]] = {}

    for path in iter_source_files(root, cfg):
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        lines = source.splitlines()
        all_files.append((path, lines))
        suppressions[str(path)] = _suppressions_for_file(lines)

        if "AR001" in enabled_rules:
            findings.extend(check_ar001_file_size(path, lines, cfg))
        if "AR008" in enabled_rules:
            findings.extend(check_ar008_long_lines(path, lines, cfg))
        if "AR003" in enabled_rules:
            findings.extend(check_ar003_filename(path, cfg))
            findings.extend(check_ar003_symbols(path, source, cfg))
        if "AR004" in enabled_rules:
            findings.extend(check_ar004_metaprog(path, source, cfg))
        if "AR011" in enabled_rules:
            findings.extend(check_ar011_barrel(path, lines, cfg))

        if is_python(path, cfg):
            try:
                tree = ast.parse(source)
            except SyntaxError:
                tree = None
            if tree is not None:
                if "AR005" in enabled_rules:
                    module_classes = {
                        n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                    }
                    findings.extend(check_ar005_inheritance(path, tree, module_classes, cfg))
                if "AR006" in enabled_rules:
                    findings.extend(check_ar006_untyped(path, tree, lines))
        elif is_js(path, cfg):
            if "AR005" in enabled_rules:
                findings.extend(check_ar005_ts(path, source, cfg))
            if "AR006" in enabled_rules:
                findings.extend(check_ar006_ts(path, source))

    if "AR002" in enabled_rules:
        findings.extend(check_ar002_duplicates(all_files, cfg))
    if "AR007" in enabled_rules:
        findings.extend(check_ar007_test_colocation(root, all_files, cfg))

    findings = _apply_suppressions(findings, suppressions)
    findings.sort(key=lambda f: (f.file, f.line, f.rule))
    return findings


# ---------- Output ----------


def _read_source_line(path_str: str, lineno: int) -> str | None:
    try:
        with open(path_str, encoding="utf-8", errors="replace") as fh:
            for i, ln in enumerate(fh, start=1):
                if i == lineno:
                    return ln.rstrip("\n")
    except OSError:
        return None
    return None


def format_text(findings: list[Finding], root: Path, quiet: bool = False, show_context: bool = True) -> str:
    if quiet:
        return f"{len(findings)} findings"

    out = []
    if not findings:
        out.append(f"No findings. Codebase at {root} passes agent-readable-code rules.")
        return "\n".join(out)

    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for fp in sorted(by_file):
        out.append(f"\n{fp}")
        for f in by_file[fp]:
            info = RULE_INFO[f.rule]
            evidence = info[2]
            fix = info[3]
            header = f"  {f.rule} [line {f.line}] ({evidence}) {f.message}"
            out.append(header)
            if show_context:
                src = _read_source_line(f.file, f.line)
                if src is not None and src.strip():
                    snippet = src.rstrip()
                    if len(snippet) > 120:
                        snippet = snippet[:117] + "..."
                    out.append(f"       | {snippet}")
            out.append(f"       why: {f.why}")
            out.append(f"       fix: {fix}")

    rule_counts: dict[str, int] = {}
    for f in findings:
        rule_counts[f.rule] = rule_counts.get(f.rule, 0) + 1
    summary = ", ".join(f"{r}={n}" for r, n in sorted(rule_counts.items()))
    out.append(f"\n{len(findings)} findings across {len(by_file)} files ({summary})")
    out.append("see references/research.md for evidence strength of each rule")
    return "\n".join(out)


def format_json(findings: list[Finding]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2)


# ---------- Config loading ----------


def load_config(config_path: Path | None) -> Config:
    cfg = Config()
    if config_path is None:
        return cfg
    if not config_path.exists():
        print(f"warning: config file not found: {config_path}", file=sys.stderr)
        return cfg
    text = config_path.read_text(encoding="utf-8")
    overrides = _parse_simple_yaml(text)
    cfg.data.update(overrides)
    return cfg


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML-ish parser: scalar values, inline lists `[a, b]`, and block lists via
    `key:` followed by indented `- item` lines. Does not support block scalars (`|`, `>`)
    or nested dicts — keep configs flat, or install PyYAML for richer needs."""
    result: dict = {}
    current_list: list | None = None
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            if current_list is not None and line.lstrip().startswith("- "):
                current_list.append(line.lstrip()[2:].strip().strip("'\""))
            continue
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        current_key = key
        if not rest:
            current_list = []
            result[key] = current_list
        elif rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                result[key] = [v.strip().strip("'\"") for v in inner.split(",")]
            current_list = None
        else:
            val = rest.strip("'\"")
            try:
                result[key] = int(val)
            except ValueError:
                try:
                    result[key] = float(val)
                except ValueError:
                    result[key] = val
            current_list = None
    return result


# ---------- Entry point ----------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="file or directory to lint")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--quiet", action="store_true", help="summary only")
    parser.add_argument("--rules", type=str, help="comma-separated rule IDs to run")
    parser.add_argument("--config", type=Path, help="YAML config override")
    parser.add_argument("--max", type=int, default=-1, help="exit nonzero if findings exceed N")
    parser.add_argument("--no-context", action="store_true", help="skip source-line snippets in text output")
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"error: path does not exist: {args.path}", file=sys.stderr)
        return 2

    cfg = load_config(args.config)

    all_rules = set(RULE_INFO.keys())
    if args.rules:
        enabled = {r.strip() for r in args.rules.split(",") if r.strip()}
        unknown = enabled - all_rules
        if unknown:
            print(f"error: unknown rules: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
    else:
        enabled = all_rules

    findings = lint_path(args.path, cfg, enabled)

    if args.json:
        print(format_json(findings))
    else:
        print(format_text(findings, args.path, quiet=args.quiet, show_context=not args.no_context))

    if args.max >= 0 and len(findings) > args.max:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
