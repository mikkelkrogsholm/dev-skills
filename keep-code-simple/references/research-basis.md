# Research basis

Use this file only to review or evolve the skill. Keep the operational rules in `SKILL.md` evergreen and independent of product versions.

## Recent evidence reviewed

- OpenAI's current model guidance recommends lean non-repeating prompts, explicit autonomy and approval boundaries, bounded tool stages, retry and stop caps, representative evals, and multi-agent execution only for cleanly independent work: <https://developers.openai.com/api/docs/guides/latest-model>.
- The 2026-08-02 preregistered preprint *Prompt-Induced Waste in Large Reasoning Models* reports 4,643 valid runs across six models and two coding-agent harnesses. Requiring multiple approaches increased reasoning without corresponding correctness gains; explicit scope, acceptance, and stop conditions reduced waste: <https://arxiv.org/abs/2608.01347>.
- Ponytail's June 2026 releases applied one reuse/YAGNI-oriented ruleset across OpenClaw, Hermes, and subagents: <https://github.com/DietrichGebert/ponytail/releases>. Its review skill operationalizes removal of speculative features, preference for native facilities, and diff-scoped simplification: <https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md>.
- Hermes' focused simplification workflow treats simplification as a review of working changes rather than a general bug hunt or mandatory multi-agent ritual: <https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/software-development/software-development-simplify-code>.
- Agent-readable-code research and operational experience support explicit dependencies, vertical slices, accurate boundaries, deterministic verification, and tolerating local duplication when abstraction would increase indirection.

## Evidence limits

- Exact numerical limits are local policy choices, not universal scientific thresholds.
- Preprints and maintainer-reported savings are useful design evidence, not guaranteed outcomes.
- Fewer lines are not the objective. Preserve correctness, tests, security, accessibility, performance, and necessary error handling.
