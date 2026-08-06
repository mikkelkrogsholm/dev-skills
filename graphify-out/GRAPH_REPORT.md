# Graph Report - .  (2026-08-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1207 nodes · 1380 edges · 27 communities (24 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ac672b9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22

## God Nodes (most connected - your core abstractions)
1. `lint_path()` - 22 edges
2. `Finding` - 18 edges
3. `Config` - 17 edges
4. `parse_skill_md()` - 11 edges
5. `run_loop()` - 10 edges
6. `check_ar003_symbols()` - 8 edges
7. `find_runs()` - 7 edges
8. `ReviewHandler` - 7 edges
9. `improve_description()` - 7 edges
10. `run_eval()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `generate_html()`  [EXTRACTED]
  .agents/skills/skill-creator/scripts/run_loop.py → .agents/skills/skill-creator/scripts/generate_report.py
- `run_loop()` --calls--> `generate_html()`  [EXTRACTED]
  .agents/skills/skill-creator/scripts/run_loop.py → .agents/skills/skill-creator/scripts/generate_report.py
- `run_loop()` --calls--> `improve_description()`  [EXTRACTED]
  .agents/skills/skill-creator/scripts/run_loop.py → .agents/skills/skill-creator/scripts/improve_description.py
- `main()` --calls--> `parse_skill_md()`  [EXTRACTED]
  .agents/skills/skill-creator/scripts/improve_description.py → .agents/skills/skill-creator/scripts/utils.py
- `package_skill()` --calls--> `validate_skill()`  [EXTRACTED]
  .agents/skills/skill-creator/scripts/package_skill.py → .agents/skills/skill-creator/scripts/quick_validate.py

## Import Cycles
- None detected.

## Communities (27 total, 3 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (51): _apply_suppressions(), check_ar001_file_size(), check_ar002_duplicates(), check_ar003_filename(), check_ar003_symbols(), check_ar004_metaprog(), check_ar005_inheritance(), check_ar005_ts() (+43 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (37): AuditEvent, AuditTrail, _format_as_csv(), _format_as_text(), format_audit_event(), normalize_email(), Return the total of two event counts. Replaces the original `handle(x, y)`…, Format an AuditEvent using a named formatter. Raises: KeyError: if… (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (26): add_integers(), load_allowed_module(), normalize_user_payload(), User account domain model and safe expression/import helpers. This module…, Evaluate a constant arithmetic expression safely. Only numeric literals and the…, Import and return a module from the fixed allow-list. Args: module_name: The…, A user account with identity, persistence, and audit metadata., Mark the user as modified now (updates ``updated_at`` in UTC). (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (27): generate_html(), main(), Generate HTML report from loop output data. If auto_refresh is True, adds a…, _call_claude(), improve_description(), main(), Path, Run `claude -p` with the prompt on stdin and return the text response. Prompt… (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (17): add_integers(), AuditRecord, identity(), OperationHandler, OperationRegistry, T, User domain model and a small, explicit helper surface. This module replaces…, Callable that executes a named operation with keyword arguments. (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (19): build_run(), embed_file(), find_runs(), _find_runs_recursive(), generate_html(), get_mime_type(), _kill_port(), load_previous_iteration() (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (8): Auditable, Base, DynamicAPI, Entity, Manager, Persisted, Dumping-ground module. Should trigger AR003 on filename, AR003 on…, User

### Community 9 - "Community 9"
Cohesion: 0.23
Nodes (12): aggregate_results(), calculate_stats(), generate_benchmark(), generate_markdown(), load_run_results(), main(), Path, Aggregate run results into summary statistics. Returns run_summary with stats… (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.18
Nodes (7): dynamic, handler, Manager, MINIFIED, OrderManager, PaymentService, ServiceWorker

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (10): main(), Path, Lint each top-level fixture dir once; attribute findings by file. This ensures…, Run linter on specific fixtures and verify certain symbols never appear in…, Every JSON finding has the expected fields including evidence level., rule_counts(), run_lint_json(), test_expectations() (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.31
Nodes (8): main(), package_skill(), Path, Check if a path should be excluded from packaging., Package a skill folder into a .skill file. Args: skill_path: Path to the skill…, should_exclude(), Basic validation of a skill, validate_skill()

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (8): add_integers(), echo_payload(), T, Arithmetic and identity helpers used by the fixture test-suite. This module…, Return ``payload`` unchanged. Replaces the former ``process(data)``. Exists as…, Return the sum of two integers. Replaces the former ``handle(x, y)``, which hid…, A persisted, auditable user record. Replaces the five-level ``Base -> Entity ->…, User

### Community 15 - "Community 15"
Cohesion: 0.38
Nodes (6): init_skill(), main(), # TODO: Add actual script logic here, Convert hyphenated skill name to Title Case for display., Initialize a new skill directory with template SKILL.md. Args: skill_name: Name…, title_case_skill_name()

### Community 16 - "Community 16"
Cohesion: 0.38
Nodes (5): main(), package_skill(), Package a skill folder into a .skill file. Args: skill_path: Path to the skill…, Basic validation of a skill, validate_skill()

### Community 17 - "Community 17"
Cohesion: 0.38
Nodes (6): init_skill(), main(), # TODO: Add actual script logic here, Convert hyphenated skill name to Title Case for display., Initialize a new skill directory with template SKILL.md. Args: skill_name: Name…, title_case_skill_name()

### Community 18 - "Community 18"
Cohesion: 0.38
Nodes (5): main(), package_skill(), Package a skill folder into a .skill file. Args: skill_path: Path to the skill…, Basic validation of a skill, validate_skill()

### Community 19 - "Community 19"
Cohesion: 0.60
Nodes (5): Auditable, Base, Entity, Persisted, User

### Community 20 - "Community 20"
Cohesion: 0.50
Nodes (3): issue_refund(), Refund issuance — small, flat, typed, specifically named., Refund

### Community 22 - "Community 22"
Cohesion: 0.50
Nodes (3): User identity value object. This file replaces the former `utils.py` dumping…, Immutable user identity. `frozen=True` prevents accidental mutation by an agent…, User

## Knowledge Gaps
- **6 isolated node(s):** `PaymentService`, `ServiceWorker`, `handler`, `dynamic`, `MINIFIED` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_skill_md()` connect `Community 4` to `Community 3`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `check_ar006_ts()` connect `Community 1` to `Community 2`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `PaymentService`, `ServiceWorker`, `handler` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0023501762632197414 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.09433962264150944 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.06025369978858351 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.07862903225806452 - nodes in this community are weakly interconnected._