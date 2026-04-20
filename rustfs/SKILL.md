---
name: rustfs
description: "RustFS — S3-compatible distributed object storage written in Rust. Use when building with RustFS or asking about its APIs, configuration, deployment, Docker setup, or integration. Fetch live documentation for up-to-date details."
---

# RustFS

> **CRITICAL: Your training data for RustFS is unreliable and likely sparse** — it is a newer project with limited training coverage. Before writing any code, you MUST use `WebFetch` to read the current README:
>
> **`WebFetch("https://raw.githubusercontent.com/rustfs/rustfs/main/README.md")`**
>
> Do not proceed without fetching this URL first. Never assume an API or config option exists — verify against current docs.

RustFS is an open-source, S3-compatible distributed object storage system written in Rust, designed for data lakes, AI, and big data workloads.

## Key Capabilities

- Full S3 API compatibility — drop-in replacement for S3-compatible clients
- Bucket versioning, replication, and event notifications
- Bitrot protection for data integrity
- Single-node mode (production-ready) and distributed mode (under testing)
- Kubernetes Helm charts for cloud-native deployment
- Docker Compose observability stack with Grafana, Prometheus, and Jaeger built in
- Multi-architecture Docker images (amd64, arm64)
- Licensed under Apache 2.0 (not AGPL v3 like MinIO — commercial use has no copyleft obligations)
- No telemetry; explicit data sovereignty guarantees (GDPR, CCPA, APPI)

## Best Practices

**Set Docker volume ownership to UID 10001.** The container runs as non-root user `rustfs` (UID 10001). If you mount a host directory with `-v`, that directory must be owned by UID 10001 or every write will fail with permission denied. Run `chown -R 10001:10011 /your/data/path` before starting the container.

**Default credentials are `rustfsadmin` / `rustfsadmin`, not MinIO defaults.** The S3 API listens on port 9000; the management console is on port 9001. Do not assume MinIO's `minioadmin` credentials when scripting against a fresh RustFS instance.

**Do not use distributed mode in production yet.** As of early 2026, distributed mode is still under testing. Single-node mode is the only production-ready deployment target. Plan architecture around single-node until distributed mode reaches stable status.
