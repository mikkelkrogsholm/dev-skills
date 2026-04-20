"""User account domain model and simple arithmetic/identity helpers.

This module intentionally replaces a former ``utils.py`` dumping ground.
It exposes:

* :class:`User` — a flat user record with audit metadata.
* :func:`add_integers` — explicit integer addition.
* :func:`identity` — generic pass-through used as a default callback.

Dynamic-dispatch helpers that previously lived here (``eval``-based
expression runner, ``importlib.import_module`` shim, ``__getattr__``
proxy, and a deep empty inheritance chain) have been removed because
they defeat static analysis and make the module impossible to maintain
safely. If you need dynamic behavior, add a narrow, explicitly-typed
function with an allow-list — do not reintroduce the old helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TypeVar

__all__ = [
    "User",
    "add_integers",
    "identity",
]


T = TypeVar("T")


def identity(value: T) -> T:
    """Return ``value`` unchanged.

    Use as an explicit no-op callback where a transform function is
    required by an API but no transformation is desired. Prefer this
    over an unnamed ``lambda x: x`` so call sites document intent.
    """
    return value


def add_integers(left: int, right: int) -> int:
    """Return the integer sum of ``left`` and ``right``.

    This is intentionally narrow: both operands must be ``int``. For
    string concatenation or float arithmetic, use the appropriate
    dedicated function rather than overloading this one.
    """
    if not isinstance(left, int) or isinstance(left, bool):
        raise TypeError(f"left must be int, got {type(left).__name__}")
    if not isinstance(right, int) or isinstance(right, bool):
        raise TypeError(f"right must be int, got {type(right).__name__}")
    return left + right


def _utcnow() -> datetime:
    """Return the current UTC time. Factored out for test patching."""
    return datetime.now(timezone.utc)


@dataclass
class User:
    """A persisted, auditable user account.

    Replaces the previous ``Base -> Entity -> Persisted -> Auditable ->
    User`` inheritance chain. All fields that the old chain hinted at
    (identity, persistence marker, audit timestamps) are represented
    explicitly here. A single flat class is easier for both humans and
    AI agents to reason about than five empty parent classes.

    Attributes:
        id: Stable unique identifier for this user.
        email: Primary email address. Not validated here; validate at
            the boundary where the value enters the system.
        created_at: UTC timestamp when the record was created.
        updated_at: UTC timestamp of the last mutation.
        is_persisted: ``True`` once the record has been written to the
            backing store. New in-memory instances default to ``False``.
    """

    id: str
    email: str
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    is_persisted: bool = False

    def mark_persisted(self) -> None:
        """Mark the user as saved to the backing store.

        Updates :attr:`updated_at` and sets :attr:`is_persisted` to
        ``True``. Idempotent: safe to call on an already-persisted user.
        """
        self.is_persisted = True
        self.updated_at = _utcnow()

    def touch(self) -> None:
        """Refresh :attr:`updated_at` to the current UTC time."""
        self.updated_at = _utcnow()
