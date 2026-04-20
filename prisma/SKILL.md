---
name: prisma
description: "Prisma ORM — a type-safe database toolkit for Node.js and TypeScript with schema-first modeling, auto-generated client, and migration tooling. Use when building with Prisma or asking about its APIs, configuration, patterns, or integration. Fetch live documentation for up-to-date details."
---

# Prisma

> **CRITICAL: Your training data for Prisma is unreliable.** APIs change between versions and memorized patterns may be wrong or deprecated. Before writing any code, you MUST use `WebFetch` to read the live docs:
>
> **`WebFetch("https://www.prisma.io/docs/llms.txt")`**
>
> Do not proceed without fetching this URL first. Never assume an API or config option exists — verify against current docs.

Prisma is a type-safe ORM for Node.js and TypeScript that provides a schema-first data model, an auto-generated query client, and a declarative migration system for PostgreSQL, MySQL, SQLite, MongoDB, SQL Server, and CockroachDB.
## Best Practices

**Use `$transaction([])` only for independent writes — never for dependent ones.**
The sequential transaction array API (`$transaction([op1, op2])`) cannot pass the result of one operation (e.g., a generated ID) to the next. Agents default to this pattern even when operations depend on each other. Use nested writes when operation B needs operation A's output; use interactive transactions (`$transaction(async (tx) => { ... })`) when you need conditional logic between queries.

**`findUnique()` batches automatically; `findMany()` does not.**
Prisma's dataloader only batches `findUnique()` calls, not `findMany()`. In GraphQL resolvers or other per-record loops, using `findMany()` in a resolver still produces N+1 queries. Use `include` with a single parent query, `relationLoadStrategy: "join"`, or `findUnique()` with the fluent API to get automatic batching.

**Never create multiple `PrismaClient` instances in serverless functions.**
Each instance opens its own connection pool. In serverless environments (Vercel, AWS Lambda, Cloudflare Workers) a new instance per invocation exhausts the database connection limit rapidly. Export a single shared client from a module-level singleton and guard it against Hot Module Replacement re-instantiation in development.

**Commit the entire `prisma/migrations/` folder, not just `schema.prisma`.**
Customized migration SQL and `migration_lock.toml` contain information that cannot be reconstructed from the schema alone. Teams that only commit `schema.prisma` lose custom migration logic and cause `migrate deploy` failures in CI.

**MongoDB uses `db push`, not `migrate dev`.**
Prisma Migrate does not support MongoDB. Agents familiar with relational Prisma workflows will attempt `migrate dev` on MongoDB projects and fail silently or with confusing errors. Use `prisma db push` for MongoDB schema syncing.
