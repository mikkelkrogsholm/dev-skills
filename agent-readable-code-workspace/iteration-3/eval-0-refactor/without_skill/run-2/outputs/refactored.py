"""User domain model and safe arithmetic/identity helpers.

This module replaces the original `utils.py` dumping ground. It exposes a
small, explicitly-typed surface that an agent can reason about without
executing the code:

- `identity`      — pass-through helper, explicitly typed.
- `add_integers`  — total addition on integers (replaces the ambiguous
                    `handle(x, y)`).
- `User`          — a flat domain record (replaces the empty 4-level
                    inheritance chain).

The original module also contained three unsafe/metaprogramming entry
points (`eval`-based expression runner, `importlib`-based dynamic import,
and a `__getattr__` catch-all dispatcher). They are intentionally *not*
reimplemented here: each one hides behavior from static analysis and
should be replaced at the call site with an explicit, enumerated
alternative (a parser, a direct import, or a typed method, respectively).
See `rationale.md` for the migration guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

T = TypeVar("T")


def identity(value: T) -> T:
    """Return `value` unchanged.

    Replaces the original `process(data)`, which had no transformation
    logic but a name that implied one. If callers actually needed a
    transformation, they should call the specific transformation
    function directly rather than going through a generic wrapper.
    """
    return value


def add_integers(left: int, right: int) -> int:
    """Return the sum of two integers.

    Replaces the original `handle(x, y)`. The new name documents the
    operation; the type annotations document the contract. If callers
    need to add floats or concatenate strings, they should use `+`
    directly or a purpose-named helper — not an overloaded `handle`.
    """
    return left + right


@dataclass(frozen=True)
class User:
    """A persisted, auditable user record.

    Replaces the `Base -> Entity -> Persisted -> Auditable -> User`
    inheritance chain. Each ancestor in the original chain was empty,
    so the hierarchy conveyed taxonomy without behavior. A flat
    dataclass expresses the same intent (an identifiable record with
    audit fields) while remaining trivially introspectable.

    Fields:
        id:          Stable unique identifier (replaces the implicit
                     "entity" concept).
        created_at:  When the record was first persisted (replaces
                     "Persisted").
        updated_at:  Last modification timestamp (replaces
                     "Auditable").
        email:       The user's email address.
    """

    id: str
    email: str
    created_at: datetime
    updated_at: datetime


__all__ = ["identity", "add_integers", "User"]
