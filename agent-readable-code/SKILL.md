---
name: agent-readable-code
description: "Principles and a linter for writing code that AI coding agents can read and modify correctly. Use when writing, refactoring, reviewing, or structuring code that will be maintained partly by AI agents (Claude Code, Cursor, Copilot, Aider, Devin). Also use when the user asks about agent-friendly code, AI-friendly architecture, how to structure a repo for AI maintenance, why agents fail on certain codebases, whether SOLID/DRY still apply with AI, or wants to audit an existing codebase for AI-readability. Applies proactively when making naming, file-organization, abstraction, or dependency choices in code the user is likely to maintain with agents — even if they don't explicitly ask for agent-friendly output. Ships with a zero-dependency linter (scripts/lint.py) that flags concrete anti-patterns."
---

# Agent-Readable Code

Research-informed principles for writing code that AI coding agents comprehend and modify correctly, plus an advisory linter that flags the most common anti-patterns.

Humans get lost in **complexity**. Agents get lost in **indirection**. Classical principles like SOLID and DRY were calibrated for human readers juggling cognitive load; several of them invert when the reader is an agent with a limited context window navigating by grep and file reads alone.

**The underlying heuristic:** write so that someone grepping a single file can act correctly without reading the rest of the repo.

**A note on evidence:** some of these practices are well-supported by controlled studies (naming, accurate documentation, verification loops). Others are operational heuristics whose *direction* is well-motivated but whose *thresholds* are tunable. The evidence strength for each rule is documented in [references/research.md](references/research.md) so you can apply judgment rather than follow rules blindly.

For longer before/after examples, see [references/patterns.md](references/patterns.md). For the linter, see [scripts/README.md](scripts/README.md).

---

## The six practices

Each practice lists the failure mode it prevents, the pattern to apply, and the lint rule that detects violations.

### 1. Name for localization (`AR003`)

Agents localize code by grepping names. Names are retrieval cues, not just labels — obfuscating them drops model comprehension accuracy from ~87% to ~59% in controlled studies. **A misleading name is worse than a random one**, because the agent confidently acts on the wrong mental model.

- Use domain-specific names: `chargeCustomerAndEmitReceipt` beats `process`.
- Avoid banlist names (`Manager`, `Service`, `Helper`, `Handler`, `Util`, `process`, `handle`, `doStuff`, single-letter vars outside tight loops).
- Avoid dumping-ground files (`utils.py`, `helpers.ts`, `misc.py`, `common.js`).
- When refactoring, **rename aggressively**. Stale names lie.

### 2. Vertical slices over horizontal layers (architecture-level)

The dominant systemic failure across all agent platforms: a feature that spans controller + service + middleware + trigger + background job. The agent fixes three of five touchpoints and ships a subtle bug. Colocate a feature's code, types, and tests in one directory the agent can load as a single coherent unit.

This isn't directly lintable, but shows up as a pattern through `AR007` (scattered tests) and `AR003` (layer-named files like `controllers/`, `services/` full of generic class names).

### 3. Keep files small and unique (`AR001`, `AR002`, `AR008`)

- **Files > ~800 lines** regularly fail apply-model merges; mid-file content is used far worse than content at the top or bottom (the "lost in the middle" effect).
- **Near-duplicate blocks** (copy-pasted error handling, repeated boilerplate) defeat exact-match string replacement — Claude Code's `str_replace` fails when surrounding lines aren't unique. Deduplicate at seams; tolerate duplication inside leaves.
- **Lines > 400 chars** (minified, generated, long string literals) break agent tool output formatting and burn context. Keep generated files out of the tree or in clearly-named `dist/` / `build/` dirs.

### 4. Static, explicit dependencies (`AR004`, `AR005`)

Code the agent can't trace with grep or a simple AST walk is code the agent hallucinates around. That includes:

- Metaprogramming: `__getattr__`, `eval`, `exec`, `importlib.import_module`, JS `Proxy`, `Reflect`, runtime monkey-patching.
- **Magic-string dispatch**: `registerHandler("user.created", ...)` spread across 40 files, or event buses keyed by string. Agents can't trace a string across the repo the way they trace a typed reference. Prefer a discriminated union + one exhaustive `switch`, or a single registry file imported explicitly by consumers.
- Deep inheritance chains (>3 levels) — agents fabricate method resolution paths that don't exist.
- Decorator stacks that rewrite behavior silently.
- Heavy dependency injection where control flow is invisible to grep.
- Barrel re-exports (`export * from './foo'` files that contain nothing else). They add a grep hop and break tree-shaking. Consumers should import from the defining file.

Prefer composition, explicit imports/exports, and direct function calls. Static code graphs are what retrievers (Aider's repo-map, Cursor's embeddings, Claude Code's grep loop) actually traverse.

### 5. Types and accurate comments at boundaries (`AR006`)

- Typed public signatures anchor the agent against fabrication. A single central types file measurably reduces hallucination at module seams.
- **Wrong docstrings are worse than missing ones.** In controlled tests, incorrect documentation crashed model success rates far below baseline; missing documentation had no effect.
- Only comment the *why* (hidden constraint, past incident, non-obvious invariant). The code already shows the *what*. A stale comment is a confidently-wrong oracle.

### 6. Verification affordances (`AR007`)

An agent without a feedback loop hallucinates into spirals (documented case: 693 lines of wrong fixes over 39 turns). Every feature should have a way the agent can verify its own change without human help:

- Tests colocated with source files (`foo.ts` + `foo.test.ts`), not siblings in a distant `tests/` dir.
- A single bash command that runs lint + typecheck + tests.
- Type errors that fail loudly at the edit site, not at runtime.

"If you can't verify it, don't ship it" is the highest-leverage rule in every AI coding tool vendor's docs.

### 7. Determinism and injectable side effects

The same failure pattern that makes verification loops fragile: non-determinism. Agents cannot debug a test that fails 1-in-10 runs — they retry until context runs out, then either disable the test or declare success.

- **Seed all randomness.** Frozen IDs, seeded `Math.random`, `faker.seed()`. UUID-in-snapshots is a near-guaranteed flake source.
- **Freeze time in tests.** Never let a test depend on `new Date()` or `time.time()` without an injected clock.
- **Pass `clock`, `fetch`, `logger`, `env`, `db` as arguments** to functions that need them. A function whose signature reveals its side effects is one an agent can test; a function that reaches into globals for `process.env` is one the agent will quietly call wrong.

### 8. Language-specific patterns that close hallucination surface

General principles above apply everywhere. These are idioms per language that have concrete agent-readability wins and that the linter can't fully police.

**Python:**
- **`__all__` on every module** that has public exports. It's the one signal Python has for "import this, not that" — agents otherwise import private helpers and create coupling you didn't intend.
- **`slots=True` on dataclasses** when you don't need dynamic attributes. An agent writing `user.foo = bar` on a slotted dataclass hits `AttributeError` immediately; on a normal class it silently succeeds and the bug surfaces three edits later.
- **`frozen=True`** for value objects. Prevents an agent from mutating what it thinks is immutable.

**TypeScript:**
- **Branded types for IDs**: `type UserId = string & { readonly __brand: 'UserId' }`. Agents routinely swap `userId` and `orgId` when both are plain `string`; branded types make the swap a compile error.
- **Discriminated unions over magic strings**: `type Event = { kind: 'created'; userId: UserId } | { kind: 'deleted'; userId: UserId }` — the compiler enumerates cases and agents can't invent a variant.
- **`as const` on literal tuples and records** so types narrow to the literal. Widening to `string` throws away information the agent needs.
- **Infer from one source of truth**: `z.infer<typeof Schema>`, `typeof table.$inferSelect`. Parallel hand-maintained type declarations drift; an agent updates one, the others silently lie.

### 9. Training-data hygiene

Agents work best with code that looks like the code they were trained on. This isn't snobbery — it's a real signal:

- **Prefer frameworks with large, stable public presence** (Hono, Drizzle, Zod, Prisma, Bun, React) over bespoke internal DSLs or cutting-edge libraries. The agent has seen the former thousands of times; the latter, rarely.
- **Pin dependency versions** (no `^` on load-bearing packages). An agent's memory of the API for `stripe@v14` is wrong for `stripe@v18`; pinning makes the docs the agent can fetch match the version you run.
- **Treat "boring stack" as a legitimate agent-performance axis.** A vanilla Postgres + Drizzle + Hono + React app will get better agent edits than an equivalently-powerful EffectTS + XState + custom-DSL setup, even if the latter is technically superior.

---

## When NOT to apply this skill

Agent-readability is one lens, not the only one. Push back — including on this skill's recommendations — when:

- **The framework dictates the layout.** Next.js `app/` routing, Rails controllers/views/models, Django apps, NestJS modules — framework conventions usually win, even if they scatter a feature across layers. The cost of fighting the framework exceeds the cost of agent-unfriendly structure.
- **Public API compatibility matters more than naming purity.** A published library function called `process()` cannot be renamed without breaking consumers. Evolve it; don't rename it just for `AR003`.
- **Metaprogramming is the product.** ORMs, validation libraries, DI frameworks, DSLs. Their job is dynamic behavior. Don't try to linter-clean them.
- **Some duplication is inherent.** Data models, DTOs, migrations, and fixtures often have repetitive shape — that's not a refactor opportunity; it's the domain.
- **The code is throwaway.** One-off migration scripts, research notebooks, prototypes that won't live past the demo. Skip the ceremony.
- **A centralized test strategy is deliberate.** Some teams colocate only unit tests and keep integration/e2e in a top-level dir on purpose. That's not a bug — disable `AR007`.

If a rule fires in a context where it shouldn't, that's a suppression, not a refactor. The linter supports `# agent-lint: disable=AR00X` inline and `# agent-lint: disable-file=AR00X` at file scope.

---

## When classical principles still apply

This skill is not "SOLID and DRY are obsolete." Human readers still exist; agents are one reader, not the only reader. Use judgment:

- **KISS and YAGNI** — unchanged. Simple code helps both audiences.
- **DRY** — still right *in spirit* (single source of knowledge), frequently wrong *in letter* (deduplicate anything that rhymes). For agents, premature abstraction is worse than duplication; three similar lines in one file are cheap, one wrong abstraction shared across ten files is expensive.
- **SOLID** — most applicable in OO-heavy enterprise codebases with long-lived human teams. In small teams using AI agents heavily, DIP and ISP often push toward unnecessary indirection that hurts both agent navigation and human comprehension. SRP is the most portable letter.

**Decide by lifetime and blast radius.** A throwaway script has a reader of ~1; skip the ceremony. A payments module maintained for ten years across dozens of contributors (human and agent) earns every clarity investment you make.

---

## Using the linter

The skill ships with `scripts/lint.py`, a zero-dependency Python linter that flags the rules above.

```bash
python scripts/lint.py <path>                    # human-readable report
python scripts/lint.py <path> --json             # machine-readable output
python scripts/lint.py <path> --rules AR001,AR003  # subset
python scripts/lint.py <path> --config my.yaml   # custom thresholds
```

It supports **Python** and **TypeScript/JavaScript** across all nine rules. Python uses the stdlib `ast` module for `AR005`/`AR006`; TS/JS uses tight regex heuristics (zero-dep by design — no `tree-sitter` or `typescript` dependency). `.js`/`.mjs`/`.cjs` files skip `AR006` since they have no type system.

**When to run it:**
- After writing or refactoring a file, as a sanity check.
- On an unfamiliar codebase before proposing a large change — findings are a punch list of the riskiest code for the agent to touch.
- In CI, with `--rules AR001,AR002,AR008` as hard errors and the rest as warnings.

See [scripts/README.md](scripts/README.md) for the full rule table, configuration, and output format.

---

## Agent context files are a separate concern

Files like `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, and `.continue/rules/` shape how agents approach a repo at a meta level (commands to run, boundaries to respect, canonical examples to imitate). They matter, but they're orthogonal to the *code itself* being agent-readable. This skill covers the code; follow the vendor docs for the context files.
