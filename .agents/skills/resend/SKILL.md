---
name: resend
description: "Resend — email API for developers. Use when building with Resend or asking about its APIs, configuration, patterns, or integration. Fetch live documentation for up-to-date details."
---

# Resend

Resend is a developer-focused email API for sending transactional and marketing emails via REST or SDK.

## Documentation

- **Docs**: https://resend.com/docs/llms.txt

## Best Practices

**Unsubscribe links are never auto-injected.** Resend does not append unsubscribe headers or links automatically. You must manually include an unsubscribe link in every marketing email body, and configure a custom unsubscribe page separately. Omitting this violates CAN-SPAM/GDPR and causes deliverability issues.

**The `resend.dev` sandbox domain only sends to your own verified email.** Using `onboarding@resend.dev` as the from address will produce a 403 error if the recipient is anyone other than the account owner's email. Always switch to a verified domain before sending to real users.

**Use idempotency keys on send to prevent duplicate emails on retry.** Network failures trigger retries, and without an idempotency key each retry creates a new send. Pass a stable `idempotency_key` (e.g. derived from your database record ID) in the request header so Resend deduplicates server-side.
