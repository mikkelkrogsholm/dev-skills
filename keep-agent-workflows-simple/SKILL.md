---
name: keep-agent-workflows-simple
description: Prevent overengineered agent plans and enforce simple, reliable execution before creating tasks, goals, subagents, Kanban boards, queues, orchestration flows, or dependency DAGs in Codex, Hermes, OpenClaw, and similar systems. Use before planning or delegating work, when configuring an agent runtime or board, when resuming a workflow, and when diagnosing excessive cards, states, branches, dependencies, retries, polling, or speculative parallelism. Discover the installed platform's current native controls, configure authorized limits, distinguish hard enforcement from prompt-only guidance, and default to one outcome, low WIP, true dependencies, executable acceptance, bounded recovery, and explicit stop conditions.
---

# Keep Agent Workflows Simple

Read and apply this skill before planning. Model only the work needed to reach the current outcome. Do not use a board or DAG as a programming language for the agent's thoughts.

If the work changes code, also load `keep-code-simple` before planning when available.

## Write the execution contract first

Define:

- **Outcome:** one observable result.
- **Non-goals:** adjacent work excluded from this run.
- **Write scope:** files, records, services, or decisions that may change.
- **Acceptance evidence:** commands, artifacts, observations, or explicit decisions.
- **Owner:** one accountable agent or human.
- **Stop condition:** finish on evidence; stop on unauthorized scope expansion, unresolved human decisions, unsafe actions, or exhausted limits.

Do not start a persistent goal, create cards, or spawn children merely to discover this contract. Use a bounded read-only inspection first when needed.

## Select the lightest execution primitive

Choose in this order:

1. **Direct action:** one tool call, edit, or short answer.
2. **Deterministic script or code tool:** mechanical gather, filter, transform, or repeated operations.
3. **Single-agent task or goal:** one outcome that benefits from iterative work in the same session.
4. **Short-lived subagent:** independent reasoning or context isolation whose result the parent needs now.
5. **Durable board card:** work that must outlive the session, cross owners, wait for a human gate, or hand off a concrete artifact.
6. **DAG or managed flow:** several known tasks with true, non-obvious prerequisites or genuine parallel independence.

Use a list instead of a DAG for sequential work. Use a checklist inside one task when steps share an owner, scope, and acceptance. Choose one primary representation; do not mirror a simple sequence into both a board and a DAG.

## Discover and enforce current platform controls

Read [references/platform-discovery.md](references/platform-discovery.md) whenever the plan uses delegation, a goal loop, a board, a managed flow, retries, or runtime budgets.

Before planning:

1. Identify the running platform and installed version.
2. Inspect its local help, bundled instructions, config schema, and installed source before relying on memory.
3. Consult current official documentation when local material is insufficient.
4. Map the invariants below to controls the current version actually supports.
5. Configure authorized per-run, session, task, or board controls and verify that the platform accepted them.
6. Mark each invariant as **hard-enforced**, **soft-only**, or **unavailable**.
7. Compensate for soft or unavailable controls by reducing scope, WIP, delegation, and retries.

Never invent a config key or assume an old default. Keep product-specific syntax out of this skill. Prefer the installed version's schema over examples from another version.

Complete capability discovery before creating the board or execution graph. Do not turn runtime inspection into a planning card unless it is genuinely durable work with a separate owner and deliverable. If the installed runtime or schema cannot be inspected, stop with the exact unblock requirement; do not draft a hypothetical configured board.

Never choose numeric budgets from memory or convenience. Derive values from an explicit user or organization policy, verified bounded native defaults, measured task history, or a stated risk-based rationale. Until one of these exists, keep the invariant qualitative and mark it unresolved. Do not print or apply candidate keys or values before the current schema is verified.

Treat an explicit request to “set up this task/workflow using this skill” as authority to apply reversible, task-scoped controls inside the requested workflow. Ask before changing persistent global defaults, external systems, production state, billing, permissions, or unrelated boards.

## Enforce the stable invariants

- Keep one writer per overlapping file, record, or mutable surface.
- Keep WIP at one task per active agent and prefer one active writer overall.
- Keep delegation flat by default; add depth only for a demonstrated independent layer.
- Keep fan-out and the visible ready queue deliberately small.
- Set bounded turns, tool calls, time, cost, and retries when the platform exposes them.
- Retry only the smallest idempotent failed step.
- Retry only after the hypothesis, input, environment, or tool has changed.
- Preserve failure evidence and convert repeated failure into a visible blocked state.
- Require executable or observable acceptance before `Done`.
- Prefer completion events or durable handoffs over status-polling loops.
- Make cancellation sticky: cancelled work must not spawn new children.
- Preserve completed work when delivery fails; do not replay completed side effects.
- Apply backpressure rather than silently growing queues or spawning replacements.

If a runtime cannot enforce an important limit, state that clearly before execution. A prompt instruction is not a hard control.

## Inject the contract into every execution lane

Do not assume children, workers, resumed sessions, or compacted contexts have read this skill. Put the non-negotiable subset directly in every task or worker contract:

- outcome and non-goals;
- permitted read/write scope;
- one owner and expected artifact;
- acceptance evidence;
- retry and stop limits;
- exact blocked/escalation protocol; and
- prohibition on further delegation unless explicitly allowed.

On resume or handoff, reload the durable contract and current runtime limits before continuing.

## Keep Kanban operational

Use the smallest state model supported by the platform. A useful conceptual minimum is `Backlog`, `Ready`, `Doing`, `Blocked`, and `Done`; omit states that have no operational transition.

- Put one outcome, owner, deliverable, and acceptance check on each card.
- Split only when parts have different owners, outputs, prerequisites, write scopes, or verification.
- Do not create states for roles, tools, priority, review opinions, or every substep.
- Keep optional work in backlog, not in the active graph.
- Archive stale planning debris.
- Treat the board as an activity ledger; keep scheduling and retry policy in native runtime controls when available.

## Build only true dependency edges

Add `A -> B` only when B cannot start correctly until it receives a concrete output or verified state from A. Do not encode chronology, shared topic, review preference, or agent availability as a data dependency.

Start with the shortest critical path. Parallelize only when tasks have independent inputs, outputs, write scopes, and acceptance. Join branches as soon as their results are needed.

## Type blocks and bound recovery

Record a block as one of these stable categories, translated to the platform's current native vocabulary:

- **dependency:** wait for a named artifact or verified state;
- **needs-input:** require a human product or architecture decision;
- **capability:** require missing access, authentication, quota, permission, or tool support;
- **transient:** retry a narrow idempotent operation within its budget.

Do not retry `needs-input` or `capability` as if they were transient. After the same diagnosed failure reaches its limit, stop, retain evidence, state the exact unblock condition, and request the required action. Do not grow a recovery DAG.

Separate work completion from result delivery. If work completed but its notification or handoff failed, retry delivery within its own bound without repeating the work.

## Simplify before execution

Remove or merge:

- tasks unrelated to the current outcome;
- nodes sharing owner, scope, inputs, and acceptance;
- edges that are not true prerequisites;
- speculative branches and recovery paths;
- redundant coordinators and handoff-only nodes;
- overlapping writers;
- duplicate board and DAG representations; and
- polling tasks replaceable by completion events.

Stop simplifying when the smallest runnable contract remains. Do not create an elaborate review process to police a simple task.

## Report the guardrails and plan

Before execution, report briefly:

- selected primitive and why heavier options were rejected;
- active WIP, ownership, and write boundaries;
- acceptance and stop conditions;
- which limits are hard-enforced versus soft-only; and
- any persistent configuration change requiring approval.

Then present only the smallest runnable plan and start with the next active task. Show a DAG only when it clarifies real dependencies.

For dated provenance behind these evergreen rules, read [references/research-basis.md](references/research-basis.md) only when reviewing or evolving this skill.
