# Research basis

Use this file only to review or evolve the skill. It records dated provenance; it must not freeze current configuration syntax or defaults into the operational workflow.

## Recent primary evidence reviewed

- Hermes added outcome, verification, constraints, boundaries, and stop conditions to persistent goals: <https://github.com/NousResearch/hermes-agent/commit/2ba1cfeb2e28c77a3ae2323772e5a6bca43844cb>.
- Hermes moved critical Kanban worker behavior into injected runtime guidance when optional skill loading proved unreliable: <https://github.com/NousResearch/hermes-agent/commit/84e1d31e5442eeff0bfcf1c2ffab6acf7fe95f45>.
- Hermes introduced typed block handling and loop breaking: <https://github.com/NousResearch/hermes-agent/commit/5b5c79a8ef4317146b0db7cc2bbb7495c1748e63>.
- Hermes bounded protocol retries and added deterministic quality gates before model judgment: <https://github.com/NousResearch/hermes-agent/commit/52cafa6f8e3e8cec6d3528b739380d4442a71cf4> and <https://github.com/NousResearch/hermes-agent/commit/6e041d524439b69ddfec73398816f8a7b01edfa0>.
- OpenClaw's official subagent and retry guidance emphasizes bounded depth/concurrency, completion events, and retrying the current idempotent operation rather than the whole flow: <https://docs.openclaw.ai/tools/subagents> and <https://docs.openclaw.ai/concepts/retry>.
- OpenClaw implemented durable completion delivery, bounded retry, visible blocked results, and backpressure: <https://github.com/openclaw/openclaw/commit/d9393bd3cbe179c1145a20ba50906b2ac11dbac2>.
- OpenClaw constrained Workboard dispatch and fixed operational failure on a 213-card board: <https://github.com/openclaw/openclaw/pull/100174> and <https://github.com/openclaw/openclaw/pull/118848>.
- OpenClaw terminated repeated critical tool loops after one recovery opportunity: <https://github.com/openclaw/openclaw/pull/118647>.
- OpenAI's current model guidance recommends explicit autonomy boundaries, bounded tool stages, stop/retry limits, concise instructions, evidence-based evals, and multi-agent work only for cleanly independent streams: <https://developers.openai.com/api/docs/guides/latest-model>.
- The 2026-08-02 preregistered preprint *Prompt-Induced Waste in Large Reasoning Models* supports explicit scope, acceptance, and stopping conditions over prompts requesting many approaches: <https://arxiv.org/abs/2608.01347>.

## Evidence limits

- Native capabilities and configuration schemas change. Always inspect the installed version.
- Official implementation evidence shows useful mechanisms, not universal optimal numeric defaults.
- Community failure reports motivate guardrails but do not prove root cause.
- Prompt-only constraints can be lost, ignored, or omitted from child contexts; use runtime enforcement when available.
