---
name: surrealdb
description: "SurrealDB — multi-model database supporting document, graph, relational, key-value, time-series, and vector search in a single engine using SurrealQL. Use when building with SurrealDB or asking about schema design (schemafull vs schemaless), SurrealQL queries, graph relations with RELATE, live queries, full-text search, JS/TS SDK setup, namespace and database hierarchy, record IDs, authentication with DEFINE ACCESS, or connecting with WebSocket vs HTTP. Fetch live documentation for up-to-date details."
---

# SurrealDB

SurrealDB is a multi-model database that handles document, graph, relational, key-value, time-series, and vector search workloads in a single engine, queried via SurrealQL — a SQL-like language with graph traversal, record links, live queries, and schema enforcement built in.

## Documentation

- **Docs**: https://surrealdb.com/docs/llms.txt

## Key Capabilities

**Multi-model in one engine** — A single SurrealDB instance handles relational queries, graph traversal, document storage, key-value access, time-series, and vector similarity search. You do not need a separate graph DB, search engine, or cache alongside it.

**SurrealQL — SQL with graph and document extensions** — The query language looks like SQL but adds native graph traversal (`->`, `<-`), record links (fetch related records inline), `SELECT VALUE` for flat arrays, `FETCH` for eager loading of linked records, and `LIVE SELECT` for real-time streaming. Treating it as plain SQL will produce incorrect queries.

**RELATE for graph edges** — The `RELATE` statement creates a typed edge record between two nodes. Edges are stored in their own table with `in` and `out` fields, can carry arbitrary data, and support bidirectional traversal natively. This replaces JOIN tables and foreign keys for connected data.

**Live queries over WebSocket** — `LIVE SELECT` and the SDK `.live()` method push change notifications (CREATE, UPDATE, DELETE) to subscribers in real time. The underlying transport must be WebSocket; HTTP connections do not support live queries.

**Schemafull and schemaless tables** — Tables can be defined as `SCHEMAFULL` (strict enforcement, undefined fields are rejected) or `SCHEMALESS` (any fields accepted). Both modes coexist in the same database. Schema is defined per-table using `DEFINE TABLE` and `DEFINE FIELD`.

**DEFINE ACCESS for record-level auth** — SurrealDB has built-in authentication at root, namespace, database, and record levels. `DEFINE ACCESS ... TYPE RECORD` with `SIGNUP` and `SIGNIN` clauses lets you implement custom auth logic (bcrypt password hashing, role checks) entirely in SurrealQL without an external auth service.

## Best Practices

**Always call `db.use()` after connecting — namespace and database are not set by the connection URL alone.** The JS/TS SDK connects to the RPC endpoint and then requires a separate `.use({ namespace, database })` call before any query will succeed. Omitting this step causes queries to fail with a "no namespace or database selected" error. Set namespace and database immediately after `await db.connect(url)`.

```typescript
const db = new Surreal();
await db.connect("ws://127.0.0.1:8000/rpc");
await db.use({ namespace: "myapp", database: "production" });
```

**Record IDs are typed values, not plain strings — queries must use the full `table:id` form.** A record with ID `person:john` cannot be fetched with just `"john"`. In SurrealQL, write `SELECT * FROM person:john`. In the SDK, pass the full record ID string or use `new RecordId("person", "john")`. Passing only the identifier part silently queries a different or non-existent record.

**Live queries require a WebSocket connection, not HTTP.** Connect with `ws://` or `wss://` (not `http://`) when using `.live()` or `LIVE SELECT`. Using an HTTP endpoint returns an error or falls back silently depending on SDK version. Switch the protocol in the connection URL before enabling live queries.

**`RELATE` creates a new edge table automatically — do not pre-create it as a regular table.** Running `RELATE person:alice->follows->person:bob` creates a `follows` edge table with `in`, `out`, and `id` fields. If you first define `follows` as a normal `DEFINE TABLE follows` without `TYPE RELATION`, the subsequent `RELATE` will fail or produce incorrect records. Define edge tables explicitly only if you need to add field-level schema enforcement: `DEFINE TABLE follows TYPE RELATION IN person OUT person`.

**Writing undefined fields to a SCHEMAFULL table silently discards them in older versions, but raises an error in SurrealDB 3.0+.** Do not assume undefined fields will be stored or ignored consistently across versions. In schemafull mode, define every field you intend to write with `DEFINE FIELD`. If you need to insert a struct that may contain extra fields, filter it first or use `SCHEMALESS` mode deliberately.

**`SELECT VALUE` returns a flat array, not an array of objects — it only works for a single un-nested field.** Using `SELECT VALUE name FROM person` returns `["Alice", "Bob"]` while `SELECT name FROM person` returns `[{ name: "Alice" }, { name: "Bob" }]`. Attempting `SELECT VALUE name, age FROM person` is invalid syntax. Use `SELECT VALUE` only when you need a plain scalar list, and use `SELECT` (with field names or `*`) when you need structured records.

**Use `FETCH` to eager-load linked records rather than making separate queries.** When a field stores a record link (e.g., `author: person:alice`), a plain `SELECT` returns only the ID reference. Adding `FETCH author` at the end of the query replaces that ID with the full author record inline — no N+1 queries needed. This applies to nested links too: `FETCH author, author.department` traverses multiple levels in a single query.
