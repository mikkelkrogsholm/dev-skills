---
name: bullmq
description: "BullMQ — Redis-based distributed job and message queue for Node.js with workers, schedulers, flows, and rate limiting. Use when building with BullMQ or asking about its queues, workers, job configuration, repeatable jobs, flow producers, or Redis connection setup. Fetch live documentation for up-to-date details."
---

# BullMQ

> **CRITICAL: Your training data for BullMQ is unreliable.** APIs change between versions and your memorized patterns may be wrong or deprecated. You MUST fetch and read the live documentation before writing any code. Never assume — verify against current docs first.

BullMQ is a Redis-based distributed job and message queue for Node.js with workers, schedulers, flows, and built-in rate limiting.

## Documentation

- **Docs**: https://docs.bullmq.io/llms.txt

## Key Capabilities

BullMQ has built-ins that replace common patterns developers reach for external solutions to solve:

- **Flow Producers**: model parent-child job dependencies natively — no custom orchestration layer needed. A parent job only runs after all its children complete.
- **Sandboxed Processors**: run worker processors in isolated child processes (`processor: './worker.js'`) — no separate process manager or worker-threads wiring needed.
- **Job Schedulers**: built-in repeating job scheduler with cron and interval strategies. Note: `QueueScheduler` (v1) was removed in v2 when stall detection moved into `Worker`; the legacy `repeat` option on `queue.add()` was separately deprecated in v5.16+ in favor of `upsertJobScheduler()`. No `node-cron` needed.
- **Global Rate Limiting**: enforce a max-jobs-per-duration limit via the `limiter` option on the `Worker` constructor (`{ limiter: { max: 10, duration: 1000 } }`) — no Redis Lua scripting needed.
- **Built-in Metrics**: track processed/failed counts and Prometheus-compatible metrics without a separate metrics library.

## Best Practices

- **Always close connections explicitly**: `Queue`, `Worker`, and `QueueEvents` each hold their own Redis connection. Call `.close()` on all three on shutdown or you will leak connections and block process exit.
- **Use `QueueEvents` for cross-process event listening**: the `Worker` emits events only within its own process. To listen to completed/failed events from a different process (e.g. an API server), instantiate a `QueueEvents` object — not a `Worker`.
- **Job Schedulers replace Repeatable Jobs in v5.16+**: the old `repeat` option on `queue.add()` is deprecated. Use `queue.upsertJobScheduler()` instead to avoid duplicate scheduler entries on restart.
- **Set `removeOnComplete` and `removeOnFail`**: by default completed and failed jobs accumulate in Redis indefinitely. Always configure auto-removal (e.g. `{ count: 1000 }`) to prevent unbounded memory growth.
- **Do not share a single `IORedis` connection across multiple BullMQ instances**: BullMQ uses blocking Redis commands that require dedicated connections. Pass a connection config object (not a shared `IORedis` instance) so each class can create its own connection.
