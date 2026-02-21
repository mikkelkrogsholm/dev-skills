# dev-skills — Agent Guide

This repository is a library of agent skills for modern web development. Skills follow the [Agent Skills open standard](https://skills.sh).

## Purpose

Skills extend agent capabilities by providing:
- Live documentation pointers (agent fetches current docs, not stale training data)
- Curated gotchas — non-obvious pitfalls that agents get wrong by default
- Triggering descriptions that activate the skill in the right context

## What agents should know

### Skills are thin by design
Do not add content Claude can generate without help. Each best practice must pass three tests:
1. Agents get it wrong by default
2. It is not prominently covered in the official docs
3. It is unlikely to go stale

### Skill structure
Every skill is a directory at the repo root:
```
skill-name/
├── SKILL.md          # Required: frontmatter + guidance
└── references/       # Optional: detailed content loaded on demand
    └── detail.md
```

SKILL.md frontmatter:
- `name`: kebab-case, max 64 chars
- `description`: the trigger — what the agent reads to decide whether to activate. Max 1024 chars. No angle brackets.

### Available skills (36 total)

See README.md for the full categorised list with stack combinations.

Categories: Runtime, Frameworks, UI/Animation, Databases, Auth/Storage, APIs/Payments, State/Routing, Background Jobs, Search, Observability, Deployment, Configuration, GDPR/Compliance, SEO/GEO.

### Recommended stacks

See README.md — Recommended Stacks section covers six common stack combinations useful for project planning.

## Tooling (Python scripts)

All scripts use the project virtualenv at `.venv/`:

| Script | Purpose |
|--------|---------|
| `dev-skill-creator/scripts/init_skill.py <name> --path .` | Scaffold a new skill |
| `dev-skill-creator/scripts/quick_validate.py <skill-dir>` | Validate SKILL.md |
| `dev-skill-creator/scripts/package_skill.py <skill-dir> dist/` | Package to dist/ |

Setup if `.venv` missing: `python3 -m venv .venv && .venv/bin/pip install pyyaml`

## When asked to add a new skill

1. Investigate the technology's documentation — find the best source (llms.txt, GitHub, or website)
2. Scaffold: `init_skill.py <name> --path .`
3. Write SKILL.md: description triggers the skill, body provides guidance + docs pointer + best practices
4. Add references/ files if body would exceed ~200 lines
5. Validate: `quick_validate.py`
6. Mirror: `ln -s "../../<name>" .claude/skills/<name>`
7. Package: `package_skill.py <skill-dir> dist/`
8. Update `technologies.md` (mark as done) and `README.md` (add to table)
9. Commit and push to `git@github.com:mikkelkrogsholm/dev-skills.git`

## Distribution

```bash
npx skills add mikkelkrogsholm/dev-skills        # all skills
npx skills add mikkelkrogsholm/dev-skills --skill bun  # one skill
```
