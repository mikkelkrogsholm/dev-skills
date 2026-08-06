# Evergreen platform discovery

Read this file before configuring delegation, goals, boards, flows, retries, or budgets. Discover capabilities from the running installation; do not copy stale syntax from this reference.

## Use this source order

1. Identify the executable, platform, installed version, active profile, and configuration location.
2. Read local `--help`, bundled instructions, schemas, examples, diagnostics, and installed source for that exact version.
3. Read current official documentation and release notes when local material is incomplete.
4. Inspect the matching source tag or schema when documentation and runtime disagree.
5. Treat blogs, old prompts, remembered defaults, and config snippets from other versions as leads only.

Never invent a setting. Never silently substitute a similarly named control. Validate configuration with the platform's own parser, diagnostic command, dry run, status view, or observable behavior.

Finish this discovery before creating a board or DAG. If the executable, installed version, active schema, or target runtime cannot be located, stop and report the exact command, path, access, or user input required. Do not create a “runtime discovery” card as a substitute for an executable workflow.

Do not select concrete limits arbitrarily. Use, in order: explicit user or organization policy; verified bounded native defaults suitable for the task; measured history for comparable tasks; or a documented risk-based calculation. If none exists, leave the value unresolved and propose it separately from applied configuration. Never show candidate config keys from memory.

## Map invariants to capabilities

For each invariant, record:

| Invariant | Desired policy | Native control found | Scope | Verification | Status |
|---|---|---|---|---|---|
| Ownership/WIP | One writer per overlapping surface | Current native mechanism or none | Task/session/board/global | Current platform evidence | Hard/soft/unavailable |
| Delegation | Flat, small fan-out | Current depth/concurrency controls or none | Per run preferred | Inspect accepted limits | Hard/soft/unavailable |
| Budgets | Bounded turns/tools/time/cost | Current budget/timeout controls or none | Per task preferred | Trigger-safe dry run or status | Hard/soft/unavailable |
| Retry | Smallest idempotent step; diagnosed retry only | Current retry/circuit-breaker controls or none | Per operation/task | Observe terminal block | Hard/soft/unavailable |
| Completion | Evidence before done | Current quality gate/check mechanism or none | Per task/card | Run the named check | Hard/soft/unavailable |
| Blocking | Typed reason and exact unblock condition | Current state/metadata vocabulary or none | Per task/card | Inspect persisted state | Hard/soft/unavailable |
| Delivery | Do not repeat completed work | Current durable handoff/completion mechanism or none | Per run/task | Simulate or inspect failure path | Hard/soft/unavailable |

Keep this table brief in user-facing output. Its purpose is to prevent assumed enforcement.

## Apply platform-native semantics dynamically

### Codex

Inspect the current Codex instructions, available collaboration tools, task/goal interfaces, approval policy, and repository `AGENTS.md`. Use native task contracts, worktree isolation, acceptance commands, and available budgets. If the current runtime does not expose hard fan-out, retry, or cost caps to the agent, reduce delegation and state the limit as soft-only. Do not claim that `AGENTS.md` enforces runtime behavior.

### Hermes

Read the installed Hermes documentation and schema for direct tools, code execution, delegation, persistent goals, Kanban, worker lanes, blocking, quality gates, and auto-decomposition. Choose the lightest current primitive. Prefer manual decomposition when automatic decomposition would create unnecessary cards. Put critical worker rules in the actual worker/task contract rather than relying on optional skill loading. Use the installed version's native limit, block, and verification mechanisms; never assume their names or defaults.

### OpenClaw

Read the installed OpenClaw documentation and schema for tasks, subagents, managed flows, Workboard, concurrency, depth, timeout, retry, completion delivery, cancellation, and backpressure. Start with a plain task and escalate only when durable coordination is required. Prefer completion events to polling and narrow idempotent retries to replaying a flow. Use the installed version's accepted controls; never assume their names or defaults.

### Other runtimes

Apply the same invariants. If no native control exists, choose a simpler topology, inject the contract into every child, monitor observable progress, and stop earlier. Report the control as soft-only.

## Respect configuration authority

- Apply reversible task-, run-, session-, or board-scoped controls when the user asked to set up that workflow.
- Ask before changing persistent global defaults, shared boards outside scope, external services, production, billing, access, permissions, or security posture.
- Show the intended persistent change, current value, new value, scope, and rollback before applying it.
- Re-read the accepted runtime state after mutation; do not assume the write succeeded.

## Preserve controls across boundaries

Copy the minimal execution contract into child prompts, cards, handoffs, and resumed sessions. Re-establish current limits after compaction, restart, migration, or version upgrade. Re-run capability discovery when the installed version changes.
