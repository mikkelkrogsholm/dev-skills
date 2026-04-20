"""User identity value object.

This file replaces the former `utils.py` dumping ground. The original file
mixed four unrelated concerns (identity model, generic data passthrough,
arithmetic, dynamic code execution, dynamic imports, a reflective API
facade). In a real repository each concern belongs in a domain-named file,
e.g.::

    users/user.py              # this file
    # The following were deleted outright, not refactored:
    #   - `process(data)` / `handle(x, y)` — dead or trivial; inline at call site
    #   - `eval(expr)` — unsafe and untraceable
    #   - `importlib.import_module(name)` — replace with explicit imports
    #   - `DynamicAPI.__getattr__` dispatch — replace with named methods
    #     per endpoint (see rationale.md)

Only the `User` value object has an obvious, safe, grep-able shape, so that
is what this file keeps.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["User"]


@dataclass(frozen=True, slots=True)
class User:
    """Immutable user identity.

    `frozen=True` prevents accidental mutation by an agent editing a caller.
    `slots=True` makes a typo like `user.emial = "x"` fail loudly with
    AttributeError instead of silently creating a latent bug.
    """

    id: str
    email: str
