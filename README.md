# dev-skills

A collection of Claude Code skills for modern web development. Each skill gives Claude live access to up-to-date documentation plus a curated layer of evergreen gotchas — the things that trip developers up but aren't prominently covered in the docs.

## Install

Install all skills at once:

```bash
npx skills add mikkelkrogsholm/dev-skills
```

Install a specific skill:

```bash
npx skills add mikkelkrogsholm/dev-skills --skill bun
```

Install to a specific agent:

```bash
npx skills add mikkelkrogsholm/dev-skills -a claude-code
```

Skills install to `~/.claude/skills/` (global) or `.claude/skills/` (project-level).

---

## How Skills Work

Skills are loaded into Claude's context when relevant. Each skill contains:
- A **triggering description** so Claude knows when to activate it
- A **live docs pointer** so Claude fetches current documentation rather than relying on training data
- **Curated best practices** covering non-obvious pitfalls that Claude gets wrong by default

---

## Skills

### Runtime & Tooling

| Skill | What it covers |
|-------|---------------|
| **bun** | Runtime, package manager, bundler, test runner, Bun APIs |
| **vite** | Dev server, build config, plugins, SSR, env variables |
| **playwright-cli** | Browser automation, testing, screenshots, data extraction |

### Frameworks

| Skill | What it covers |
|-------|---------------|
| **react** | Hooks, state, effects, Server Components, Suspense |
| **hono** | Multi-runtime web framework, middleware, routing, RPC |

### UI

| Skill | What it covers |
|-------|---------------|
| **shadcn-ui** | Component library, CLI, theming, Tailwind integration |

### Databases

| Skill | What it covers |
|-------|---------------|
| **drizzle** | TypeScript-first ORM, schema, migrations, query builder |
| **prisma** | Schema-first ORM, auto-generated client, migrations |
| **neon** | Serverless PostgreSQL, branching, autoscaling, serverless driver |
| **turso** | Edge SQLite, embedded replicas, multi-tenancy, libSQL client |

### Auth & Storage

| Skill | What it covers |
|-------|---------------|
| **better-auth** | Framework-agnostic auth, sessions, OAuth, plugins |
| **rustfs** | S3-compatible distributed object storage |

### APIs & Payments

| Skill | What it covers |
|-------|---------------|
| **stripe** | Payments, subscriptions, webhooks, fraud prevention |
| **resend** | Transactional email API |
| **trpc** | End-to-end typesafe APIs, routers, procedures, middleware |
| **zod** | TypeScript-first schema validation, type inference, transforms |

### State & Routing

| Skill | What it covers |
|-------|---------------|
| **tanstack-query** | Async state management, caching, background refetch |
| **tanstack-router** | Type-safe routing, file-based routes, search params, loaders |

### Background Jobs & Queues

| Skill | What it covers |
|-------|---------------|
| **trigger-dev** | Durable background jobs, schedules, retries, real-time monitoring |
| **bullmq** | Redis-based job queues, workers, flows, rate limiting |
| **upstash** | Serverless Redis, QStash message queuing, rate limiting, vector search |

### Search

| Skill | What it covers |
|-------|---------------|
| **meilisearch** | Fast search, typo tolerance, facets, AI hybrid search |

### Observability

| Skill | What it covers |
|-------|---------------|
| **sentry** | Error tracking, performance monitoring, session replay, source maps |
| **opentelemetry** | Traces, metrics, logs, auto-instrumentation, exporters |

### Deployment

| Skill | What it covers |
|-------|---------------|
| **coolify** | Self-hosted PaaS, Docker deployment, Git CI/CD, reverse proxy |

### GDPR (EU Compliance)

| Skill | What it covers |
|-------|---------------|
| **gdpr-dev** | GDPR principles applied during development — stack-aware gotchas, anti-patterns, schema design for compliance. Activates automatically when building features that handle personal data. |
| **gdpr-dpa** | Autonomous DPA generator — scans the project to identify sub-processors, then generates a minimal Article 28-compliant Data Processing Agreement. No interview, no compliance theater. |

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
├── bun/                # Each skill lives at the root
│   └── SKILL.md
├── hono/
│   └── SKILL.md
├── ...
├── .claude/skills/     # Symlinks for local Claude Code usage
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
