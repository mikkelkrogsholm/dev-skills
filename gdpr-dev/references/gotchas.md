# GDPR Gotchas for Developers

A full catalogue of GDPR anti-patterns encountered when building web applications. Organized by area.

---

## Data Collection Anti-patterns

- **Storing more data than needed** — collecting full date of birth when only an age bracket is required; storing full address when only country is needed for VAT. Violates the data minimization principle.
- **Pre-checked consent boxes** — invalid under GDPR. Consent must be an active, affirmative opt-in. Pre-checked boxes do not constitute valid consent.
- **Bundled consent** — one checkbox for all purposes. Each processing purpose requires a separate, specific consent. A single "I agree to everything" checkbox is not valid.
- **Storing consent intent without proof** — must record the timestamp, the IP address, and the version of the privacy policy the user consented to. Storing only `marketing_opt_in = true` is insufficient.

---

## Logging and Observability

- **PII in application logs** — use structured logging with user IDs only, never user objects or personal fields.
- **Sentry breadcrumbs** — Sentry captures `console.log` calls as breadcrumbs. Any PII logged to the console is captured by Sentry. Treat Sentry as a potential PII store and configure data scrubbing.
- **Error messages containing triggering data** — `Error: User john@example.com not found` sends an email address to every log aggregator and error tracker in your stack. Sanitize error messages before they are thrown.
- **Analytics receiving PII via URL parameters** — `/confirm?email=user@example.com` or `/reset?token=abc` sends PII to Google Analytics, Plausible, and any other analytics tool that captures full URLs. Use POST requests or hash sensitive parameters before redirect.
- **IP addresses in access logs without a retention policy** — IP addresses are personal data. nginx and other server logs retain them indefinitely by default. Set log rotation and define a retention period.

---

## Authentication and Sessions

- **JWT payload containing email, name, or other PII** — JWTs cannot be revoked or recalled after issuance. Any PII in the payload persists until the token expires, making erasure requests impossible to fulfill completely. Use opaque session IDs or put only a non-identifying user ID in the JWT with a short expiry.
- **Session stores (Redis) containing full user objects** — the TTL on session keys is your de facto data retention policy for that session data. Set explicit TTLs. Do not store full user objects; store the user ID and reload from the database when needed.
- **"Remember me" tokens stored indefinitely** — long-lived tokens stored without expiry are personal data with no retention policy. Set a maximum lifetime and rotate on use.

---

## Database and Schema

- **Soft deletes that leave PII fields populated** — `deleted_at = now()` satisfies no erasure obligation. Null out all PII fields on erasure; keep the row to preserve referential integrity.
- **No separation between PII and behavioral or audit data** — mixing personal data with audit events makes it difficult to scope erasure correctly. Keep PII in dedicated tables and reference it by ID from audit and behavioral tables.
- **Audit logs containing raw user PII** — audit logs should use a pseudonymized reference (e.g., a hash of the user ID) rather than the user ID itself or any personal fields. This allows the audit trail to survive erasure.
- **Backups not covered by the erasure policy** — erasure from the live database does not affect backup snapshots. Either define a backup retention window that aligns with your erasure SLA, or use anonymization so backups are safe regardless.
- **Cascading deletes that destroy the audit trail** — using `ON DELETE CASCADE` from users to audit logs destroys the audit history when a user is deleted. Instead, pseudonymize the actor in audit logs before erasure, then erase the user record.

---

## Third-party Integrations

- **Sending PII to services without a Data Processing Agreement (DPA)** — any service that processes personal data on your behalf requires a DPA. This includes analytics providers, error trackers, email services, and CRMs.
- **Using a non-EU region when an EU region is available** — Sentry, Neon, Upstash, and many other services offer EU-hosted regions. Using a US region for EU user data requires an additional legal mechanism (SCCs) and increases compliance risk. Prefer EU regions by default.
- **Forwarding full request or response bodies to logging services** — middleware that logs raw requests will capture any PII submitted in forms or API payloads. Allowlist the fields to log rather than logging everything.

---

## Email and Marketing

- **Legitimate interest as a basis for direct marketing** — legitimate interest is not a valid legal basis for direct marketing emails to EU individuals. Explicit opt-in consent is required.
- **No unsubscribe mechanism** — every marketing or promotional email must include a clear and functional unsubscribe link. Transactional emails are exempt, but only if they are genuinely transactional.
- **Sending emails without a record of the consent that authorized them** — you must be able to demonstrate that the person opted in, when they did so, and under which version of your privacy policy. Store consent records at the time of collection.

---

## Data Retention

- **No retention policy for any data type** — GDPR requires that data is not kept longer than necessary for the stated purpose. Every data type should have a defined retention period.
- **Keeping data "just in case"** — the data minimization and purpose limitation principles require that data is collected and retained only for a specific, documented purpose. Storing data because it might be useful later is not a valid basis.
