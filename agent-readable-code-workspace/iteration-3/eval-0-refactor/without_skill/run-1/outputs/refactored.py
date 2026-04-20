"""User domain model and a small, explicit helper surface.

This module replaces the previous ``utils.py`` dumping ground. It now has a
single responsibility: define the ``User`` entity together with the minimal,
fully typed helpers its callers need.

Guidelines applied:

* Concrete, intent-revealing names (no ``process`` / ``handle`` / ``do_stuff``).
* Full type annotations on every public symbol.
* No ``eval`` and no ``importlib.import_module`` — dynamic dispatch is
  replaced by an explicit, registered handler table.
* No ``__getattr__`` magic — unknown operations raise a clear error.
* Flat class structure; shared behavior is expressed via mixins/protocols
  rather than a five-level inheritance chain.

If you need the removed behaviors (arbitrary dynamic import, dynamic
attribute dispatch), prefer an explicit, audited registry at the call site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol, TypeVar

__all__ = [
    "AuditRecord",
    "User",
    "add_integers",
    "identity",
    "OperationHandler",
    "OperationRegistry",
]


# ---------------------------------------------------------------------------
# Small, explicit helpers (replace ``process`` and ``handle``)
# ---------------------------------------------------------------------------

T = TypeVar("T")


def identity(value: T) -> T:
    """Return ``value`` unchanged.

    Replaces the old ``process(data)`` passthrough. Kept only because the
    original code used it as a placeholder; prefer inlining at call sites.
    """
    return value


def add_integers(left: int, right: int) -> int:
    """Return the sum of two integers.

    Replaces ``handle(x, y)``. The name now states what the function does.
    """
    return left + right


# ---------------------------------------------------------------------------
# Domain model: flat, composed, fully typed
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditRecord:
    """Immutable audit metadata attached to persisted entities."""

    created_at: datetime
    updated_at: datetime

    @classmethod
    def new(cls) -> "AuditRecord":
        now = datetime.now(timezone.utc)
        return cls(created_at=now, updated_at=now)


@dataclass
class User:
    """Application user.

    The previous code modeled this with a five-level inheritance chain
    (``User -> Auditable -> Persisted -> Entity -> Base``) where every
    intermediate class was empty. Here the same concepts are expressed
    with a flat dataclass that *composes* an :class:`AuditRecord` and
    carries its own identifier — easier to read, test, and extend.
    """

    id: str
    email: str
    audit: AuditRecord = field(default_factory=AuditRecord.new)


# ---------------------------------------------------------------------------
# Explicit operation dispatch (replaces ``DynamicAPI.__getattr__`` and ``eval``)
# ---------------------------------------------------------------------------


class OperationHandler(Protocol):
    """Callable that executes a named operation with keyword arguments."""

    def __call__(self, **kwargs: object) -> object: ...


class OperationRegistry:
    """Explicit name-to-handler table.

    Motivation
    ----------
    The original module offered two escape hatches that defeat static
    analysis:

    * ``run_expression(expr)`` ran arbitrary strings through ``eval``.
    * ``DynamicAPI.__getattr__`` returned a silent no-op lambda for any
      attribute name, so typos never surfaced.

    Both are replaced here by a registry: callers must register a handler
    up front, and unknown operations raise :class:`KeyError` loudly.
    """

    def __init__(
        self,
        handlers: Mapping[str, OperationHandler] | None = None,
    ) -> None:
        self._handlers: dict[str, OperationHandler] = dict(handlers or {})

    def register(self, name: str, handler: OperationHandler) -> None:
        """Register ``handler`` under ``name``. Raises if already registered."""
        if name in self._handlers:
            raise ValueError(f"Operation already registered: {name!r}")
        self._handlers[name] = handler

    def invoke(self, name: str, /, **kwargs: object) -> object:
        """Invoke the handler registered under ``name``.

        Raises :class:`KeyError` with a clear message if the operation is
        not registered — no silent no-ops.
        """
        try:
            handler = self._handlers[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._handlers)) or "<none>"
            raise KeyError(
                f"Unknown operation {name!r}. Registered: {known}"
            ) from exc
        return handler(**kwargs)


# ---------------------------------------------------------------------------
# Notes on removed functionality
# ---------------------------------------------------------------------------
#
# * ``run_expression(expr)`` — removed. If a caller genuinely needs to
#   evaluate user-supplied expressions, use a sandboxed expression language
#   (e.g. ``asteval``) rather than raw ``eval``.
# * ``dynamic_import(name)`` — removed. If a plugin system is required,
#   build an explicit registry (see :class:`OperationRegistry`) or use
#   ``entry_points`` from ``importlib.metadata`` with an allow-list.
# * ``Manager.do_stuff(thing)`` — removed. The original was an identity
#   method on an otherwise empty class; call :func:`identity` directly or,
#   better, inline the value.
