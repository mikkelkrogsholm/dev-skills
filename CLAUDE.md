# dev-skills

This is a library of agent skills for modern web development. Skills follow the [Agent Skills open standard](https://skills.sh) and work with any compatible agent (Claude Code, Cursor, etc.).

## What this repo is

Each skill is a folder at the repo root containing a `SKILL.md` file with:
- YAML frontmatter: `name` (kebab-case) and `description` (triggering mechanism, max 1024 chars, no angle brackets)
- A documentation pointer so the agent fetches live docs rather than relying on training data
- Curated best practices: gotchas that agents get wrong by default, not prominently in docs, and unlikely to go stale

Skills are thin by design. They are not tutorials. They do not contain boilerplate Claude can generate itself.

## Repo structure

```
dev-skills/
├── bun/              # Each skill at root level
│   └── SKILL.md
├── hono/
│   ├── SKILL.md
│   └── references/   # Optional: detailed reference files
├── ...
├── .claude/skills/   # Symlinks to root-level skills (for local agent use)
├── dist/             # Packaged .skill files (zip format, .skill extension)
├── dev-skill-creator/ # Meta-skill + scripts for building new skills
│   └── scripts/
│       ├── init_skill.py      # Scaffold a new skill directory
│       ├── quick_validate.py  # Validate SKILL.md frontmatter
│       └── package_skill.py  # Package skill into dist/
├── technologies.md   # Build tracker (what's done, what's planned)
├── skills-lock.json  # Skill version lock
└── README.md         # Human + agent-readable overview with stack combinations
```

## Python tooling

Scripts require the project virtualenv:

```bash
# Validate a skill
.venv/bin/python dev-skill-creator/scripts/quick_validate.py <skill-dir>

# Package a skill
.venv/bin/python dev-skill-creator/scripts/package_skill.py <skill-dir> dist/

# Scaffold a new skill
.venv/bin/python dev-skill-creator/scripts/init_skill.py <skill-name> --path .
```

If `.venv` doesn't exist: `python3 -m venv .venv && .venv/bin/pip install pyyaml`

## Adding a skill

1. Run `init_skill.py` to scaffold
2. Write `SKILL.md` — description is the trigger, body is the guidance
3. Add `references/` files if content would push SKILL.md past ~200 lines
4. Validate with `quick_validate.py`
5. Create symlink: `ln -s "../../<name>" .claude/skills/<name>`
6. Package with `package_skill.py`
7. Add to `technologies.md` and update `README.md`

## Mirroring

`.claude/skills/` contains symlinks to root-level skill folders so agents running in this project directory can load skills locally. When adding a new skill, always create the symlink.

## Distribution

Skills are distributed via:
```bash
npx skills add mikkelkrogsholm/dev-skills
```

The `.skill` files in `dist/` are zip archives with a `.skill` extension — one per skill.
