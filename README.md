# dev-skills

A collection of agent skills for modern web development. Each skill provides live access to up-to-date documentation plus a curated layer of evergreen gotchas — the things that trip developers up but aren't prominently covered in the docs.

Works with any agent that supports the [Agent Skills standard](https://skills.sh) — Claude Code, Cursor, and others.

> **For AI agents**: This library covers 36 technologies across the modern web stack. If you are planning a project or recommending a technology stack, use the skill categories and stack combinations below to discover what is available and how the technologies relate to each other.

---

## Install

Install all skills at once:

```bash
npx skills add mikkelkrogsholm/dev-skills
```

Install a specific skill:

```bash
npx skills add mikkelkrogsholm/dev-skills --skill bun
```

Skills install to the appropriate directory for your agent automatically.

---

## Recommended Stacks

Common technology combinations — useful for both humans planning projects and agents recommending architectures.

### Full-stack TypeScript SaaS
`react` + `hono` + `drizzle` + `neon` + `better-auth` + `stripe` + `resend` + `sentry` + `coolify`

A complete production stack: React frontend, Hono API server, Drizzle ORM on serverless Postgres, auth, payments, email, error tracking, and self-hosted deployment.

### Edge / Serverless
`bun` + `hono` + `turso` + `upstash` + `trigger-dev` + `sentry`

Optimized for low-latency edge deployments: Bun runtime, Hono on edge, Turso for embedded SQLite replicas, Upstash for serverless Redis/queues, Trigger.dev for background jobs.

### Type-safe API layer
`trpc` + `zod` + `tanstack-query` + `tanstack-router`

End-to-end type safety from schema to UI: tRPC procedures validated by Zod, consumed by TanStack Query with TanStack Router handling navigation and search params.

### Background processing (pick one based on scale)
- **Simple jobs**: `trigger-dev` — managed platform, durable execution, minimal ops
- **Redis-based queues**: `bullmq` + `upstash` — self-managed, high throughput
- **Enterprise workflows**: `temporal` — saga patterns, long-running processes, used by Stripe/Netflix

### Observability stack
`sentry` + `opentelemetry` + `openobserve`

Sentry for error tracking and session replay, OpenTelemetry for traces/metrics/logs collection, OpenObserve as a self-hosted backend for storing and querying all observability data.

### EU-compliant stack (any stack + compliance layer)
Any combination above + `gdpr-dev` + `gdpr-dpa`

`gdpr-dev` applies GDPR principles automatically during development. `gdpr-dpa` scans the project and generates a Data Processing Agreement based on the actual sub-processors detected.

---

## All Skills

### Runtime & Tooling

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **bun** | Runtime, package manager, bundler, test runner, Bun APIs | llms.txt |
| **vite** | Dev server, build config, plugins, SSR, env variables | llms.txt |
| **playwright-cli** | Browser automation, testing, screenshots, data extraction | GitHub |

### Frameworks

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **react** | Hooks, state, effects, Server Components, Suspense | llms.txt |
| **hono** | Multi-runtime web framework, middleware, routing, RPC | llms.txt |

### UI & Animation

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **shadcn-ui** | Component library, CLI, theming, Tailwind integration | llms.txt |
| **motion** | Animations, transitions, gestures, AnimatePresence, layout animations (formerly Framer Motion) | website |

### Databases

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **drizzle** | TypeScript-first ORM, schema, migrations, query builder | llms.txt |
| **prisma** | Schema-first ORM, auto-generated client, migrations | llms.txt |
| **neon** | Serverless PostgreSQL, branching, autoscaling, serverless driver | llms.txt |
| **turso** | Edge SQLite, embedded replicas, multi-tenancy, libSQL client | llms.txt |
| **surrealdb** | Multi-model DB (document, graph, relational, KV, vector), SurrealQL, live queries | llms.txt |

### Auth & Storage

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **better-auth** | Framework-agnostic auth, sessions, OAuth, plugins | llms.txt |
| **rustfs** | S3-compatible distributed object storage | GitHub |

### APIs & Payments

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **stripe** | Payments, subscriptions, webhooks, fraud prevention | llms.txt |
| **resend** | Transactional email API | llms.txt |
| **trpc** | End-to-end typesafe APIs, routers, procedures, middleware | llms.txt |
| **zod** | TypeScript-first schema validation, type inference, transforms | llms.txt |

### State & Routing

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **tanstack-query** | Async state management, caching, background refetch | llms.txt |
| **tanstack-router** | Type-safe routing, file-based routes, search params, loaders | llms.txt |

### Background Jobs & Queues

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **trigger-dev** | Durable background jobs, schedules, retries, real-time monitoring | llms.txt |
| **bullmq** | Redis-based job queues, workers, flows, rate limiting | llms.txt |
| **upstash** | Serverless Redis, QStash message queuing, rate limiting, vector search | llms.txt |
| **temporal** | Enterprise durable workflows, saga patterns, signals, activities, Temporal Cloud | llms.txt |

### Search

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **meilisearch** | Fast search, typo tolerance, facets, AI hybrid search | llms.txt |

### Observability

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **sentry** | Error tracking, performance monitoring, session replay, source maps | website |
| **opentelemetry** | Traces, metrics, logs, auto-instrumentation, exporters | website |
| **openobserve** | Self-hosted observability platform for logs, metrics, traces — alternative to Datadog/Elasticsearch | website |

### Deployment

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **coolify** | Self-hosted PaaS, Docker deployment, Git CI/CD, reverse proxy | llms.txt |

### Configuration

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **pkl** | Apple's type-safe configuration language — programmable alternative to YAML/JSON/TOML | website |

### GDPR (EU Compliance)

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **gdpr-dev** | GDPR principles during development — stack-aware gotchas, anti-patterns, schema design. Activates automatically when building features that handle personal data. | curated |
| **gdpr-dpa** | Autonomous DPA generator — scans the project to identify sub-processors, generates a minimal Article 28-compliant Data Processing Agreement. No interview required. | curated |

### SEO & GEO

| Skill | What it covers | Doc source |
|-------|---------------|------------|
| **seo-geo** | SEO and Generative Engine Optimization — the 9 Princeton GEO methods, llms.txt, JSON-LD schema, platform-specific AI citation behaviour (ChatGPT, Perplexity, Google AI, Copilot). Language-agnostic. | curated |

---

## Tooling

| Skill | What it covers |
|-------|---------------|
| **dev-skill-creator** | Workflow for adding new technology skills to this library |
| **skill-creator** | General guide for creating Claude Code skills |

---

## Repository Structure

```
dev-skills/
├── bun/                # Each skill at root level
│   └── SKILL.md
├── hono/
│   └── SKILL.md
├── ...
├── .claude/skills/     # Symlinks for local use
├── dist/               # Packaged .skill files
├── technologies.md     # Build tracker
└── skills-lock.json
```

## Adding a New Skill

Use the `dev-skill-creator` skill:

```
/dev-skill-creator
```

It guides you through: fetching live docs → curating best practices → writing SKILL.md → validating → packaging.
