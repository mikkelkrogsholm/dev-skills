"""Arithmetic and identity helpers used by the fixture test-suite.

This module replaces the former ``utils.py`` dumping ground. It exposes a
small, explicit API: two pure functions and one dataclass. There is no
dynamic dispatch, no inheritance, and no metaprogramming — everything a
caller needs is visible to ``grep`` on this file alone.

If new behavior is needed, add it to a module named after its domain
(``billing.py``, ``audit_log.py``, ...). Do not grow this file into a
generic helpers bucket.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

__all__ = [
    "echo_payload",
    "add_integers",
    "User",
]


T = TypeVar("T")


def echo_payload(payload: T) -> T:
    """Return ``payload`` unchanged.

    Replaces the former ``process(data)``. Exists as a typed identity
    function for the fixture tests; callers should prefer passing values
    directly over threading them through this.
    """
    return payload


def add_integers(left: int, right: int) -> int:
    """Return the sum of two integers.

    Replaces the former ``handle(x, y)``, which hid its numeric intent
    behind generic names. Typed as ``int`` so an agent cannot misuse it
    for string concatenation without a type-check failure.
    """
    return left + right


@dataclass(frozen=True, slots=True)
class User:
    """A persisted, auditable user record.

    Replaces the five-level ``Base -> Entity -> Persisted -> Auditable
    -> User`` inheritance chain with a single flat dataclass. The fields
    that previously lived implicitly in intermediate base classes are
    now explicit attributes on this record.

    ``frozen=True`` prevents accidental mutation; ``slots=True`` makes
    typo-ed attribute assignment fail loudly rather than silently
    creating a new attribute.
    """

    id: str
    email: str
    created_at: str  # ISO-8601 timestamp, injected by the caller's clock.
    updated_at: str  # ISO-8601 timestamp, injected by the caller's clock.


# Removed in this refactor (see problems.md for rationale):
#
# - ``run_expression`` / ``eval``:            AR004, unsafe and untraceable.
# - ``dynamic_import`` / ``importlib``:       AR004, hides the import graph.
# - ``Manager.do_stuff``:                     AR003, carried no behavior.
# - ``DynamicAPI.__getattr__``:               AR004, silent no-op dispatch.
# - ``Base/Entity/Persisted/Auditable``:      AR005, ceremony without behavior.
#
# If a real use case emerges for any of the above, reintroduce it as a
# named function in a domain-specific module with explicit arguments
# and a typed signature — not as a generic dispatch primitive.
