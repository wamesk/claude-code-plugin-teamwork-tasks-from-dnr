---
name: teamwork-tasks-from-dnr
description: "Use when the user asks to 'vytvor tasky z DNR', 'generuj Teamwork tasky', 'rozpíš DNR na taskov', 'vytvor projektový plán z DNR', 'create Teamwork tasks from DNR', 'build project plan from DNR', or '/teamwork-tasks-from-dnr'. Reads a 'Detailný návrh riešenia' (DNR) document (.docx, .pdf, .md) and generates a Teamwork.com import-ready XLSX plus a companion Markdown plan with task lists, business-friendly task names, acceptance criteria, and technical plans. Detects language (sk/en/cs) from the document."
argument-hint: "[path/to/dnr.(docx|pdf|md)] [--output-dir=docs] [--lang=auto|sk|en|cs] [--no-contract] [--init] [--from-json=plan.json] [--dry-run]"
allowed-tools: [Bash, Read, Write, Glob, AskUserQuestion]
---

# Teamwork Tasks From DNR

Generates a Teamwork.com import-ready **XLSX** plus a companion **Markdown** plan
from a "Detailný návrh riešenia" (DNR) document. Works in Claude Code (local
plugin) and Claude.ai (online skill) with the same script.

## Arguments

User invoked this with: `$ARGUMENTS`

Supported forms:
- `/teamwork-tasks-from-dnr <path>` — generate from a DNR file
- `/teamwork-tasks-from-dnr <path> --output-dir=<dir>` — custom output dir
- `/teamwork-tasks-from-dnr <path> --lang=en` — force output language
- `/teamwork-tasks-from-dnr --init` — write per-project `config.json`
- `/teamwork-tasks-from-dnr --from-json=<json>` — skip LLM, regenerate XLSX/MD from existing plan JSON
- `/teamwork-tasks-from-dnr <path> --dry-run` — produce JSON plan only, do not write XLSX/MD
- `/teamwork-tasks-from-dnr <path> --no-contract` — skip the contract-first flow (pre-1.3.0 behaviour: XLSX + MD only)

## Step-by-step instructions

### Step 1 — Locate the orchestrator script

The Python orchestrator ships with the plugin. Find it once and reuse:

```bash
SCRIPT=$(find ~/.claude/plugins -path "*/teamwork-tasks-from-dnr/skills/*/scripts/teamwork_tasks.py" -print -quit 2>/dev/null | head -1)

# Claude.ai cloud fallback: script lives next to SKILL.md
if [ -z "$SCRIPT" ]; then
    SCRIPT="$(dirname "$0")/scripts/teamwork_tasks.py"
fi
```

If still empty, tell the user the plugin is not installed correctly and stop.

### Step 1.5 — Detect repository mode

Classify the repo you are running in — it decides whether the API contract is
**generated**, **referenced**, or **skipped**:

```bash
python3 "$SCRIPT" --detect-repo --pretty
```

Returns `{ mode, repo_name, is_backend, is_frontend, modules, warning }`:

- **`backend`** (Laravel `composer.json`) — you will *generate* the API contract
  skeleton from the DNR.
- **`frontend`** (Ionic `@ionic/vue` / `@ionic/core`) — you will *reference* an
  existing contract, never generate one.
- **`standalone`** (no git repo, or neither backend nor frontend — typical on
  Claude.ai) — no contract is produced; the Markdown plan instead gets a
  `## Chýbajúce artefakty` section listing what must be generated in the BE repo.

If `warning` is present (monorepo — both Laravel and Ionic detected), relay it.

**`--no-contract`**: if the user passed `--no-contract`, skip every contract
step below and behave exactly like the pre-1.3.0 skill (XLSX + MD only). Do not
add any contract fields to the plan.

Remember `mode` and `repo_name` for the rest of the run.

### Step 2 — Handle `--init`

If user passed `--init`, run:

```bash
python3 "$SCRIPT" --init
```

Print the resulting `config_path`. Stop.

### Step 3 — Handle `--from-json` (skip LLM)

If user passed `--from-json=<path>`, jump directly to **Step 7 (Build)** with
that JSON. Skip Steps 4-6.

### Step 4 — Locate the DNR file

Parse the first positional argument as the DNR path. If missing:
- In Claude.ai chat: ask the user to upload the DNR document.
- In Claude Code: ask for the path.

Resolve the path (absolute or relative to the project root) and check that
the file exists. If not, stop with a clear error message.

### Step 5 — Extract DNR plain text + metadata

```bash
python3 "$SCRIPT" --plan --dnr "<path>" --pretty
```

The script returns a JSON object with:
- `plain_text` — the full DNR converted to plain text (newline-preserved)
- `detected_language` — `sk` / `en` / `cs` (heuristic from common stop words)
- `section_count` — number of detected extension sections
- `client_metadata` — `{ client, project_ref, version, title }` (best-effort grep from header)
- `warning` — present if extraction was incomplete; relay to the user

If the user passed `--lang=<code>`, override `detected_language` with that.

### Step 5.5 — Contract questions (backend mode — ask at the start)

If `mode == backend` and `--no-contract` was **not** passed, ask the user these
**before** extraction, in a single `AskUserQuestion` batch. They pin down the
contract and must not be guessed (spec open questions §9):

1. **Chybový HTTP status** — internal WAME examples disagree (one returns errors
   with `Response::HTTP_OK`, another with `HTTP_UNAUTHORIZED`). The contract must
   commit to one:
   - `HTTP status (napr. 401/422)` → `error_http_convention = "http_status"`.
   - `Vždy HTTP 200 (chyba v obálke)` → `error_http_convention = "ok"`.
2. **Jazyk `description` v OpenAPI**:
   - `Slovensky (konzistentné s DNR)` → `contract_desc_language = <DNR language>`.
   - `Anglicky (konzistentné s kódom)` → `contract_desc_language = "en"`.
3. **Umiestnenie kontraktu** — confirm `docs/contracts` or take a custom path →
   `contract_dir`.

Store the answers in `metadata` (`error_http_convention`,
`contract_desc_language`, `contract_dir`). Pass `error_http_convention` to
`--contract-plan` / `--write-contract` as `--error-convention`.

## WAME estimate methodology

We estimate as senior engineers using Claude Code as a force multiplier.

Baseline assumptions:
- Engineer is senior in the stack of the current repo
- Claude Code handles boilerplate / scaffolding / repetitive edits
- Test scaffolding (Pest/PHPUnit/Vitest/Playwright) is mostly LLM-generated
- Code review and QA are done by the same engineer (no separate review cycle)

Speedup vs traditional estimate: ~30–50% faster than a hand-written estimate
without Claude Code. Apply that reduction first.

Buffer policy: after the reduction, add 15–30% buffer for:
- unknown unknowns (undocumented API, hidden coupling)
- environment friction (failing CI, flaky local setup)
- review feedback that costs more than one cycle

The final number must:
- be a multiple of 15 minutes
- be at least 15 minutes for trivial tasks (rename, copy edit)
- be at most 8 hours (480 min) per single task — bigger tasks must be split

Calibration anchors (use as sanity check, not as a lookup table):
- Single-model CRUD endpoint + Pest test: 60–120 min
- New Vue component wired to existing API: 60–120 min
- New module in `wamesk/*` (model + migration + controller + tests): 240–360 min
- DB schema migration with data backfill: 180–300 min
- Bugfix from reproducible repro: 60–180 min
- Bugfix without repro / investigation: 120–360 min

Why this matters: legacy estimates were ~2× too high and made us
non-competitive. Reducing them manually was the workaround. This methodology
encodes the same judgement so estimates are aggressive (we beat them in
practice) yet still include enough buffer to survive surprises.

This block is **byte-identical** with the same section in the
`teamwork-task-analyze` and `dnr-business` plugins. When updating the
methodology, change it in all three places.

---

### Step 6 — Extract structured task plan (LLM intelligence)

Read the prompt at `${PROMPT_DIR}/extract_dnr_to_json.md` (where `PROMPT_DIR`
is the `prompts/` folder next to the script).

You (Claude) now perform the extraction:

1. Read `plain_text` from Step 5.
2. Apply the rules from `extract_dnr_to_json.md`:
   - Each extension section → one tasklist.
   - Tasklist description = verbatim DNR text from that section.
   - 6-12 business-friendly tasks per tasklist.
   - Each task: `name`, `priority`, `estimated_minutes`, `goal`, `acceptance_criteria[]`, optional `dependencies[]`, `technical_plan`.
   - Sum of `estimated_minutes` per tasklist must match DNR "Odhad pracnosti" (1 MD = 480 min).
   - Output language = `detected_language` (do **not** translate).
3. Produce a JSON object matching `${PROMPT_DIR}/json_schema.json`.
4. Validate the JSON:
   ```bash
   python3 "$SCRIPT" --validate --json /tmp/plan.json
   ```
   If validation fails, fix the JSON and retry (max 2 attempts). Common issues:
   - Missing required field → add it.
   - `estimated_minutes` not divisible by 15 → round.
   - Wrong language enum → match detected.

### Step 6a — Generate / reference the API contract

Skip this whole step if `--no-contract` was passed.

**Backend mode** (`mode == backend`):

1. Read `${PROMPT_DIR}/extract_dnr_to_contract.md` and produce the `contracts[]`
   block (endpoints, schemas, `data_model`) using the Q1–Q3 answers. If the DNR
   has no clean feature boundaries, ask **Q4** now via `AskUserQuestion`: one
   contract per project, or one per phase — and shape `contracts[]` accordingly.
2. Wire the contract into the tasklists exactly as `extract_dnr_to_json.md` §11a
   says: add the "Definovať API kontrakt" task (`task_kind: "contract"`) at the
   start of the earliest linked tasklist, set `contract_ref` on every
   API-touching task, add the contract task to their `dependencies`, and apply
   the BE/FE differences (BE: response-matches-contract AC + Pest test proposal;
   FE: depends on the contract task, works against a mock). Compute the contract
   task estimate with `python3 "$SCRIPT" --contract-estimate --endpoints N --entities M`.
3. Set `metadata.repo_mode = "backend"` and `metadata.repo_name = <repo_name>`.
4. Re-validate — the validator now also checks contract slugs, `operation_id`s,
   and that every contract has its "Definovať API kontrakt" task:
   ```bash
   python3 "$SCRIPT" --validate --json /tmp/plan.json
   ```

**Frontend mode** (`mode == frontend`):

1. Look for an existing contract (Glob `docs/contracts/**/openapi.yaml`):
   ```bash
   ls docs/contracts/*/openapi.yaml 2>/dev/null
   ```
2. If found, set `contract_ref` on every API-touching task to that slug (read
   its `info.version` for the version). **Never generate or modify** the
   contract here.
3. If **none** exists, do not fail: add a `warning` ("kontrakt zatiaľ neexistuje
   — dogenerovať v BE repe") and still set `contract_ref` to the expected slug,
   so the reference is ready once the BE side lands.
4. Set `metadata.repo_mode = "frontend"`. No contract task is added on the FE
   side — it belongs to the backend plan.

**Standalone mode** (`mode == standalone`):

Set `metadata.repo_mode = "standalone"`. Do **not** generate a contract. Tag
API-touching tasks with `contract_ref` (slug only) so the renderer lists them
under `## Chýbajúce artefakty`. Never invent contract content.

### Step 6.5 — Detect roles and optionally pre-assign tasks

After the JSON validates, scan every task `name` for a role tag in square
brackets right after the section number — the convention from the prompt is
`<section> [ROLE] <title>` (e.g. `4.1.1 [BE] Pridanie konfigurácie …`,
`4.3.2 [FE] Ionic AutoAddService …`). Common tags are `BE`, `FE`, `QA`,
`DevOps`, `Compliance`, `Docs`. Tasks without a tag fall into an implicit
`Other` bucket.

**Decision logic:**

- **Zero or one role detected** → skip this step entirely (nothing to ask
  about, the PM can pre-assign the whole plan in Teamwork after import).
- **Two or more roles detected** → ask the user **one `AskUserQuestion`
  per role**, in role order. Each question:
  - Header: `<ROLE> assignee` (max 12 chars — truncate if needed).
  - Question text: `K úlohám označeným [<ROLE>] (N úloh, X.Xh) — kto má byť
    pridelený?` (use the detected language; fall back to English if not
    sk/cs/en).
  - **Options must always include `Skip`** (literally as one of the
    options, plus the harness adds the user's free-text "Other" option
    automatically). Suggest 1–2 likely e-mails if the user mentioned any
    in the conversation; otherwise just `Skip`.

**Write the answers back into the JSON plan:**

For every task whose role matches an answered role and the user picked an
e-mail (not `Skip`), set `task["assign_to"] = "<email>"`. Leave others
untouched. Re-validate after the edit:

```bash
python3 "$SCRIPT" --validate --json /tmp/plan.json
```

The orchestrator's `--build` step will then populate the XLSX `ASSIGN TO`
column (and the MD `**Pridelené:**` meta line) automatically. If the user
picks `Skip` for every role, the column stays empty and the PM assigns in
Teamwork after import — exactly the same as before this feature existed.

### Step 7 — Confirm before write

Show the user a compact summary:

```
Project: <title>
Language: <lang>
Tasklists: N (X.X MD total, Yh)
Tasks: M total

Tasklist 1: <name> — N tasks (X.X MD)
Tasklist 2: <name> — N tasks (X.X MD)
...

Output dir: <output_dir>
Files to write:
  - <basename>_TeamworkTasks.md
  - <basename>_TeamworkTasks.xlsx
```

If user passed `--dry-run`, write only `<basename>_TeamworkTasks.json` (the
plan JSON itself) and stop.

### Step 7a — Write the contract (backend mode)

Only in `backend` mode, after the user confirmed the plan and before building
the outputs. Skip if `--no-contract`.

1. **Preview** — compute the intended writes without touching disk:
   ```bash
   python3 "$SCRIPT" --contract-plan --json /tmp/plan.json --contract-dir "<contract_dir>"
   ```
   Show each action (`create` / `unchanged` / `exists`). When an action is
   `exists`, the file is already there and may have been hand-edited — show the
   unified `diff` and ask the user what to do. Do not proceed past an `exists`
   without confirmation.
2. **Write**:
   ```bash
   python3 "$SCRIPT" --write-contract --json /tmp/plan.json --contract-dir "<contract_dir>"
   ```
   Existing files are **never overwritten silently** — a sibling `*.proposed`
   file is written instead. Use `--force` only when the user explicitly asks to
   overwrite the current file. The shared `_shared/wame-envelope.yaml` is only
   ever created, never modified.
3. Report created / proposed files. The skill **never runs git** — committing
   the contract and filling the `Commit:` line in each task is left to the user.

### Step 8 — Build the outputs

```bash
python3 "$SCRIPT" --build --json /tmp/plan.json --output-dir "<dir>" --basename "<basename>"
```

The script writes both files and prints:

```
✅ Created: <relative path>.md
✅ Created: <relative path>.xlsx
```

### Step 9 — Final summary

```
Generated N tasks across M tasklists, total Y hours (Z MD).
Output:
  - <path>.md
  - <path>.xlsx

Import to Teamwork: Options → Import → Microsoft Excel → upload <path>.xlsx
```

Also report, when relevant:

- **backend** — the contract files written (`docs/contracts/<slug>/openapi.yaml`,
  `data-model.md`, `_shared/wame-envelope.yaml`) and any `*.proposed` files that
  need manual reconciliation. Remind the user to review `x-wame-status: draft`
  endpoints and `[DOPLNIŤ]` values, then merge and fill each task's `Commit:` line.
- **frontend** — which existing contract was referenced (or that it is missing).
- **standalone** — that the plan carries a `## Chýbajúce artefakty` section
  because the contract must be generated by re-running this skill in the BE repo.

## Error handling

- **DNR file not found** → show the resolved absolute path, suggest correction.
- **DOCX parsing failed** → suggest converting to `.md` via `pandoc DNR.docx -o DNR.md`.
- **PDF parsing requires pdftotext** → suggest `brew install poppler` (macOS) or `apt install poppler-utils` (linux), or convert to `.docx` first.
- **JSON validation fails twice** → save partial JSON to `/tmp/plan_partial.json`, show diff to schema, stop.
- **No sections detected in DNR** → emit warning, ask user to confirm fallback (treat whole doc as one tasklist).
- **Frontend repo, no contract found** → do **not** fail; warn ("kontrakt zatiaľ neexistuje — dogenerovať v BE repe") and reference the expected slug.
- **Contract file already exists (backend)** → the writer produces a `*.proposed` file + a diff; show the diff and ask before doing anything else. Never `--force` without an explicit request.
- **Not a backend repo but user expected a contract** → explain the detected mode and that contracts are only authored in a Laravel backend repo; suggest re-running there or `--no-contract`.

## Configuration reference

Per-project config lives at:
```
~/.claude/plugins/data/teamwork-tasks-from-dnr-wamesk/<project-hash>/config.json
```

Created via `/teamwork-tasks-from-dnr --init` from the bundled `config.example.json`.

Key options:

- `output_dir` — where MD/XLSX go (project-relative).
- `output_basename` — `auto` (derive from DNR filename) or fixed string.
- `language` — `auto` (detect) or explicit `sk`/`en`/`cs`. CLI `--lang` overrides.
- `priorities.high_keywords` / `medium_keywords` / `low_keywords` — used in prompt as hints for LLM priority assignment.
- `task_size_target` — min/max tasks per tasklist, min/max minutes per task.
- `xlsx_layout` — colors, column widths.
- `include_tags` — whether to populate the TAGS column (default `false`, per user request).
- `default_status` — value for the STATUS column (default `Active`).

## Notes for Claude

- The orchestrator script uses **only Python stdlib** — works in Claude.ai
  cloud sandbox without `pip install`.
- The XLSX writer creates a minimal-but-valid OOXML file. If you need to
  inspect it, `unzip <file>.xlsx` reveals the standard XML structure.
- The MD output is designed for direct use in Claude Code's **Plan mode**:
  copy a single task description and paste it as the plan prompt.
- For DNR documents in non-WAME format (no "Rozšírenie č. N" headings), fall
  back to detecting any top-level numbered sections (`## 4.1`, `# Module 1`,
  etc.) and emit a warning.
- **Contract-first (since 1.3.0)** is fully additive. With `--no-contract`, or
  in a repo that is neither Laravel nor Ionic, the skill behaves byte-for-byte
  like before: no `contracts[]`, no `contract_ref`, no `### Kontrakt` block, and
  the XLSX/MD are unchanged. The `openapi.yaml` is emitted deterministically by
  `contract_emit.py` from the structured `contracts[]` you produce — you never
  hand-write YAML, which is what keeps it valid OpenAPI 3.1 even with `[DOPLNIŤ]`.
