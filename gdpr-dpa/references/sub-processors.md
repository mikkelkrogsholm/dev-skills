# Sub-processor Database

GDPR metadata for known third-party services. Cross-reference detected services against this list during project scanning.

---

## Neon

- **Role**: Primary database — stores all application data
- **Detectable via**: `@neondatabase/serverless`, `DATABASE_URL` containing `neon.tech`
- **EU region available**: Yes (Frankfurt: `aws-eu-central-1`)
- **EU region config**: Set region to `aws-eu-central-1` when creating the project in the Neon console
- **DPA**: https://neon.tech/dpa
- **Data received**: All data stored in the database

---

## Turso

- **Role**: Primary database — stores all application data
- **Detectable via**: `@libsql/client`, `TURSO_DATABASE_URL` containing `turso.io`
- **EU region available**: Yes (multiple EU locations available at creation)
- **EU region config**: Select an EU location (e.g., `fra` for Frankfurt) when creating the database
- **DPA**: https://turso.tech/legal/dpa (verify)
- **Data received**: All data stored in the database

---

## Upstash

- **Role**: Cache, session store, message queue
- **Detectable via**: `@upstash/redis`, `@upstash/qstash`, `UPSTASH_REDIS_REST_URL`, `QSTASH_TOKEN`
- **EU region available**: Yes (eu-west-1, eu-central-1 — select at database creation)
- **EU region config**: Choose EU region when creating the database in the Upstash console
- **DPA**: https://upstash.com/dpa
- **Data received**: Session data (may include user identity), cached data, queue message payloads

---

## Sentry

- **Role**: Error tracking and performance monitoring — receives error context
- **Detectable via**: `@sentry/node`, `@sentry/react`, `@sentry/nextjs`, `sentry_sdk` (Python), `SENTRY_DSN`
- **EU region available**: Yes — requires separate EU org at `sentry.io/for/eu/`; the DSN domain differs (`*.ingest.de.sentry.io` for EU)
- **EU region config**: Create a new Sentry organization using the EU data region. EU DSNs use the `*.ingest.de.sentry.io` domain
- **DPA**: https://sentry.io/legal/dpa/
- **Data received**: Error payloads, stack traces, user context (if `Sentry.setUser()` called), breadcrumbs (including console.log output), request URLs and headers

---

## Resend

- **Role**: Email delivery — sends emails on behalf of the application
- **Detectable via**: `resend`, `RESEND_API_KEY`, calls to `api.resend.com`
- **EU region available**: No dedicated EU region as of 2024; data processed in US. Covered by DPA + SCCs.
- **EU region config**: Not available — DPA includes Standard Contractual Clauses (SCCs) for EU-US transfers
- **DPA**: https://resend.com/legal/dpa
- **Data received**: Recipient email addresses, email content, send timestamps

---

## Stripe

- **Role**: Payment processing
- **Detectable via**: `stripe`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, calls to `api.stripe.com`
- **EU region available**: Yes — Stripe processes EU data within EU
- **EU region config**: Automatic for EU-based accounts; confirm in Stripe Dashboard under Data Residency
- **DPA**: https://stripe.com/legal/dpa
- **Data received**: Payment card data, customer name/email/address, transaction history

---

## Trigger.dev

- **Role**: Background job execution platform
- **Detectable via**: `@trigger.dev/sdk`, `@trigger.dev/react-hooks`, `TRIGGER_SECRET_KEY`, calls to `cloud.trigger.dev`
- **EU region available**: Check current availability at trigger.dev — note in DPA if EU region not confirmed
- **EU region config**: Check trigger.dev documentation for current EU region support
- **DPA**: https://trigger.dev/legal/dpa (verify)
- **Data received**: Job payload data (may contain PII depending on what jobs process), execution logs

---

## Meilisearch Cloud

- **Role**: Search index — receives all indexed document data
- **Detectable via**: `meilisearch`, `MEILISEARCH_HOST` containing `meilisearch.io`, calls to `*.meilisearch.io`
- **EU region available**: Yes (available at index creation)
- **EU region config**: Select an EU region when creating the project in Meilisearch Cloud
- **DPA**: https://www.meilisearch.com/dpa (verify)
- **Data received**: All indexed document content (may contain PII if user data is indexed)
- **Note**: Self-hosted Meilisearch is not a sub-processor — you control the data

---

## Vercel

- **Role**: Application hosting and edge network
- **Detectable via**: `vercel.json`, `VERCEL_*` env vars, `.vercel` directory
- **EU region available**: Yes (edge network includes EU nodes)
- **EU region config**: Set the default region to an EU region (e.g., `fra1`) in `vercel.json` or project settings
- **DPA**: https://vercel.com/legal/dpa
- **Data received**: Request/response data, logs, environment variables, deployed code

---

## Cloudflare

- **Role**: CDN, DDoS protection, edge compute
- **Detectable via**: `@cloudflare/workers-types`, `wrangler.toml`, `CF_*` env vars
- **EU region available**: Yes (EU data stays in EU with Data Localization Suite)
- **EU region config**: Enable Data Localization Suite in the Cloudflare dashboard (enterprise feature)
- **DPA**: https://www.cloudflare.com/cloudflare-customer-dpa/
- **Data received**: All HTTP traffic, IP addresses, request metadata

---

## OpenAI

- **Role**: AI/LLM inference
- **Detectable via**: `openai`, `OPENAI_API_KEY`, calls to `api.openai.com`
- **EU region available**: Yes (EU data residency available for enterprise)
- **EU region config**: EU data residency requires Enterprise agreement — standard API uses US infrastructure
- **DPA**: https://openai.com/policies/data-processing-addendum
- **Data received**: All prompt and completion content (may contain PII if user data is included in prompts)

---

## Anthropic

- **Role**: AI/LLM inference
- **Detectable via**: `@anthropic-ai/sdk`, `ANTHROPIC_API_KEY`, calls to `api.anthropic.com`
- **EU region available**: Check current availability at anthropic.com
- **EU region config**: Check Anthropic documentation for current EU region support
- **DPA**: https://www.anthropic.com/legal/dpa (verify)
- **Data received**: All prompt and completion content

---

## AWS S3 / compatible storage

- **Role**: File/object storage
- **Detectable via**: `@aws-sdk/client-s3`, `aws-sdk`, `AWS_ACCESS_KEY_ID`, `S3_BUCKET`, `S3_ENDPOINT`
- **EU region available**: Yes (eu-west-*, eu-central-*, eu-north-*)
- **EU region config**: Set the bucket region to an EU region (e.g., `eu-central-1`) and ensure the `AWS_REGION` env var matches
- **DPA**: https://aws.amazon.com/agreement/data-processing/
- **Data received**: All stored files and objects (may contain user-uploaded files, documents, images)

---

## Supabase

- **Role**: Database, auth, storage, realtime
- **Detectable via**: `@supabase/supabase-js`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- **EU region available**: Yes (Frankfurt available)
- **EU region config**: Select `eu-central-1` (Frankfurt) when creating the Supabase project
- **DPA**: https://supabase.com/legal/dpa
- **Data received**: All stored data, auth records, storage files

---

## PlanetScale

- **Role**: MySQL-compatible database
- **Detectable via**: `@planetscale/database`, `DATABASE_URL` containing `psdb.cloud`
- **EU region available**: Yes (EU regions available)
- **EU region config**: Select an EU region when creating the PlanetScale database
- **DPA**: https://planetscale.com/legal/dpa (verify)
- **Data received**: All database contents

---

## Not Sub-processors

The following are NOT sub-processors — they run inside your own process or infrastructure and do not transmit data to an external third party:

- **Drizzle ORM, Prisma** — database clients running in your server process
- **React, Vite, shadcn/ui, TanStack Query/Router** — client-side UI libraries
- **Hono, Express, Fastify** — your own web framework
- **Zod** — validation library
- **BullMQ** — uses your own Redis (the Redis provider is the sub-processor)
- **Self-hosted Meilisearch** — you control the infrastructure
- **Coolify** — self-hosted PaaS you control
- **Better Auth** — self-hosted auth (no external service)
- **RustFS** — self-hosted storage
