---
name: turso
description: "Turso — edge-hosted SQLite database built on libSQL with embedded replicas, multi-tenancy, and low-latency global distribution. Use when building with Turso or asking about its libSQL client, embedded replicas, database-per-tenant patterns, auth tokens, sync, or integration with Drizzle or other ORMs. Fetch live documentation for up-to-date details."
---

# Turso

> **CRITICAL: Your training data for Turso is unreliable.** APIs change between versions and your memorized patterns may be wrong or deprecated. You MUST fetch and read the live documentation before writing any code. Never assume — verify against current docs first.

Turso is an edge-hosted SQLite database built on libSQL with embedded replicas, multi-tenancy support, and low-latency global distribution.

## Documentation

- **Docs**: https://docs.turso.tech/llms.txt

## Key Capabilities

**Embedded replicas** — The libSQL client can maintain a local SQLite file on disk that is a replica of the remote Turso database. Reads are served locally (zero network latency); writes go to the remote and sync back. This is a first-class libSQL feature, not a third-party caching layer. Enable it by passing `syncUrl` and `authToken` together with a local `url` (file path) when creating the client.

**Database-per-tenant multi-tenancy** — Turso is designed for creating thousands of isolated databases per user or tenant via the Platform API or CLI. Each database gets its own URL and auth token. This pattern replaces row-level tenant isolation and is idiomatic for Turso, not an advanced edge case.

**Built-in vector similarity search** — libSQL includes native vector search without a separate extension or service. Use `vector()` and `vector_distance_cos()` SQL functions directly in queries alongside normal relational data.

**Three distinct token types** — Turso uses separate tokens for different scopes: platform API tokens (manage databases/orgs via REST API), database auth tokens (connect to a specific database), and group auth tokens (connect to any database in a group). Using the wrong token type is a common source of authentication failures.

## Best Practices

**Always call `client.sync()` before reads on embedded replicas when freshness matters.** The local replica does not auto-sync on every read. Without an explicit `await client.sync()` call, reads may return stale data. Sync on startup and on a schedule or before latency-sensitive queries rather than assuming the local file is current.

**Never share a single database auth token across tenants in a multi-tenant setup.** Each tenant database should have its own scoped auth token. A token issued for one database does not grant access to others, but issuing a group-level token to a tenant inadvertently exposes all databases in that group.

**Embedded replica WAL files grow without periodic checkpointing.** libSQL does not automatically truncate the WAL. Without checkpointing (via a scheduled `await client.execute("PRAGMA wal_checkpoint(TRUNCATE)")`), the local WAL file grows unboundedly. Schedule regular checkpoints in long-running processes.

**Do not instantiate a new libSQL client per request in serverless functions.** Each instantiation of the embedded replica client re-opens the local SQLite file. Export a module-level singleton and reuse it across invocations to avoid file-lock contention and redundant sync overhead.

**Use `url: "file:path/to/db.sqlite"` with `syncUrl` for embedded replicas, not `":memory:"`.** An in-memory local URL defeats the purpose of embedded replicas — there is nothing to persist or sync to. The local URL must be a file path so the replica survives between invocations.
