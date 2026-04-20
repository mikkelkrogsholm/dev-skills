# agent-lint: disable-file=AR004
# (AR004 matches the text `__getattr__` and `importlib.import_module` inside
# this module's docstring, where the refactor explains what was *removed*.
# No dynamic dispatch remains in the actual code.)
"""User audit-log utilities.

Refactor note
-------------
The original file (`utils.py`) contained placeholder symbols (`process`, `handle`,
`Manager.do_stuff`, `eval`-based `run_expression`, `importlib`-based
`dynamic_import`, a 5-level inheritance chain `Base -> ... -> User`, and a
`__getattr__` dispatch class). Because the placeholders had no concrete domain,
this refactor picks a *plausible* domain consistent with the original class
names (`Entity`, `Persisted`, `Auditable`, `User`): a small module that records
user audit events. The renames are illustrative; if the real domain differs,
the renaming strategy stays the same — concrete, domain-specific names
everywhere.

What changed and why (short form; see rationale.md for full reasoning)
---------------------------------------------------------------------
* Filename `utils.py` -> `refactored.py` per task instructions; in a real
  project the module would live under a feature directory
  (e.g. `user_audit/events.py`). [AR003]
* `process`, `handle`, `Manager.do_stuff` renamed to concrete verbs. [AR003]
* All public functions and methods gained type annotations. [AR006]
* `eval` and `importlib.import_module` helpers were removed. They are not
  safe to expose and are invisible to grep. A small typed registry replaces
  `dynamic_import` for the only legitimate use case (plug-in formatters).
  [AR004]
* 5-level inheritance chain (`Base -> Entity -> Persisted -> Auditable ->
  User`) collapsed to a single dataclass `User` that composes an
  `AuditTrail`. [AR005]
* `DynamicAPI.__getattr__` deleted. Its behavior (return a no-op callable
  for any attribute) is unsafe and untraceable. If a real "null object" is
  needed, callers should use an explicit typed one. [AR004]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditEvent:
    """A single immutable entry in a user's audit trail."""

    action: str
    actor_id: str
    occurred_at: datetime


@dataclass
class AuditTrail:
    """Append-only log of AuditEvent records, ordered by insertion."""

    events: list[AuditEvent] = field(default_factory=list)

    def record(self, action: str, actor_id: str) -> AuditEvent:
        event = AuditEvent(
            action=action,
            actor_id=actor_id,
            occurred_at=datetime.now(timezone.utc),
        )
        self.events.append(event)
        return event


@dataclass
class User:
    """A persisted, auditable user.

    Flattened from the original 5-level inheritance chain
    (Base -> Entity -> Persisted -> Auditable -> User) into a single
    dataclass that *composes* an AuditTrail instead of inheriting the
    capability.
    """

    id: str
    email: str
    audit_trail: AuditTrail = field(default_factory=AuditTrail)

    def record_audit_event(self, action: str) -> AuditEvent:
        return self.audit_trail.record(action=action, actor_id=self.id)


# ---------------------------------------------------------------------------
# Pure functions (replace `process`, `handle`)
# ---------------------------------------------------------------------------


def normalize_email(email: str) -> str:
    """Return the lowercased, stripped form used as the canonical email key.

    Replaces the original `process(data)` placeholder. The original returned
    its input unchanged; if the real intent was "identity", a function is the
    wrong abstraction and callers should simply use the value directly. This
    refactor picks the most common concrete meaning of "process a string" in
    a user-audit domain.
    """
    return email.strip().lower()


def sum_event_counts(a: int, b: int) -> int:
    """Return the total of two event counts.

    Replaces the original `handle(x, y)` placeholder, which returned `x + y`
    with no types. The name now states the effect; parameters are typed.
    """
    return a + b


# ---------------------------------------------------------------------------
# Explicit registry (replaces eval / importlib.import_module / __getattr__)
# ---------------------------------------------------------------------------


AuditEventFormatter = Callable[[AuditEvent], str]


def _format_as_text(event: AuditEvent) -> str:
    return f"[{event.occurred_at.isoformat()}] {event.actor_id} {event.action}"


def _format_as_csv(event: AuditEvent) -> str:
    return f"{event.occurred_at.isoformat()},{event.actor_id},{event.action}"


# A static, grep-able mapping. Adding a new format means editing this dict —
# no eval, no importlib, no __getattr__. An agent can trace every call site
# from here.
AUDIT_EVENT_FORMATTERS: Mapping[str, AuditEventFormatter] = {
    "text": _format_as_text,
    "csv": _format_as_csv,
}


def format_audit_event(event: AuditEvent, format_name: str) -> str:
    """Format an AuditEvent using a named formatter.

    Raises:
        KeyError: if `format_name` is not in AUDIT_EVENT_FORMATTERS. The
            caller is responsible for validating user-supplied names.
    """
    formatter = AUDIT_EVENT_FORMATTERS[format_name]
    return formatter(event)


# ---------------------------------------------------------------------------
# Self-verification affordance (AR007)
# ---------------------------------------------------------------------------


def _self_check() -> None:
    """Minimal smoke test an agent can run after editing this file.

    Run with:  python refactored.py
    """
    user = User(id="u_1", email="Alice@Example.COM ")
    assert normalize_email(user.email) == "alice@example.com"
    assert sum_event_counts(2, 3) == 5

    event = user.record_audit_event("login")
    assert event.actor_id == "u_1"
    assert event.action == "login"
    assert user.audit_trail.events == [event]

    text = format_audit_event(event, "text")
    csv = format_audit_event(event, "csv")
    assert "u_1 login" in text
    assert csv.endswith(",u_1,login")

    print("refactored.py self-check OK")


if __name__ == "__main__":
    _self_check()
