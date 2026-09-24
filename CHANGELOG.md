# Changelog

All notable changes to the `teamwork-tasks-from-dnr` plugin are documented in
this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] — 2026-09-24

Source: reported in a colleague's "Štyri cesty k nule" analysis, and the follow-up
request that every plugin which plans work makes the developer think about UI/UX,
performance, security and page reachability *while building* — the same four
dimensions `teamwork-task-test` checks at QA time — plus a fifth, `framework`: use
the idioms of the framework versions the project actually has installed.

### Added
- **Cross-cutting acceptance criteria for generated tasks.** A DNR describes what a
  feature must do, and the extracted acceptance criteria followed it faithfully —
  so a task that added a new admin section never said it must be reachable from the
  menu or from the parent screen, and the orphan was found in QA (or by nobody).
  Two optional task fields carry this now:
  - `ui_surface` — `new_screen` (adds a screen / admin section / module with UI) or
    `existing_screen` (changes one);
  - `cross_cutting[]` — `{dimension, criterion}` with `dimension` exactly one of
    `reachability`, `security`, `performance`, `ui_ux` (teamwork-task-test's keys)
    and the criterion in the document language.
- **Validator gate:** `validate_json.cross_validate` rejects a plan in which a
  `new_screen` task has no `reachability` item. Only reachability is enforced — it is
  the one the user asked for explicitly, and forcing the other three would push the
  model into boilerplate on tasks where they do not apply. A deliberately URL-only
  page passes by saying so.
- **Rendering:** the new `scripts/cross_cutting.py` (shared by `json_to_md.py` and
  `json_to_xlsx.py`, like `contract_render.py`) renders the items as
  `- [ ] **<Label> (<key>):** <criterion>` under `### Prierezové požiadavky` /
  `### Průřezové požadavky` / `### Cross-cutting requirements` — inside the
  acceptance section, after the ordinary criteria, before `### Závislosť` and the
  first `---`, because that block is the only one `teamwork-task-test` reads and
  ticks. The MD conventions list mentions the sub-block only when a plan uses it.
- **Extraction prompt §9a**, the `## Final check` list and SKILL.md Step 6 say when
  to set each field, give sk / cs / en examples, keep the contract task free of
  them, forbid minutes in a criterion, and ask the technical plan of a new screen to
  name where the menu entry and the inbound link are registered.
- **Framework line in the technical plan (`framework`).** Model knowledge of a
  framework is always a version or two behind, so a generated plan could steer the
  implementer to a pattern the installed Laravel / Vue / Tailwind has replaced — or
  to one it does not support yet. `repo_detect.detect_repo_mode` (`--detect-repo`)
  now also returns `framework_versions` and a one-line `framework_summary`, read
  from `composer.json` (`config.platform.php` / `require.php`), `composer.lock`
  (Laravel, Nova, Livewire, Inertia, Pest), `package-lock.json` / `package.json`
  (Vue, Nuxt, React, Ionic, Inertia, Tailwind CSS, Vite, TypeScript), `.nvmrc` /
  `engines.node` and `.browserslistrc` / `browserslist`. They are read from the
  nearest directory between the start directory and the git root that holds a
  `composer.json` / `package.json`, because the app may live in a subdirectory of
  the repository (`<repo>/appbase/`). This works in every mode and never relies on
  memory. A malformed file, or one with invalid bytes, is skipped. Prompt §11, its
  Final check and SKILL.md Step 1.5 / 6 end every code task's `technical_plan` with one
  `**Framework:**` line naming those versions ("respect the installed versions and
  their current idioms"), or a generic line when nothing was detected (Claude.ai,
  no lock files). It is plan context only — **never** an acceptance criterion or a
  `cross_cutting` item: `teamwork-task-test` treats `framework` as advisory, so such
  a checkbox could never be ticked. The schema's dimension enum stays at the four
  keys and rejects `framework`.
- `tests/test_cross_cutting.py` — 17 tests: no-op without the field, sk / cs / en
  headings and labels, placement inside the acceptance block before `Závislosť`,
  MD and XLSX byte-identical, the gold plan unchanged and still valid, the gate
  (fires without reachability, passes with it or with a URL-only statement, ignores
  `existing_screen`), unknown dimension / `ui_surface` / empty criterion rejected,
  `framework` rejected as a dimension. `tests/test_repo_detect.py` +8 tests for the
  version detection (lock wins over declared range, platform PHP wins, `v` prefix
  stripped, `.nvmrc` / `.browserslistrc` precedence, empty without git or
  manifests, malformed lock skipped, lock with invalid bytes skipped, app in a
  subdirectory of the repo, npm lockfile v1).
  Suite: 126 passed, 2 skipped (was 101 passed, 2 skipped).

### Fixed
- **Frontend mode's contract lookup aborted in zsh.** `ls docs/contracts/*/openapi.yaml
  2>/dev/null` is a `no matches found` error in zsh (Claude Code's shell on macOS)
  when no contract exists yet — exactly the case the step is written for. Replaced
  by `find docs/contracts -mindepth 2 -maxdepth 2 -name openapi.yaml`.
  Repro: `zsh -c 'ls nope/*/openapi.yaml 2>/dev/null; echo "exit=$?"'` →
  `zsh:1: no matches found: nope/*/openapi.yaml`, `exit=1`.
- **Step 1 could not find the orchestrator script, or could find a stale one.** The
  lookup `find ~/.claude/plugins -path "*/teamwork-tasks-from-dnr/skills/*/scripts/…"`
  never matches the plugin cache layout `<plugin>/<version>/skills/teamwork-tasks-from-dnr/scripts/`,
  and its fallback `$(dirname "$0")` is `.` in zsh (`$0` is `zsh`). A pattern that did
  match would have taken the first hit with `-print -quit` — possibly an older cached
  release whose validator and renderers silently ignore `ui_surface` /
  `cross_cutting`. Step 1 now uses the skill's own base directory and falls back to
  the highest installed version (`sort -V | tail -1`).
  Repro: `find ~/.claude/plugins -path "*/teamwork-tasks-from-dnr/skills/*/scripts/teamwork_tasks.py"`
  → no output with 1.3.0 and 1.5.0 both in the cache.

### Changed
- `SKILL.md` gains a short **Shell portability contract** (no bare globs, no
  bash-only expansions, `while read` for line lists, no `echo "$JSON" |`).

Unchanged: the estimate never enters a description (a criterion carries no minutes),
`md_estimate × 480` stays the hard tasklist gate, and the contract-first flow is
untouched — a plan without the new fields renders byte-for-byte as before.

## [1.5.0] — 2026-09-22

### Fixed
- **The generated tasklist description carried the estimate.** The extraction prompt
  told the model to copy the DNR's "Odhad pracnosti" sub-section into
  `tasklists[].description`, and `json_to_xlsx._build_rows` writes that straight into the
  DESCRIPTION column of the Teamwork import file. The same man-days were already the
  `md_estimate` field that `validate_json.cross_validate` gates against, so the number
  shipped twice and could disagree with itself. Removed from the prompt, from the Step 6
  summary the model acts on, and from the `## Final check` list it re-reads before
  returning.
- The three gold fixtures encoded the wrong shape and would have pulled the
  implementation back to it: `tests/fixtures/expected_tasks.json` (three tasklist
  descriptions), `tests/fixtures/Strecnianska_v1.2_gold_TeamworkTasks.md` (three
  blockquotes) and the binary `Strecnianska_v1.2_gold_TeamworkTasks.xlsx`, regenerated
  from the corrected JSON. `tests/legacy/build_tw_xlsx_v1.py` is an uncollected archive
  and carries a banner instead.
- Suite green after the change: 94 passed, 3 skipped.

### Changed
- **Two new rules, shared verbatim as the `wame-task-record-v1` block.**
  1. *The estimate lives in the estimate field, and nowhere else.* Minutes never go
     into a task title or description — not in the preamble, not in the technical
     plan, not as a footer line. An estimate gets revised, and a number duplicated
     into prose has to be changed in every copy; the copy somebody misses is the one
     the next reader believes. Previews, confirmation gates, final reports and
     companion documents may still show it — those are read once and thrown away.
  2. *Never lose what the reporter wrote.* When an existing description is rewritten,
     everything already there survives verbatim at the top: inline images, links, the
     reporter's own wording, spelling and punctuation. No diacritics added, no grammar
     fixed, no translation, no tidying.
- The task DESCRIPTION cell built by `json_to_xlsx._render_task_description` never
  carried the estimate and still does not; the number goes to the ESTIMATED TIME column
  alone. The companion Markdown plan from `json_to_md.py` keeps its `**Odhad:**` meta
  line — a document read once beside the XLSX is not a task record, and the rule says so
  explicitly.

## [1.4.0] — 2026-09-22

### Changed
- **Estimate methodology replaced — `wame-estimate-v2`.** The old rule produced a
  "traditional" estimate, cut it by 30–50 % for Claude Code, then added a 15–30 %
  buffer on top. Two percentages stacked on a guess give a 0.58×–0.91× band on
  every task, so the same work could legitimately be quoted at 60 or at 95
  minutes and the wider end always won the argument. The methodology now
  estimates **one number directly** against a table of finished-outcome anchors.
  The anchors are tighter (a single figure each, adjust by at most one 15-minute
  step) and the block states explicitly what the number covers — reproduce,
  implement, test, run the suite, self-review, one review round — and what it
  never covers: deployment, production data fixes, client communication, and any
  work behind an unanswered `[OTVORENÉ]` question.
- **Uncertainty is now an open question, not a surcharge.** Where the old text
  told you to pad for "unknown unknowns", the new one tells you to write the
  question into the task, estimate the investigation that answers it, and state
  what the fix costs under each answer.
- **The 240-minute split threshold is now named as the working ceiling**, so it
  no longer contradicts the 480-minute hard cap sitting in the same paragraph.
- The methodology block is byte-identical across `teamwork-task-analyze`,
  `teamwork-tasks-from-dnr`, `teamwork-tasks-from-desk`,
  `teamwork-tasks-from-session` and `dnr-business`, and now carries a version
  marker so a drifted copy is visible.

### Fixed
- **Two estimate rules contradicted each other and the losing one was never
  marked as losing.** `SKILL.md` told the model to apply the methodology, while
  `scripts/validate_json.py` hard-fails any plan whose tasklist minutes drift
  more than 5 % or 60 minutes from `md_estimate × 480`. The gate always won, so
  the methodology could not move a single total and the extraction prompt's
  "prefer the methodology" instruction was impossible to obey. A new
  *Which rule wins* section states the precedence: the man-days in the DNR are a
  number the client has already seen, so the **sum is a commitment** and the
  methodology governs the **distribution** inside it. When the two disagree, fit
  the budget and write the delta into `warnings` by name — never reshape tasks
  silently until the arithmetic works, because that deletes the only signal that
  the DNR figure needs reopening.
- `scripts/contract_estimate.py` no longer describes its own constants as a
  figure that "bakes in the speed-up and the risk buffer". The three constants
  are the estimate.

### Removed
- References to the 30–50 % speedup and the 15–30 % risk buffer in
  `prompts/extract_dnr_to_json.md`.

## [1.3.0] — 2026-07-24

### Added — contract-first flow

Moves the API-contract definition **ahead** of implementation so backend and
frontend tasks can run in parallel instead of the frontend waiting for a working
API. Fully additive and opt-out (`--no-contract`); every existing behaviour is
unchanged when no contract is generated.

- **Repository detection** (`scripts/repo_detect.py`, new). Walks up to the git
  root and classifies the repo as `backend` (Laravel `composer.json`),
  `frontend` (Ionic `@ionic/vue` / `@ionic/core`) or `standalone` (no repo, or
  neither). Monorepos prefer `backend` with a warning. The Laravel/module
  detection helpers are copied from the `laravel-docs` plugin (the spec forbids
  sharing code across the separate plugin repos). Exposed as
  `teamwork_tasks.py --detect-repo`.
- **Deterministic OpenAPI 3.1 emitter** (`scripts/contract_emit.py`, new). Claude
  produces a *structured* `contracts[]` block; Python renders `openapi.yaml`
  and `data-model.md` from it. Because the YAML is emitted deterministically
  (stdlib-only block-style emitter with conservative quoting), the file is valid
  OpenAPI 3.1 **even with `[DOPLNIŤ]` placeholders** — `[DOPLNIŤ]` only ever
  lands inside quoted scalar strings, never in a structural position. Generated
  contracts pass `redocly lint` with zero errors. Endpoints use the Sanctum
  bearer scheme, reference a shared response envelope via relative `$ref` +
  `allOf`, carry `x-wame-status: draft|stable`, and auto-declare path
  parameters. Two error conventions are supported (`http_status` → real 4xx
  responses; `ok` → HTTP 200 with `oneOf` success/error envelope).
- **Shared response envelope** (`assets/wame-envelope.yaml`, new) with
  `WameSuccess` / `WameError` schemas, copied once into
  `docs/contracts/_shared/` and never overwritten.
- **Idempotent contract writer** (`scripts/contract_writer.py`, new). Two-phase:
  `--contract-plan` previews actions + `difflib` diffs without touching disk;
  `--write-contract` writes. Existing contracts are never silently overwritten —
  a sibling `*.proposed` file is written and a diff surfaced (unless `--force`).
- **Contract predecessor task.** A "Definovať API kontrakt" task
  (`task_kind: "contract"`) is added at the start of the earliest linked
  tasklist, with its own MD estimate (`scripts/contract_estimate.py`,
  `45 + 15·endpoints + 15·entities`, clamped 60–480, rounded to 15). Every BE
  and FE task touching the contract lists it as a dependency; FE tasks depend on
  the **contract task**, not on backend completion, and work against a
  contract-derived mock.
- **`### Kontrakt` block** appended to the technical description of every task
  with a `contract_ref` (shared `scripts/contract_render.py`, used by both the
  MD and XLSX renderers) — file path, version, repo, and a
  `Commit: [DOPLNIŤ po zmergovaní]` line filled in manually after merge.
- **`## Chýbajúce artefakty`** section added to the Markdown plan in
  `standalone` mode, listing the contract(s) that must be generated in the
  backend repo and the tasks waiting on them.
- New prompt `prompts/extract_dnr_to_contract.md`; `prompts/extract_dnr_to_json.md`
  gains a *§11a Contract-first fields* section (role, `contract_ref`, the
  contract task, BE/FE differences).
- New CLI modes on `scripts/teamwork_tasks.py`: `--detect-repo`,
  `--contract-plan`, `--write-contract`, `--contract-estimate`, plus the
  `--no-contract` opt-out.
- 63 new pytest cases (repo detection, YAML emitter incl. a pyyaml round-trip,
  idempotent writer, estimate, rendering, schema cross-validation).

### Changed

- `prompts/json_schema.json` gains optional `contracts[]`, per-task `task_kind`
  / `role` / `contract_ref`, and metadata `repo_mode` / `repo_name` /
  `error_http_convention` / `contract_desc_language` / `contract_dir`. All new
  fields are optional, so pre-1.3.0 plans still validate unchanged.
- `scripts/validate_json.py` cross-checks contract slugs (kebab-case),
  `operation_id`s (ASCII, unique), HTTP methods, `contract_ref` integrity, and
  that every generated contract has its "Definovať API kontrakt" task. These
  checks only apply in backend mode (when `contracts[]` is present).
- The plugin **never runs git** — committing the contract and filling each
  task's `Commit:` line is left to the user.

## [1.2.1] - 2026-06-11

### Fixed
- **XLSX corruption from illegal control characters.** `scripts/json_to_xlsx.py`
  escaped cell text with `xml.sax.saxutils.escape`, which only escapes `&`, `<`
  and `>` and leaves XML-1.0-illegal C0 control bytes in place (every char
  `< 0x20` except `0x09`/`0x0A`/`0x0D`). DNR text extracted from `.docx`/`.pdf`
  routinely carries `0x0B`, `0x0C`, `NUL` and `0x01-0x08`, producing a
  non-wellformed `xl/sharedStrings.xml` that Excel/Teamwork reject as corrupt.
  A new `_xml_safe` sanitizer now strips every character outside the XML 1.0
  `Char` production and is applied to each string **before** `escape()`, while
  preserving legal whitespace (tab and newline).
- **Missing CHANGELOG link reference.** The footer listed `[1.1.0]`, `[1.0.2]`,
  `[1.0.1]` and `[1.0.0]` but was missing the `[1.2.0]:` link reference even
  though the `[1.2.0]` section existed. Added the missing reference.

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

[1.3.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.3.0
[1.2.1]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.2.1
[1.2.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.2.0
[1.1.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.1.0
[1.0.2]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.2
[1.0.1]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.1
[1.0.0]: https://github.com/wame-sk/claude-code-plugin-teamwork-tasks-from-dnr/releases/tag/v1.0.0
