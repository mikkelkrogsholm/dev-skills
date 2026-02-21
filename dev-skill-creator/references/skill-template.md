# Tech Skill Template

Use this as the canonical template when writing SKILL.md for a new technology skill.

---

## Frontmatter

```yaml
---
name: [technology-name]
description: "[Technology] — [one sentence: what it is and its primary use case]. Use when building with [Technology] or asking about its APIs, configuration, patterns, or integration. Fetch live documentation for up-to-date details."
---
```

## Body

```markdown
# [Technology]

[Technology] is [one sentence description].

## Documentation

[Use the section matching the doc source type — pick one, delete the others]

### llms.txt (preferred)
- **Docs**: [llms.txt URL]

### GitHub repo
- **Repo**: [GitHub URL]
- **README**: [GitHub URL]/blob/main/README.md
- **Docs folder** (if present): [GitHub URL]/tree/main/docs

### Website
- **Docs**: [docs URL]

## Key Capabilities

[ONLY include if the technology has non-obvious built-in capabilities that agents
commonly replace with unnecessary external dependencies. Otherwise delete this section.]

[Technology] includes built-in support for things developers often add as separate packages:

- **[Capability]**: prefer `[built-in API]` over `[common external package]`
- **[Capability]**: prefer `[built-in API]` over `[common external package]`

## Best Practices

[ONLY include if there are evergreen gotchas meeting ALL three criteria:
(1) agent gets it wrong by default, (2) not prominently in the docs, (3) unlikely to go stale.
Otherwise delete this section.]

- [Gotcha or pattern] — [one line on why it matters]
- [Gotcha or pattern] — [one line on why it matters]
```

---

## Section Guidelines

**Key Capabilities** — include when the technology has built-ins that replace external dependencies.
- Good fit: Bun (built-in SQL, S3, password hashing, shell, test runner)
- Not a fit: React, Vite (no significant built-in replacements)

**Best Practices** — include for technologies where mistakes have real consequences.
- Good fit: Stripe (payment security), Better Auth (auth flows), Prisma (transaction safety), RustFS (deployment/replication config)
- Not a fit: Vite, shadcn/ui (low consequence, well-documented patterns)

**When both sections are empty**, the skill body is just the documentation pointer. That is fine.

## Source Type Priority

If multiple sources are available, prefer in this order:
1. `llms.txt` — purpose-built for LLM consumption, always prefer
2. Docs website — structured, maintained, browsable
3. GitHub repo — use when no dedicated docs site exists
