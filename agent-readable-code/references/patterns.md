# Before / after patterns

Worked examples for each practice. The linter rules cited in SKILL.md map directly to the anti-pattern side of each pair.

---

## AR003 — Naming

### Before: generic-name dumping ground

```python
# utils.py (1200 lines of unrelated functions)

def process(data):
    ...

def handle_it(x, y):
    ...

class Manager:
    def do_stuff(self, thing):
        ...
```

An agent asked "where is the refund logic?" greps for `refund`, finds nothing, then scans `utils.py`, `helpers.py`, and `services/Manager.py` one by one, running out of context before locating the right function.

### After: domain-specific names, feature-colocated

```python
# billing/refunds.py

def issue_refund_and_notify_customer(order_id: str, reason: RefundReason) -> Refund:
    ...

def reverse_stripe_charge(charge_id: str) -> None:
    ...
```

Now `grep refund` returns one file. The function name answers "what does it do?" without opening the file.

---

## AR001 + AR002 — File size and near-duplicates

### Before: 1400-line file with copy-pasted error handling

```ts
// api/routes.ts (1400 lines)

export async function createOrder(req: Request, res: Response) {
  try {
    // 40 lines
  } catch (err) {
    if (err instanceof ValidationError) {
      logger.warn({ err, path: req.path });
      return res.status(400).json({ error: err.message });
    }
    logger.error({ err, path: req.path });
    return res.status(500).json({ error: "Internal error" });
  }
}

export async function updateOrder(req: Request, res: Response) {
  try {
    // 40 lines
  } catch (err) {
    if (err instanceof ValidationError) {
      logger.warn({ err, path: req.path });
      return res.status(400).json({ error: err.message });
    }
    logger.error({ err, path: req.path });
    return res.status(500).json({ error: "Internal error" });
  }
}
// ...28 more handlers with the same catch block
```

Claude Code tries `str_replace` on one of those catch blocks and fails — 30 identical copies, no unique context. The agent falls back to rewriting the whole file and drops half of it because the file is too long.

### After: split by resource + shared error handler

```ts
// api/orders/create.ts  (70 lines)
import { handleError } from "../errors";

export async function createOrder(req: Request, res: Response) {
  try {
    // logic
  } catch (err) { return handleError(err, req, res); }
}

// api/errors.ts
export function handleError(err: unknown, req: Request, res: Response) {
  if (err instanceof ValidationError) { ... }
  logger.error({ err, path: req.path });
  return res.status(500).json({ error: "Internal error" });
}
```

One seam, no duplicates, every file under 200 lines.

---

## AR004 — Metaprogramming

### Before: dynamic dispatch via `__getattr__`

```python
class API:
    def __getattr__(self, name):
        endpoint = name.replace("_", "-")
        return lambda **kw: self._request(endpoint, **kw)

api = API()
api.list_customers()   # invisible to grep
api.refund_payment(id=...)
```

Grep for `refund_payment` returns nothing. The agent either invents a definition that doesn't exist or rewrites the call in a way the dispatcher doesn't handle.

### After: explicit methods

```python
class API:
    def list_customers(self) -> list[Customer]:
        return self._request("list-customers")

    def refund_payment(self, payment_id: str) -> Refund:
        return self._request("refund-payment", payment_id=payment_id)
```

Grep works. Types flow through. Autocomplete works for humans too. The "duplication" is not a problem — it's the price of being searchable.

---

## AR005 — Inheritance depth

### Before: five-level chain

```python
class Base: ...
class Entity(Base): ...
class Persisted(Entity): ...
class Auditable(Persisted): ...
class User(Auditable): ...
```

An agent asked to "add a `last_login` field to `User`" fabricates a `super().__init__` signature from `Persisted` it has never seen, because it's reasoning about the chain rather than reading it.

### After: composition

```python
class User:
    def __init__(self, id: str, email: str):
        self.id = id
        self.email = email
        self.audit = AuditLog(entity_id=id)
        self.persistence = PersistenceMeta()
```

Each collaborator is a field the agent can grep for. No method resolution order puzzle.

---

## AR006 — Types and comments

### Before: untyped boundary + stale docstring

```python
def charge(user, amount, **opts):
    """Charges a user and returns True on success. Sends email receipt."""
    # (code that no longer sends an email; returns a Charge object now)
    ...
```

The agent trusts the docstring. Writes code that checks `if charge(...)`, which is truthy for any `Charge` object, masking failures.

### After: typed signature, accurate comment or none

```python
def charge(user: User, amount: Money, *, idempotency_key: str) -> Charge:
    ...
```

The type signature is the spec. No prose required. If behavior is non-obvious, one short *why* comment — not a restatement of the signature.

---

## AR007 — Test colocation

### Before: tests in a distant mirror tree

```
src/billing/refunds.ts
tests/unit/billing/refunds.test.ts
tests/integration/billing/refunds.integration.ts
```

The agent edits `refunds.ts`, doesn't find adjacent tests, and either skips testing or invents a new test file in the wrong place. CI catches it later, but only after a wasted turn.

### After: colocated

```
src/billing/refunds.ts
src/billing/refunds.test.ts
src/billing/refunds.integration.ts
```

The agent sees the tests in the same directory listing as the source. Running them is `bun test src/billing/` — obvious from the structure.

---

## AR008 — Long lines

### Before: minified asset checked in

```
src/vendor/analytics.min.js    // single 38,000-character line
```

`ripgrep` matches spill the entire line into the agent's context, truncating or confusing parsing.

### After: vendored assets out of tree or ignored

Put it in `public/vendor/` (never read by an agent working on source), or add to `.gitignore` / `.claudeignore` / `.cursorignore`.

---

## Combined: a feature module that makes agents' lives easy

```
src/billing/refunds/
├── index.ts              // 40 lines: public API + types re-export
├── types.ts              // 30 lines: Refund, RefundReason, RefundStatus
├── issue-refund.ts       // 120 lines: one exported function, typed
├── issue-refund.test.ts  // colocated unit test
├── reverse-charge.ts     // 80 lines
└── reverse-charge.test.ts
```

- Every file under 200 lines → `AR001` clean.
- No duplicate error handling (factored into a shared `handleError`) → `AR002` clean.
- Names say what functions do → `AR003` clean.
- No reflection or deep inheritance → `AR004` / `AR005` clean.
- Typed public surface in `index.ts` → `AR006` clean.
- Tests next to source → `AR007` clean.

An agent can land on any file in this module cold and act correctly.
