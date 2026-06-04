# Changelog

All notable changes to the `teamwork-tasks-from-dnr` plugin are documented in
this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-06-04

### Added
- **WAME estimate methodology** is now documented as an explicit
  `## WAME estimate methodology` H2 block in `SKILL.md`, placed right before
  Step 6 (the LLM extraction step). It defines the senior-engineer +
  Claude Code model: estimates are 30–50% lower than legacy hand-written
  ones, padded with a 15–30% buffer for risk, capped at 480 min per task and
  rounded to 15-min steps. Six calibration anchors (CRUD endpoint, Vue
  component, new `wamesk/*` module, schema migration, bugfix with repro,
  bugfix without repro) are listed as sanity checks rather than as a lookup
  table.
- The same block is byte-identical with the corresponding section in the
  `teamwork-task-analyze` v1.0.0 and `dnr-business` v1.2.0 plugins —
  one source of truth, three places to keep in sync.
- `prompts/extract_dnr_to_json.md` now references the methodology in the
  `### 7. Task estimated_minutes` rules so the LLM extraction applies the
  speedup + buffer factors when distributing minutes across tasks. If the
  distribution conflicts with the calibration anchors, the prompt now
  instructs the model to prefer the methodology and flag the conflict
  rather than silently inflating.

### Changed
- No schema, XLSX, or Markdown output change — `estimated_minutes` is still
  an integer column. The methodology only affects **how** the model picks
  the number, not the schema or the renderer.
- Rationale captured directly in SKILL.md: legacy estimates were ~2× too
  high and made us non-competitive; the manual workaround was to reduce
  them by hand. The methodology encodes the same judgement so the same
  engineer produces the same number twice, and competitors don't have to
  reverse-engineer it from one-off PRs.

## [1.1.0] — 2026-06-04

### Added
- **Interactive role detection + assignee prompt** in the `SKILL.md`
  workflow (new *Step 6.5*). After the JSON plan is extracted, Claude scans
  every task name for role tags (`[BE]`, `[FE]`, `[QA]`, `[DevOps]`,
  `[Compliance]`, …), groups them by role, and asks the user one
  `AskUserQuestion` per detected role for an e-mail / Teamwork user to
  pre-assign that role's tasks to. **The prompt always includes a `Skip`
  option** so the user can leave assignment to the PM after import — no
  role is auto-assigned without explicit consent. Single-role plans (e.g.
  pure backend) skip the prompt entirely.
- New optional **`assign_to`** field on every task (schema-level). When
  set, it populates the `ASSIGN TO` column of the import XLSX (column 4)
  and is shown in the Markdown report on the task meta line as
  `**Pridelené:** <value>`. This is the underlying mechanism that the
  interactive role prompt writes into; users can also set it manually in
  the JSON plan before `--build` when they regenerate via `--from-json`.
- `prompts/extract_dnr_to_json.md` documents the new field under section
  *10a — Task `assign_to`* including the role-tag convention
  (`4.1.1 [BE] …`) that powers role detection.

## [1.0.2] — 2026-06-04

### Added
- **Summary of acceptance criteria** is now automatically appended to every
  tasklist description in both the Markdown report and the XLSX
  `DESCRIPTION` cell. The summary picks one representative acceptance
  criterion from each **High** and **Medium** priority task in the tasklist,
  prefixed with the task's section number (e.g. `[4.1.3]`), so a PM can
  scan the deliverables of a whole feature without opening every task.
  *Low priority tasks are intentionally excluded to keep the summary focused
  on must-have outcomes.*
- New shared helper `scripts/description_summary.py` is reused by
  `json_to_md.py` and `json_to_xlsx.py` so the MD report and the XLSX
  cell stay byte-identical.
- Summary heading is localised: `Sumár akceptačných kritérií` (sk),
  `Souhrn akceptačních kritérií` (cs), `Acceptance criteria summary` (en).

### Changed
- `extract_dnr_to_json.md` prompt now documents the auto-summary behaviour so
  authors know they only need to write clean per-task `acceptance_criteria`
  arrays — they should **not** add a summary section manually.

## [1.0.1] — 2026-06-03

### Changed
- **Tasklist `name` format** must now prefix the descriptive title with the
  DNR section reference (e.g. `4.1 Ročný zálohový predpis`) so Teamwork lists
  scan-map back to the DNR.
- **Task `name` format** must add the per-tasklist 1-based index after the
  parent section (e.g. `4.1.1 Príprava systémových štruktúr…`).
- Tasklist description sub-headings switched from `==` heredoc markers to
  `**` Markdown bold. The `==` style does not render in Teamwork's task
  description view.

### Fixed
- Gold fixture (JSON + MD) regenerated with the new conventions; the full
  pytest suite (28 cases) still passes.

## [1.0.0] — 2026-05-22

### Added
- Initial release of the `teamwork-tasks-from-dnr` plugin.
- Generates Teamwork.com import-ready **XLSX** + companion **Markdown** plan
  from a "Detailný návrh riešenia" (DNR) document.
- Stdlib-only Python orchestrator (works in Claude Code plugins and the
  Claude.ai cloud sandbox without `pip install`).
- Components:
  - `.claude-plugin/plugin.json` — manifest.
  - `skills/teamwork-tasks-from-dnr/SKILL.md` — orchestration steps
    (identical in Claude Code and Claude.ai contexts).
  - `scripts/dnr_to_text.py` — DOCX / MD / PDF parser with metadata
    detection (client, project ref, version, title, language).
  - `scripts/json_to_md.py` — Markdown renderer with per-tasklist task
    breakdown (Acceptance criteria checkbox list, Goal, Technical plan).
  - `scripts/json_to_xlsx.py` — minimal OOXML XLSX writer (no `openpyxl`,
    no `pandas`).
  - `scripts/validate_json.py` — JSON Schema validator (with the 5% / 60min
    `estimated_minutes` vs `md_estimate` tolerance check).
  - `scripts/teamwork_tasks.py` — CLI orchestrator (`--init`, `--plan`,
    `--validate`, `--build`).
  - `prompts/extract_dnr_to_json.md` + `prompts/json_schema.json` — LLM
    extraction prompt and the intermediate schema.
  - `tests/` — 28 pytest cases including a gold-standard fixture from
    *DNR Strečnianska v1.2*.
  - `config.example.json` — per-project configuration template.

### Conventions baked in from the start
- Detects DNR language (sk / cs / en) and produces all outputs in that
  language.
- Acceptance criteria rendered as Markdown checkboxes (`- [ ]`).
- Each task has a `Cieľ` (Goal) and a `Technický popis` (Technical plan)
  section.
- `TAGS` column intentionally left empty; `STATUS` defaults to `Active`.

[1.1.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.1.0
[1.0.2]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.2
[1.0.1]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.1
[1.0.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.0
