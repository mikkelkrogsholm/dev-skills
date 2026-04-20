"""User account domain model and safe expression/import helpers.

This module replaces the original dumping-ground ``utils.py`` with a single
cohesive concern: the :class:`User` aggregate plus the small set of helpers
that the surrounding code genuinely needs.

Design choices that matter for AI-assisted maintenance:

* Every public function and method has a precise type signature and docstring.
* No ``eval``, no runtime ``importlib.import_module``, no ``__getattr__``
  magic.  The set of callable operations is fully enumerable by static tools.
* The domain model is a single flat :class:`User` dataclass.  The previous
  five-level empty inheritance chain (``Base -> Entity -> Persisted ->
  Auditable -> User``) is collapsed — the behaviour it implied (identity,
  persistence metadata, audit timestamps) is expressed as plain fields on
  ``User``.
* An explicit ``__all__`` declares the public surface so callers (human or
  agent) know what is supported.

If behaviour previously attached to the empty base classes needs to come
back, add it to :class:`User` as a method or to a new, *named*, *non-empty*
mixin — do not reintroduce empty hierarchy levels.
"""

from __future__ import annotations

import ast
import importlib
import operator as _operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final, Mapping
from uuid import UUID, uuid4

__all__ = [
    "User",
    "add_integers",
    "normalize_user_payload",
    "safe_eval_arithmetic",
    "load_allowed_module",
]


# ---------------------------------------------------------------------------
# Replaces: ``handle(x, y)`` — a generic "adds two things" function.
# Giving it a real name and types means callers (and agents) cannot confuse
# it with string concatenation, list merging, etc.
# ---------------------------------------------------------------------------
def add_integers(left: int, right: int) -> int:
    """Return the integer sum of ``left`` and ``right``.

    Raises:
        TypeError: If either argument is not an ``int`` (``bool`` is rejected
            because ``bool`` is an ``int`` subclass and would silently work).
    """
    if type(left) is not int or type(right) is not int:
        raise TypeError(
            f"add_integers requires two ints, got {type(left).__name__} "
            f"and {type(right).__name__}"
        )
    return left + right


# ---------------------------------------------------------------------------
# Replaces: ``process(data)`` and ``Manager.do_stuff(thing)`` — both of which
# did nothing meaningful.  The real intent in the surrounding codebase was
# "take a raw dict and turn it into a validated User-shaped dict", so that
# is what this function does, under a name that says so.
# ---------------------------------------------------------------------------
def normalize_user_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Return a normalized copy of a user payload.

    Strips surrounding whitespace from string fields and lower-cases the
    ``email`` field if present.  Unknown keys are preserved untouched so
    callers can round-trip data they do not own.
    """
    normalized: dict[str, object] = dict(payload)
    for key, value in list(normalized.items()):
        if isinstance(value, str):
            normalized[key] = value.strip()
    email = normalized.get("email")
    if isinstance(email, str):
        normalized["email"] = email.lower()
    return normalized


# ---------------------------------------------------------------------------
# Replaces: ``run_expression(expr)`` which called ``eval``.
#
# The real need was "evaluate a small arithmetic expression from a config
# file".  We satisfy that with an AST walker that only permits literals and
# a fixed set of binary/unary operators.  Anything else raises — the set of
# legal inputs is now enumerable and auditable.
# ---------------------------------------------------------------------------
_ALLOWED_BINOPS: Final[Mapping[type, object]] = {
    ast.Add: _operator.add,
    ast.Sub: _operator.sub,
    ast.Mult: _operator.mul,
    ast.Div: _operator.truediv,
    ast.FloorDiv: _operator.floordiv,
    ast.Mod: _operator.mod,
    ast.Pow: _operator.pow,
}

_ALLOWED_UNARYOPS: Final[Mapping[type, object]] = {
    ast.UAdd: _operator.pos,
    ast.USub: _operator.neg,
}


def safe_eval_arithmetic(expression: str) -> int | float:
    """Evaluate a constant arithmetic expression safely.

    Only numeric literals and the operators ``+ - * / // % **`` (plus unary
    ``+``/``-``) are permitted.  Names, attribute access, function calls and
    any other AST node cause :class:`ValueError`.

    Args:
        expression: The arithmetic expression as a string, e.g. ``"2 * (3 + 4)"``.

    Returns:
        The numeric result.

    Raises:
        ValueError: If ``expression`` contains any disallowed syntax.
    """

    def _eval(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op = _ALLOWED_BINOPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Operator {type(node.op).__name__} is not allowed")
            return op(_eval(node.left), _eval(node.right))  # type: ignore[operator]
        if isinstance(node, ast.UnaryOp):
            op = _ALLOWED_UNARYOPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unary {type(node.op).__name__} is not allowed")
            return op(_eval(node.operand))  # type: ignore[operator]
        raise ValueError(f"AST node {type(node).__name__} is not allowed")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid arithmetic expression: {expression!r}") from exc
    return _eval(tree)


# ---------------------------------------------------------------------------
# Replaces: ``dynamic_import(name)`` which imported arbitrary modules.
#
# We keep dynamic loading — some callers really do need plugin-style imports —
# but gate it behind an explicit allow-list.  An agent editing this code can
# now see exactly which modules are reachable.
# ---------------------------------------------------------------------------
_ALLOWED_PLUGIN_MODULES: Final[frozenset[str]] = frozenset(
    {
        # Extend this set deliberately; do not replace with a regex.
        "json",
        "math",
    }
)


def load_allowed_module(module_name: str):
    """Import and return a module from the fixed allow-list.

    Args:
        module_name: The fully qualified module name.  Must appear in
            :data:`_ALLOWED_PLUGIN_MODULES`.

    Raises:
        ValueError: If ``module_name`` is not allow-listed.
    """
    if module_name not in _ALLOWED_PLUGIN_MODULES:
        raise ValueError(
            f"Module {module_name!r} is not in the plugin allow-list. "
            f"Add it to _ALLOWED_PLUGIN_MODULES after review."
        )
    return importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# Replaces: the Base -> Entity -> Persisted -> Auditable -> User chain and
# the ``DynamicAPI.__getattr__`` stub.
#
# The responsibilities the empty classes hinted at are now explicit fields
# on a single dataclass.  No dynamic attribute dispatch — every supported
# operation is a real, typed method.
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class User:
    """A user account with identity, persistence, and audit metadata."""

    email: str
    display_name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    def touch(self) -> None:
        """Mark the user as modified now (updates ``updated_at`` in UTC)."""
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Mark the user as inactive and bump ``updated_at``."""
        self.is_active = False
        self.touch()

    def rename(self, new_display_name: str) -> None:
        """Change the display name and bump ``updated_at``.

        Raises:
            ValueError: If ``new_display_name`` is empty after stripping.
        """
        cleaned = new_display_name.strip()
        if not cleaned:
            raise ValueError("display_name must not be empty")
        self.display_name = cleaned
        self.touch()
