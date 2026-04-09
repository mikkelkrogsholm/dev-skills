---
name: bullmq
description: "BullMQ — Redis-based distributed job and message queue for Node.js with workers, schedulers, flows, and rate limiting. Use when building with BullMQ or asking about its queues, workers, job configuration, repeatable jobs, flow producers, or Redis connection setup. Fetch live documentation for up-to-date details."
---

# BullMQ

BullMQ is a Redis-based distributed job and message queue for Node.js with workers, schedulers, flows, and built-in rate limiting.

## Documentation

- **Docs**: https://docs.bullmq.io/llms.txt

## Quick Start

```typescript
import { Queue, Worker } from 'bullmq';

const connection = { host: 'localhost', port: 6379 };

// 1. Create a queue
const queue = new Queue('my-queue', { connection });

// 2. Add a worker with a processor
const worker = new Worker('my-queue', async (job) => {
  console.log(`Processing ${job.name}`, job.data);
  return { success: true };
}, { connection, removeOnComplete: { count: 1000 }, removeOnFail: { count: 5000 } });

// 3. Add jobs
await queue.add('email', { to: 'user@example.com', subject: 'Hello' });

// 4. Graceful shutdown
process.on('SIGTERM', async () => {
  await worker.close();
  await queue.close();
});
```

## Key Capabilities

- **Flow Producers**: model parent-child job dependencies natively. A parent job only runs after all its children complete -- no custom orchestration needed.
- **Sandboxed Processors**: run worker processors in isolated child processes (`processor: './worker.js'`) for crash isolation without separate process management.
- **Job Schedulers**: built-in repeating job scheduler with cron and interval strategies via `queue.upsertJobScheduler()`. Replaces the deprecated `repeat` option from v5.16+.
- **Global Rate Limiting**: enforce a max-jobs-per-duration limit via the `limiter` option on the `Worker` constructor (`{ limiter: { max: 10, duration: 1000 } }`).
- **Built-in Metrics**: track processed/failed counts and Prometheus-compatible metrics without a separate metrics library.

## Best Practices

- **Always close connections explicitly**: `Queue`, `Worker`, and `QueueEvents` each hold their own Redis connection. Call `.close()` on all three on shutdown or you will leak connections and block process exit.
- **Use `QueueEvents` for cross-process event listening**: the `Worker` emits events only within its own process. To listen to completed/failed events from a different process (e.g. an API server), instantiate a `QueueEvents` object -- not a `Worker`.
- **Use `upsertJobScheduler()` for repeating jobs**: the old `repeat` option on `queue.add()` is deprecated in v5.16+. Use `queue.upsertJobScheduler()` to avoid duplicate scheduler entries on restart.
- **Set `removeOnComplete` and `removeOnFail`**: by default completed and failed jobs accumulate in Redis indefinitely. Always configure auto-removal (e.g. `{ count: 1000 }`) to prevent unbounded memory growth.
- **Do not share a single `IORedis` connection**: BullMQ uses blocking Redis commands that require dedicated connections. Pass a connection config object (not a shared `IORedis` instance) so each class creates its own connection.
