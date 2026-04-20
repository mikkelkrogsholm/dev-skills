"""User audit records and a small safe-expression evaluator.

This module replaces the former ``utils.py`` dumping ground. It now owns two
narrow responsibilities:

1. :class:`AuditedUser` — a frozen value object for a user with audit metadata.
2. :func:`evaluate_arithmetic` — a bounded, AST-validated numeric expression
   evaluator used by the reporting layer. It exists because we need a safer
   replacement for the old ``eval``-based helper; see the function docstring
   for the security invariant.

The old ``process``, ``handle``, ``Manager.do_stuff``, ``run_expression``,
``dynamic_import``, and ``DynamicAPI`` helpers were removed. If you are
looking for them, the git history has the rename map; do not reintroduce
them under new names.
"""

from __future__ import annotations

import ast
import operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

__all__ = [
    "AuditedUser",
    "evaluate_arithmetic",
    "sum_integers",
    "UnsafeExpressionError",
]


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuditedUser:
    """A user record with audit metadata.

    Replaces the old ``User -> Auditable -> Persisted -> Entity -> Base``
    inheritance chain. The audit fields are composed in as plain attributes
    rather than mixed in through a hierarchy, so an agent can see everything
    this type carries by reading this one dataclass.

    ``frozen=True`` prevents accidental mutation (the audit trail is supposed
    to be immutable once written). ``slots=True`` makes ``user.foo = bar``
    raise immediately instead of silently adding an attribute.
    """

    id: str
    email: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    is_deleted: bool = False


# ---------------------------------------------------------------------------
# Safe arithmetic evaluation
# ---------------------------------------------------------------------------


class UnsafeExpressionError(ValueError):
    """Raised when :func:`evaluate_arithmetic` is given something it will not run.

    This includes syntactically invalid input, non-arithmetic nodes
    (attribute access, calls, names, comprehensions, etc.), and operators
    outside the allowed set.
    """


# Explicit, grep-able dispatch table. An agent adding support for a new
# operator edits this one map; there is no decorator registry, no
# ``__getattr__``, no ``importlib`` lookup.
_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_arithmetic(expression: str) -> float:
    """Evaluate a numeric expression without using :func:`eval`.

    Only numeric literals and the operators in :data:`_BINARY_OPERATORS` and
    :data:`_UNARY_OPERATORS` are allowed. Anything else raises
    :class:`UnsafeExpressionError`.

    Security invariant: this function must never execute arbitrary attribute
    access, function calls, or name lookups. If you need to add a new node
    type, add it to the explicit dispatch tables above *and* add a matching
    test in ``test_safe_expression.py``.

    >>> evaluate_arithmetic("1 + 2 * 3")
    7.0
    >>> evaluate_arithmetic("(10 - 4) / 3")
    2.0
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"invalid expression: {expression!r}") from exc

    return _evaluate_node(tree.body)


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.BinOp):
        op = _BINARY_OPERATORS.get(type(node.op))
        if op is None:
            raise UnsafeExpressionError(f"operator not allowed: {type(node.op).__name__}")
        return op(_evaluate_node(node.left), _evaluate_node(node.right))

    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPERATORS.get(type(node.op))
        if op is None:
            raise UnsafeExpressionError(f"unary operator not allowed: {type(node.op).__name__}")
        return op(_evaluate_node(node.operand))

    raise UnsafeExpressionError(f"node type not allowed: {type(node).__name__}")


# ---------------------------------------------------------------------------
# Small typed helpers (replacements for the former generic ``handle``/``process``)
# ---------------------------------------------------------------------------


def sum_integers(left: int, right: int) -> int:
    """Return ``left + right``.

    This replaces the old ``handle(x, y)``. The name reflects what it does;
    the types anchor callers against drift.
    """
    return left + right
