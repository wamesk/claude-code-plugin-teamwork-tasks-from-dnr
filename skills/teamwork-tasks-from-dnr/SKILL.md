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

## Shell portability contract

The bash snippets below run in the user's login shell — **zsh on macOS** (what
Claude Code's Bash tool starts there), bash elsewhere — and every Bash tool call
is a fresh shell, so re-resolve `$SCRIPT` in each call that needs it. The heavy
lifting is in the stdlib-only Python scripts; keep the shell glue to these rules:

- **No bare globs that may not match** — zsh aborts with `no matches found`
  before `2>/dev/null` applies (`ls docs/contracts/*/openapi.yaml` did exactly
  that in a repo without contracts). Use `find`.
- **`[ "$a" = "$b" ]`** with a single `=`; no `${!…}`, `${X@Q}`, `${X,,}` (bad
  substitution in zsh); read line lists with `while IFS= read -r`, never an
  unquoted `for X in $LIST` (zsh iterates once).
- JSON goes to `jq` / Python through a file, stdin or a here-string — never
  `echo "$JSON" | …`, whose zsh `echo` rewrites backslashes inside the JSON.
- A failing script call is reported, not swallowed: relay the script's own
  error output and stop, per *Error handling* below.

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

The Python orchestrator ships with the plugin, next to this `SKILL.md`. Prefer
that copy — it is guaranteed to match these instructions:

```bash
# The skill's own directory, as announced when the skill loaded
# ("Base directory for this skill: …"). Works locally and on Claude.ai.
SCRIPT="<base directory of this skill>/scripts/teamwork_tasks.py"

if [ ! -f "$SCRIPT" ]; then
    # Fallback: the newest installed copy. The plugin cache layout is
    # <plugin>/<version>/skills/teamwork-tasks-from-dnr/scripts/ — sort by version
    # so an older cached release (without the newest renderers and validator
    # rules) never wins. `$(dirname "$0")` is no fallback: in zsh `$0` is "zsh".
    SCRIPT=$(find ~/.claude/plugins -path "*/skills/teamwork-tasks-from-dnr/scripts/teamwork_tasks.py" 2>/dev/null | sort -V | tail -1)
fi
echo "SCRIPT=${SCRIPT:-<not found>}"
```

If still empty, tell the user the plugin is not installed correctly and stop.

### Step 1.5 — Detect repository mode

Classify the repo you are running in — it decides whether the API contract is
**generated**, **referenced**, or **skipped**:

```bash
python3 "$SCRIPT" --detect-repo --pretty
```

Returns `{ mode, repo_name, is_backend, is_frontend, modules, warning,
framework_versions, framework_summary }`:

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

`framework_versions` / `framework_summary` (since 1.6.0) are the framework and
language versions installed in the repo. They are read from `composer.json` /
`composer.lock` / `package.json` / `package-lock.json` / `.nvmrc` /
`.browserslistrc` in the nearest directory between the current one and the git
root that has a `composer.json` / `package.json` (e.g. `PHP ^8.3, Laravel
12.28.1, Nova 5.7.4, Vue 3.5.13`). This works in any mode, `--no-contract`
included. They are empty / `null` without a git root or without those files.
They feed the technical plan's framework line (Step 6). If the repo you run in
is not the project the DNR describes, ignore them and use the generic line.

Remember `mode`, `repo_name` and `framework_summary` for the rest of the run.

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

## Task record rules

> Block version `wame-task-record-v1`. Shared **verbatim** across the plugins that write a Teamwork
> task — `teamwork-task-analyze`, `teamwork-tasks-from-desk`, `teamwork-tasks-from-session` and
> `teamwork-tasks-from-dnr`. Change it in all of them or in none.

### The estimate lives in the estimate field, and nowhere else

Never write minutes or hours into a task's **title** or **description**. Not in the preamble, not
inside the technical plan, not as a footer line under it.

The reason is maintenance, not taste. An estimate gets revised — after the first hour of work, after
a clarifying answer comes back, after the task is split into subtasks. A number that also sits in
prose has to be found and changed in every copy it was written to, and the copy somebody misses is
the one the next reader believes. One field, one number, nothing to reconcile.

This binds every surface that writes a task:

- the description body, including any `**Odhad:** … min` or `**Estimate:** … min` line
- the task title, including a `(120 min)` or `· 2h` suffix
- the description column of a generated import file
- a subtask's title and description, on the same terms as the parent

Where the estimate belongs instead: the API estimate field — `estimateMinutes` on a v3 read,
`estimatedMinutes` on a v3 create, `estimated-minutes` on the classic v1 update.

Where it is still fine to show: the terminal preview, the confirmation gate, the final report, and
any companion document that is not the task itself — a Desk internal note, a Markdown plan sitting
next to an XLSX. Those are read once and thrown away. The task record is not.

### Never lose what the reporter wrote

When this skill rewrites an **existing** task description, everything already there survives
**verbatim** at the top, above the first `---`.

- **Inline images.** A screenshot pasted into a Teamwork description is ordinary Markdown:
  `![image.png](https://tw-inlineimages.s3-accelerate.amazonaws.com/…)`. It is **not** a separate
  attachment, and Teamwork shows it **nowhere else** — `GET /projects/api/v3/tasks/{id}/files.json`
  returns nothing for it. Dropping that link deletes the screenshot from the task. This is not
  hypothetical: one run stripped the image links out of 18 descriptions on the assumption that
  Teamwork rendered them separately, and destroyed 25 screenshots. They came back only because the
  original text happened to still be in a scratch file.
- **The reporter's own wording, spelling and punctuation.** Do not add diacritics, do not fix
  grammar, do not translate, do not tighten, do not re-order. A bug report is the record of what
  somebody saw and how they described it. A tidied version is no longer that record, and the tester
  cannot recognise their own report in it.
- **Links, lists, line breaks, and any HTML that is already there.** Pass the block through
  untouched.

Before writing, read the current description. After composing the new one, check that the old text
still occurs inside it character for character. When it does not, you are about to delete somebody's
work — stop and ask the user instead of writing.

Attachments and comments are separate records and this skill never touches them. If a change would
need one removed, that is a question for the user, not a step in the plan.

---

## WAME estimate methodology

> Block version `wame-estimate-v2`. Shared **verbatim** across the plugins
> `teamwork-task-analyze`, `teamwork-tasks-from-dnr`, `teamwork-tasks-from-desk`,
> `teamwork-tasks-from-session` and `dnr-business`. Change it in all five or in
> none — a per-plugin variant is how two skills start quoting different numbers
> for the same task.

**Estimate one number, directly.** Do not produce a "traditional" estimate and
then multiply it by a speedup and a buffer. Two percentages stacked on a guess
open a band almost twice as wide as the guess itself, and in a negotiation the
widest end of that band always wins. Name the minutes the work takes and defend
that number.

**Who does the work.** A senior engineer who already knows this codebase,
directing Claude Code. Claude Code writes the implementation and the tests; the
engineer decides, reviews and runs the suite. There is no separate QA pass and
no handover to a second person.

**What the number covers**

- Reading the relevant code and reproducing the reported behaviour
- The implementation itself
- Writing or extending the test, and running the affected tests
- Self-review and the fixes it produces
- One round of review feedback

**What the number never covers** — estimate each of these as its own task instead
of folding it in

- Deployment, running the migration on production, fixing production data
- Talking to the client or the PO, and waiting for the answer
- Any work that sits behind an unanswered `[OTVORENÉ]` question
- Anything the task itself declares out of scope

**Shape of the number**

- A multiple of 15 minutes. Never below 15.
- Above 240 minutes: propose a split into 2–6 atomic subtasks. That threshold is
  `propose_split_threshold_minutes` and it is the real ceiling in daily use.
- 480 minutes is a hard cap. Work that will not fit under it is not a task yet.

**Anchors.** These are finished outcomes, not categories of feeling. Pick the
closest line and move by at most one 15-minute step. If the number you want is
more than one step away from every anchor, write down in the reasoning what makes
this case different — that sentence is what a reviewer checks.

| Finished work | Minutes |
|---|---|
| Text, label, translation key or config value, plus the test that guards it | 15 |
| One field, filter or validation rule on one screen, plus a test | 30 |
| Bug with a stack trace or a one-line repro: fix plus regression test | 60 |
| Vue/React component wired to an API that already exists, plus a test | 90 |
| Bug that reproduces but spans 2–3 layers: fix plus tests | 120 |
| One CRUD endpoint or one screen end to end, plus tests | 120 |
| Bug with no repro yet: investigate, then fix | 180 |
| Schema migration with a data backfill and a copy-back assertion | 180 |
| New module in `wamesk/*` (model, migration, Nova screen, policy, tests) | 300 |

**Uncertainty is an open question, not a surcharge.** When you cannot size the
work, you have found something the task does not say yet. Write that question
into the task, estimate the investigation that answers it, and state in the
reasoning what the fix costs under each likely answer. A number with a written
assumption survives review. A number padded for "unknown unknowns" does not, and
it hides the question that was worth asking.

**Do not pad a task because it is labelled TBD**, and do not shrink a real
multi-layer bug so the list looks cheap. Both errors cost the same trust.

**Why this replaced the old rule.** Hand-written estimates used to run about
twice the real cost, which lost us work we should have won. The first fix was a
30–50 % speedup factor with a 15–30 % buffer on top — but that chain put the
padding straight back while sounding rigorous, and it produced a 0.58×–0.91×
band on every single task. The anchors above carry the same judgement as one
number. The measured feedback loop is the `teamwork-tasks-from-session` plugin,
which shows the methodology estimate and the real logged session time side by
side. When those two drift apart on the same kind of work, change the anchors
here — never re-introduce a buffer percentage.

### Which rule wins: the DNR man-days or the methodology

These two pull in opposite directions and the skill must not pretend otherwise.

- `md_estimate × 480` is a **hard gate**. `scripts/validate_json.py`
  (`cross_validate`, the `md_estimate` check) fails the plan when a tasklist's
  minutes drift more than 5 % or 60 minutes from it, and a failed plan is never
  written. The man-days in the DNR are a number the client has already seen, so
  the sum is a commitment, not an estimate.
- The methodology therefore governs **the distribution, not the total**: which
  task is twice the size of which, where each number sits against the anchors,
  and the 15-minute step. Within a fixed tasklist budget that is exactly the
  judgement worth having.
- When the methodology total and `md_estimate × 480` genuinely disagree, **do
  not reshape the tasks until the numbers happen to fit.** Fit them to the
  budget, then write the delta into `warnings` in plain words — which tasks you
  had to compress or stretch, and by how much. That line is what lets a human
  reopen the DNR figure. A silently reshaped plan hides the one fact the PM
  needed.
- Never inflate a task to consume leftover budget, and never cut one below its
  anchor to create room. Adjust across several tasks proportionally instead.

---

### Step 6 — Extract structured task plan (LLM intelligence)

Read the prompt at `${PROMPT_DIR}/extract_dnr_to_json.md` (where `PROMPT_DIR`
is the `prompts/` folder next to the script).

You (Claude) now perform the extraction:

1. Read `plain_text` from Step 5.
2. Apply the rules from `extract_dnr_to_json.md`:
   - Each extension section → one tasklist.
   - Tasklist description = verbatim DNR text from that section, minus the
     "Odhad pracnosti" sub-section — the estimate belongs only in `md_estimate`
     and in the ESTIMATED TIME column, never in a description.
   - 6-12 business-friendly tasks per tasklist.
   - Each task: `name`, `priority`, `estimated_minutes`, `goal`, `acceptance_criteria[]`, optional `dependencies[]`, `technical_plan`.
   - **Cross-cutting requirements** (prompt §9a): a task that adds a screen /
     admin section / module with UI gets `ui_surface: "new_screen"` and a
     `cross_cutting[]` item with `dimension: "reachability"` — the menu entry
     and the inbound link from the parent screen (or an explicit URL-only
     statement) — plus the `security` / `performance` / `ui_ux` items that
     apply. The keys are the same four dimensions `teamwork-task-test` checks
     at QA time; the criterion text is in `detected_language`. The renderers put
     them under `### Prierezové požiadavky` (cs `### Průřezové požadavky`,
     en `### Cross-cutting requirements`) inside the acceptance section. Tasks
     without UI get no such items — do not pad.
   - **Framework line** (prompt §11): every task that writes or changes code
     ends its `technical_plan` with one `**Framework:**` line — respect the
     installed versions (`framework_summary` from Step 1.5) and their current
     idioms; a generic line when the summary is `null`. Plan only — never an
     acceptance criterion and never a `cross_cutting` item (the tester treats
     `framework` as advisory, so such a box could never be ticked).
   - Sum of `estimated_minutes` per tasklist must match DNR "Odhad pracnosti" (1 MD = 480 min).
     **This sum wins over the methodology, and that is deliberate** — see
     *Which rule wins* below before you try to reconcile the two.
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
   - `ui_surface is 'new_screen' but cross_cutting has no 'reachability' item`
     → add the reachability criterion (menu section + inbound link from the
     parent screen, in the DNR's own names). Do **not** "fix" it by dropping
     `ui_surface` from a task that really adds a screen.

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
   # `find`, not `ls docs/contracts/*/openapi.yaml` — with no contract yet, zsh
   # aborts that glob with "no matches found" instead of printing nothing.
   find docs/contracts -mindepth 2 -maxdepth 2 -name openapi.yaml 2>/dev/null
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
- **Cross-cutting requirements (since 1.6.0)** are additive too: a plan without
  `ui_surface` / `cross_cutting` renders byte-for-byte as before. They never
  touch the estimate — no minutes in a criterion — and the contract task never
  carries them.
- For DNR documents in non-WAME format (no "Rozšírenie č. N" headings), fall
  back to detecting any top-level numbered sections (`## 4.1`, `# Module 1`,
  etc.) and emit a warning.
- **Contract-first (since 1.3.0)** is fully additive. With `--no-contract`, or
  in a repo that is neither Laravel nor Ionic, the skill behaves byte-for-byte
  like before: no `contracts[]`, no `contract_ref`, no `### Kontrakt` block, and
  the XLSX/MD are unchanged. The `openapi.yaml` is emitted deterministically by
  `contract_emit.py` from the structured `contracts[]` you produce — you never
  hand-write YAML, which is what keeps it valid OpenAPI 3.1 even with `[DOPLNIŤ]`.
