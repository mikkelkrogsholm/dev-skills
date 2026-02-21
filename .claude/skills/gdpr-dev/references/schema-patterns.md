# GDPR-Friendly Schema Patterns

Schema design patterns that make GDPR compliance easier to implement and maintain.

---

## User Table

Group PII fields together so they can be nulled in a single targeted update on erasure. Keep the row to preserve referential integrity for foreign keys in other tables.

```sql
-- Group PII fields — easy to null on erasure
users (
  id          uuid primary key,
  created_at  timestamptz not null,
  -- PII: null these on erasure, keep the row for FK integrity
  email       text,
  name        text,
  -- Erasure tracking
  erased_at   timestamptz
)
```

The `erased_at` column serves two purposes: it records when erasure occurred for audit purposes, and it signals to application code that the user's PII has been removed (allowing graceful handling of null fields elsewhere).

---

## Audit Log (Pseudonymized)

Audit logs must survive the erasure of the user they reference. Use a hash of the user ID as the reference so the log remains useful after the user record is erased. Do not add a foreign key to the users table — the intentional absence of a FK is what allows the audit log to remain intact.

```sql
-- Use a hash of user_id, never the raw ID or any PII
audit_logs (
  id          uuid primary key,
  user_ref    text not null,   -- sha256(user_id) — pseudonymized
  action      text not null,
  created_at  timestamptz not null
  -- NO FK to users — intentional
)
```

Pseudonymize before erasure:

```sql
-- Run this before erasing the user row
UPDATE audit_logs
SET user_ref = encode(sha256(user_id::text::bytea), 'hex')
WHERE user_id = ?;
```

---

## Consent Records

Store proof of consent at the moment of collection. You must be able to demonstrate what was consented to, when, by whom, and under which version of your privacy policy.

```sql
consent_records (
  id                     uuid primary key,
  user_id                uuid references users(id),
  purpose                text not null,        -- 'marketing_email', 'analytics', etc.
  granted                boolean not null,
  ip_address             text,                 -- who consented (PII — apply retention policy)
  privacy_policy_version text,                 -- which policy was in effect
  created_at             timestamptz not null
)
```

Each consent purpose is a separate row. When a user withdraws consent for marketing emails, insert a new row with `granted = false` rather than updating the existing one. This preserves the full audit trail.

---

## Right to Erasure Implementation

```sql
-- Step 1: Pseudonymize audit trail before erasing the user
UPDATE audit_logs
SET user_ref = encode(sha256(user_id::text::bytea), 'hex')
WHERE user_id = ?;

-- Step 2: Null PII fields, keep the row for referential integrity
UPDATE users
SET email = null,
    name  = null,
    erased_at = now()
WHERE id = ?;
```

This two-step approach means:
- The audit trail survives and remains consistent (pseudonymized actor)
- Foreign keys from orders, payments, and other tables remain valid
- The user's personal data is gone
- You have a record of when erasure occurred

---

## Data Minimization in Schema Design

Collect the minimum data required for the stated purpose.

| Instead of | Use | When |
|---|---|---|
| `date_of_birth date` | `age_verified boolean` | You only need to confirm the user is 18+ |
| `full_address text` | `country_code char(2)` | You only need country for tax or VAT purposes |
| `phone_number text` | omit entirely | You have no stated purpose for it |
| `gender text` | omit or use `pronouns text` | Only collect if required for the product |

The guiding question: if you had to justify storing this field to a data protection authority, what would you say? If the answer is "we might need it someday," do not store it.

---

## Separating PII from Behavioral Data

Avoid mixing personal data with behavioral or analytical data in the same table. Keep a clean boundary so erasure is scoped and predictable.

```sql
-- PII lives here
users (id, email, name, erased_at, ...)

-- Behavioral data references user ID only
page_views (id, user_id, path, viewed_at)
-- user_id can be set to null on erasure if no other legal basis applies

-- Audit data uses pseudonymized reference
audit_logs (id, user_ref, action, created_at)
-- user_ref is a hash, survives erasure intact
```

This separation means an erasure request has a well-defined scope: null the PII table, decide what to do with behavioral references, leave the audit trail alone.
