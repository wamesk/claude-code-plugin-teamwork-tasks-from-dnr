---
name: teamwork-tasks-from-dnr
description: "Use when the user asks to 'vytvor tasky z DNR', 'generuj Teamwork tasky', 'rozpíš DNR na taskov', 'vytvor projektový plán z DNR', 'create Teamwork tasks from DNR', 'build project plan from DNR', or '/teamwork-tasks-from-dnr'. Reads a 'Detailný návrh riešenia' (DNR) document (.docx, .pdf, .md) and generates a Teamwork.com import-ready XLSX plus a companion Markdown plan with task lists, business-friendly task names, acceptance criteria, and technical plans. Detects language (sk/en/cs) from the document."
argument-hint: "[path/to/dnr.(docx|pdf|md)] [--output-dir=docs] [--lang=auto|sk|en|cs] [--init] [--from-json=plan.json] [--dry-run]"
allowed-tools: [Bash, Read, Write, Glob]
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

## Error handling

- **DNR file not found** → show the resolved absolute path, suggest correction.
- **DOCX parsing failed** → suggest converting to `.md` via `pandoc DNR.docx -o DNR.md`.
- **PDF parsing requires pdftotext** → suggest `brew install poppler` (macOS) or `apt install poppler-utils` (linux), or convert to `.docx` first.
- **JSON validation fails twice** → save partial JSON to `/tmp/plan_partial.json`, show diff to schema, stop.
- **No sections detected in DNR** → emit warning, ask user to confirm fallback (treat whole doc as one tasklist).

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
