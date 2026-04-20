# Research behind each rule

Citations and evidence strength for every rule in the linter. Use when explaining *why* a recommendation matters.

**Not every rule is equally well-supported.** Some are grounded in empirical studies; others are operational heuristics calibrated to current agent tooling. The evidence column below is honest about which is which.

| Rule | Evidence strength | Evidence type | Threshold confidence |
|---|---|---|---|
| AR003 generic names | **strong** | controlled empirical study + tool-behavior evidence | high |
| AR006 accurate docs/types | **strong** | controlled empirical study (docs) + constrained-generation research (types) | high |
| AR007 verification affordances | **strong** | vendor guidance (Anthropic, Cursor) + agent-spiral case studies | medium-high |
| AR002 near-duplicate blocks | **moderate** | vendor first-hand reports + failure-trajectory analysis | medium |
| AR004 metaprogramming | **moderate** | agent postmortems + multi-platform failure patterns | medium |
| AR001 file size (800 lines) | **heuristic** | lost-in-the-middle position bias + vendor reports; **exact number is tunable** | low-medium |
| AR008 long lines (400 chars) | **heuristic** | tool-output formatting reports; **exact number is tunable** | low |
| AR005 inheritance depth (>3) | **heuristic** | case studies + extrapolation; **treat as a review prompt, not a hard rule** | low |
| AR011 barrel re-export files | **moderate** | vendor guidance (Aider's `/add` tips, Cursor rule docs) + mechanistic reasoning | medium |

**What "heuristic" means here:** the direction of the rule is right (deeper inheritance is harder for agents to reason about than shallower), but the specific threshold is an operational choice. Teams should tune via `--config`.

---

## AR001 — File size

**Claim:** Files over ~800–1000 lines regularly fail apply-model merges, and mid-file content is used far worse than content near the start or end of the context.

- **Lost in the Middle: How Language Models Use Long Contexts** — Liu et al., 2023. U-shaped position bias: evidence placed in the middle of a long context is retrieved far worse than evidence at the start or end. GPT-3.5 can score below its own closed-book baseline when the needle sits mid-context. https://arxiv.org/abs/2307.03172
- **Morph LLM — Common apply-model errors.** First-hand vendor report: merges fail predictably on files over ~1000 lines; generated output gets truncated or garbled. https://www.morphllm.com/common-errors/error-editing-file
- **Aider — Edit errors troubleshooting.** `str_replace`-style edits fail when surrounding lines aren't unique, and the probability of duplicates rises with file size. https://aider.chat/docs/troubleshooting/edit-errors.html

**Practical implication:** target files under 800 lines. Break up by responsibility *inside* a feature directory, not by cross-feature layer.

---

## AR002 — Near-duplicate blocks

**Claim:** Repeated blocks of code defeat exact-match string-replacement edits, which most AI coding tools use as their primary edit primitive.

- **Aider — Edit errors.** Explicit: if the same snippet appears in multiple places, the model can't uniquely target one. https://aider.chat/docs/troubleshooting/edit-errors.html
- **Understanding Code Agent Behaviour: Success and Failure Trajectories** — Ma et al., 2025. Repeated edits to the same region dominate syntax-error failure modes. https://arxiv.org/html/2511.00197v1

**Practical implication:** factor repeated error handling, validation, and logging into a single helper *at the seam*, not by copy-paste. Inside a single leaf function, a little duplication is fine.

---

## AR003 — Generic names

**Claim:** Names are retrieval cues for learned patterns. Descriptive names improve model comprehension dramatically; misleading names hurt more than random ones.

- **When Names Disappear: Revealing What LLMs Actually Understand About Code** — 2025. Removing or obfuscating identifiers drops GPT-4o class-summarization accuracy from 87.3% → 58.7%; execution-prediction accuracy drops 20–30 percentage points. https://arxiv.org/html/2510.03178v1
- **How Does Naming Affect LLMs on Code Analysis Tasks?** — 2024. Method/function names have the largest effect; variable names moderate; call-site names least. **Shuffled (misleading) names are worse than random names** — an incorrect name is an actively wrong oracle. https://arxiv.org/html/2307.12488v5
- **Aider — Repository map.** Repo-map retrieval works via tree-sitter + PageRank over symbol references. Well-named, widely-referenced symbols surface automatically. https://aider.chat/docs/repomap.html

**Practical implication:** avoid banlist names. Rename on refactor — stale names are load-bearing and wrong.

---

## AR004 — Metaprogramming / dynamic dispatch

**Claim:** Code that can't be traced with grep or a simple AST walk is code the agent invents around.

- **Coding Agents Are "Fixing" Correct Code** — ETH SRI Lab, 2025. Documented an agent literally asking itself "has `self.data.get_str_vals` been monkey-patched?" before producing a wrong fix. https://www.sri.inf.ethz.ch/blog/fixedcode
- **When Coding Agents Spiral Into 693 Lines of Hallucinations** — Surge HQ, 2025. Gemini imagined inheritance relationships that didn't exist; produced 693 lines of patches over 39 turns without realizing its mental model was wrong. https://surgehq.ai/blog/when-coding-agents-spiral-into-693-lines-of-hallucinations
- **9 Critical Failure Patterns of Coding Agents** — DAPLab, Columbia, 2026. Reflection, metaprogramming, and heavy DI rank among the top failure triggers across Claude Code, Cursor, and Devin. https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html

**Practical implication:** prefer composition and explicit calls. If you use decorators, keep them declarative (don't rewrite behavior). If you use DI, wire it at edges, not throughout.

---

## AR005 — Deep inheritance

**Claim:** Inheritance chains >3 levels deep cause agents to fabricate method resolution paths.

- Surge HQ case study (linked above): Gemini invented `super()` calls into nonexistent parents.
- **Rigorous Evaluation of Coding Agents on SWE-Bench** — ACL 2025. ~52% of SWE-bench failures classified as "incorrect implementation"; a meaningful fraction involve wrong assumptions about inherited behavior. https://aclanthology.org/2025.acl-long.189.pdf

**Practical implication:** flatten hierarchies. Composition with explicit delegation is easier for both humans and agents to trace.

---

## AR006 — Typed boundaries, accurate comments

**Claim:** Type annotations reduce hallucination at module seams; incorrect documentation is worse than no documentation.

- **Testing the Effect of Code Documentation on LLM Code Understanding** — 2024. Incorrect docstrings crashed GPT-3.5 task success to 22.1% (from baseline); GPT-4 to 68.1%. Missing or partial docstrings showed no significant effect. https://arxiv.org/html/2404.03114v1
- **Type-Constrained Code Generation with Language Models** — 2025. Explicit type annotations measurably improve constrained generation and retrieval of the right APIs. https://arxiv.org/pdf/2504.09246
- **Morph LLM — observed vendor pattern.** A single central types file prevents dozens of wrong assumptions at module seams.

**Practical implication:** annotate public boundaries. Delete stale docstrings; don't "update later."

---

## AR007 — Test colocation / verification affordances

**Claim:** Agents without an in-loop verification signal hallucinate into long wrong-patch spirals.

- **Best Practices for Claude Code** — Anthropic. "If you can't verify it, don't ship it" framed as the single highest-leverage rule. https://code.claude.com/docs/en/best-practices
- Surge HQ 693-line spiral (linked above): no feedback signal until human review, which arrived after 39 wrong turns.

**Practical implication:** colocate tests (`foo.ts` + `foo.test.ts`) so agents find and run them without exploration. Provide one command that runs everything.

---

## AR011 — Barrel re-export files

**Claim:** Files whose only content is `export * from` / `export { foo } from` add a grep hop between consumers and the defining symbol, and break tree-shaking.

- **Aider — Tips.** "Only `/add` files you actually intend to edit; unrelated files distract and confuse the LLM." Barrel files force the agent to follow an extra hop before reaching the real source. https://aider.chat/docs/usage/tips.html
- **Cursor — Rules docs.** Explicit recommendation to reference *defining* files rather than re-exports in rules and examples. https://cursor.com/docs/rules
- Mechanistic: an agent asked "where is `createUser` defined?" greps and finds the barrel first. It has to open the barrel, read the `from` clause, then grep again. On a large tree this doubles tool-call count before the agent has even started working.

**Practical implication:** import from the defining file. Keep barrels only where a tool requires them (Drizzle's `db/schema/index.ts`, package entry points).

---

## AR008 — Long lines

**Claim:** Lines longer than ~400 characters break ReAct-formatted tool outputs and burn agent context.

- **Why Your Coding Agent Should Use ripgrep** — CodeAnt, 2025. Long single lines (minified bundles, inline SVGs) cause ripgrep output to overflow the agent's parsing, leading to dropped matches. https://www.codeant.ai/blogs/why-coding-agents-should-use-ripgrep

**Practical implication:** keep minified and generated content out of the source tree (put it in `dist/`, `build/`, ignore via `.gitignore`). Wrap long literals.

---

## Additional context (not tied to a single rule)

- **SweRank: Benchmarking Code-Localization for Software Issue Resolution** — 2025. File localization is the #1 bottleneck on SWE-bench across all agent platforms. https://arxiv.org/pdf/2505.07849
- **cAST: Chunking by Abstract Syntax Tree** — 2025. AST-aware chunking outperforms fixed-size chunking by +4.3 Recall@5 on RepoEval and +2.67 Pass@1 on SWE-bench. Implies self-contained functions/classes are what retrievers return best. https://arxiv.org/html/2506.15655v1
- **SWE-Bench Pro** — 2025. Top frontier models still under 45% Pass@1 on multi-file edits; failures cluster on semantic correctness across files. Reinforces "colocate what changes together." https://arxiv.org/abs/2509.16941
- **Your AI Agent Doesn't Care About Your README** — DAPLab, 2026. Agents need "where things live and what rules to follow," not project history. Prose READMEs can actively mislead. https://daplab.cs.columbia.edu/general/2026/03/31/your-ai-agent-doesnt-care-about-your-readme.html
- **Best Practices for Claude Code**, Anthropic. https://code.claude.com/docs/en/best-practices
- **How Anthropic teams use Claude Code** (PDF). https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf
- **Cursor — Best practices for coding with agents**. https://cursor.com/blog/agent-best-practices
- **GitHub — How to write a great agents.md (lessons from 2500+ repositories)**. https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/
- **Cognition — Devin 2025 Performance Review**. https://cognition.ai/blog/devin-annual-performance-review-2025
- **Zed — On Programming with Agents**. https://zed.dev/blog/on-programming-with-agents
