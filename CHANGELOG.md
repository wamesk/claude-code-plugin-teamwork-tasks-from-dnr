# Changelog

All notable changes to the `teamwork-tasks-from-dnr` plugin are documented in
this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.2]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.2
[1.0.1]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.1
[1.0.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.0
