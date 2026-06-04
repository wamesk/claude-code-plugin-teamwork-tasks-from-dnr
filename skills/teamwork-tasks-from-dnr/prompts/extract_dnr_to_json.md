# DNR → Teamwork Tasks JSON — Extraction Prompt

You are extracting a structured project plan from a "Detailný návrh riešenia"
(Slovak software requirements document — also possible in Czech or English).

## Input

You will receive the plain text of a DNR document (extracted from `.docx`,
`.pdf`, or `.md`).

## Output

A single JSON object matching `json_schema.json` (in the same `prompts/`
folder). Do **not** wrap the JSON in markdown fences or commentary — output
raw JSON only.

## Extraction rules

### 1. Tasklists = extension sections

- A WAME-format DNR has sections like "**Rozšírenie č. 1 — <name>**" inside
  section 4 ("Popis riešenia a rozsah").
- Each such extension → one tasklist.
- If the document uses different headings (e.g. "Module 1", "Feature A",
  "Funkcia X"), treat them analogously. Number from 1 in document order.
- If the document has only one feature or no clear sectioning, create a
  single tasklist named after the document title.

#### Tasklist `name` format

The tasklist `name` MUST start with the DNR section number followed by a
single space and the descriptive title. Examples:

- ✅ `"4.1 Rozšírenie dátového modelu OM o nové atribúty"`
- ✅ `"4.2 Automatické párovanie platieb z banky"`
- ✅ `"4.3 Ročné zúčtovanie služieb"`
- ❌ `"Rozšírenie dátového modelu OM o nové atribúty"` (no section prefix)
- ❌ `"Rozšírenie #1 — Ročný zálohový predpis (DNR 4.1)"` (section ref in
  parentheses at the end — wrong position, hard to scan in Teamwork lists)

If the DNR does not assign a section number to the extension (rare), fall
back to a sequential `1`, `2`, … prefix in document order. Set
`section_ref` to the same value used in the name prefix.

### 2. Tasklist `description`

The full verbatim DNR text from that extension section, including:
- Business purpose (Biznisový účel)
- Decisions table (Zásadné rozhodnutia)
- Use case scenarios (Scenáre použitia)
- Effort estimate (Odhad pracnosti)
- Any side-note boxes (Edge-case, Dospresnenie, …)

Format as plain text with light structure:
```
ROZŠÍRENIE Č. N — <NAME> (DNR sekcia X.Y)

** X.Y.1 Biznisový účel **
<paragraph>

** X.Y.2 Zásadné rozhodnutia **
• <key>: <value>
• <key>: <value>
...
```

Use `**` (Markdown bold) for sub-headings and `•` for bullets. Always wrap the
sub-heading text in `**` with a single space on each side (e.g. `** 4.1.1
Biznisový účel **`). Do NOT use `==` — older versions of this skill used
heredoc-style `==` headings but they don't render in Teamwork. Preserve
original wording — do not paraphrase. Do not translate.

**Note on summary acceptance criteria:** the build step (`json_to_md.py` /
`json_to_xlsx.py`) automatically appends a `** Sumár akceptačných kritérií **`
section to every tasklist description. It picks one representative acceptance
criterion from each High/Medium priority task in that tasklist, prefixed with
the task's section number. **You do NOT need to add this section manually** —
just write clean per-task `acceptance_criteria` arrays and the renderers will
synthesize the summary. Heading text adapts to the detected language (sk/cs/en).

### 3. Tasklist `section_ref` and `md_estimate`

- `section_ref` — original section number from DNR (e.g. `"4.1"`).
- `md_estimate` — man-days from "Odhad pracnosti" line (e.g. `2.5`).

### 4. Tasks per tasklist

Decompose each tasklist into **6 to 12 actionable engineering tasks**. Each
task should be **completable in 15 minutes to 8 hours** (15 to 480 minutes).

Tasks must cover, in order:
1. **Data foundation** — DB migrations, enums, schema changes.
2. **Domain models** — Eloquent models, relations, observers.
3. **Core business logic** — services, calculators, builders.
4. **UI / admin actions** — Nova actions, resources, filters.
5. **Output generation** — PDF/email templates, file generators.
6. **Bulk / batch operations** — bulk Nova actions, scheduled jobs.
7. **Side effects / integrations** — mailables, console commands, API calls.
8. **Audit / compliance / observability** (optional, often Low priority).
9. **Tests** (always last task in tasklist).

If a step is not needed in the given extension, skip it.

### 5. Task `name`

**Business-friendly** in the detected language. The name must be understandable
to a project manager or client, NOT just a developer.

#### Task `name` format

Every task `name` MUST start with a hierarchical number derived from the
parent tasklist's `section_ref` plus the 1-based task index within that
tasklist, followed by a single space and the business-friendly title.

- Tasklist `section_ref = "4.1"` → tasks are named `"4.1.1 …"`,
  `"4.1.2 …"`, …, `"4.1.N …"`.
- Tasklist `section_ref = "4.2"` → tasks are named `"4.2.1 …"`, …
- Use the same numbering scheme even if the DNR doesn't enumerate
  sub-tasks — the index is purely structural so PMs can match Teamwork
  tasks back to the DNR section by glance.

✅ Good:
- "4.1.1 Príprava systémových štruktúr pre ročný zálohový predpis"
- "4.1.4 Funkcia 'Odoslať predpis e-mailom' v detaile zmluvy"
- "4.2.5 Automatické párovanie platieb so splátkami"

❌ Bad (no section number, or technical jargon):
- "Príprava systémových štruktúr pre ročný zálohový predpis" (missing
  `4.1.1` prefix)
- "DB migrations + enum"
- "Add InvoiceScheduleInstallment model"
- "PaymentMatcher service"

### 6. Task `priority`

- **High** — blocking, data foundation, critical business logic, core services, anything other tasks depend on.
- **Medium** — bulk actions, UI polish, mails, manual-edit features, tests, side-effects.
- **Low** — optional / nice-to-have, audit logs, observability, edge-case handling.

Apply config hints (`priorities.high_keywords`, etc.) if provided.

### 7. Task `estimated_minutes`

- Integer, multiple of 15.
- Sum per tasklist must equal `md_estimate * 480` minutes (1 MD = 8h = 480 min).
- Distribute proportionally to complexity (e.g. a calculator service ≈ 5h, a
  migration ≈ 1-2h, tests ≈ 1-3h).

### 8. Task `goal`

1-3 sentences. Frame for an engineer **starting work cold**:
- What's being built (entity, service, action).
- Which existing pattern in the codebase to reuse (be specific if DNR hints at it).
- Key constraint or dependency.

Example:
> Vytvoriť Eloquent model `InvoiceScheduleInstallment` s relations na `Invoice`
> a `InvoicePayment` a doplniť relations na opačnej strane. Mirror logiky
> existujúceho `ChangeInvoiceStatusByPaymentJob` pre prepočet stavu splátky
> podľa pripojených platieb (UNPAID → PARTIALLY_PAID → PAID → OVERPAY).

### 9. Task `acceptance_criteria`

3-8 bullet points **from the user's / client's perspective**. Each item is a
single short sentence. They become checkbox items in the output MD.

✅ Good (business outcome):
- "Pre každý ročný predpis vie systém zobraziť zoznam splátok s aktuálnym stavom."
- "Pri každej platbe sa stav príslušnej splátky automaticky aktualizuje."

❌ Bad (technical detail — that belongs in `technical_plan`):
- "Add HasMany relation to Invoice model"
- "Implement recalculateStatus() method"

### 10. Task `dependencies` (optional)

Reference earlier tasks **by name** that must be done first. Use only when the
dependency is non-obvious (within the same tasklist, task order already
implies dependency).

### 10a. Task `assign_to` (optional)

E-mail (or Teamwork display name) of the user this task should be assigned
to. Populated in the `ASSIGN TO` column of the import XLSX and shown in the
MD report as `**Pridelené:** <value>`. Useful when the project has a clear
BE/FE split — for example `assign_to: "backend.dev@team.sk"` for Laravel
tasks and `assign_to: "frontend.dev@team.sk"` for Ionic / React tasks. Leave
unset to let the PM assign the task manually after import.

### 11. Task `technical_plan`

Markdown-formatted detailed plan for the implementer:
- File paths (`app/Models/Foo.php`, `database/migrations/<dnes>_create_foo_table.php`).
- Code snippets with language hint (` ```php `, ` ```bash `).
- Sub-sections via `### Header`.
- Edge cases at the end.
- Mention specific existing files to reference (e.g. "pattern z `GenerateInvoiceTrait::createInvoice()`").

This is the developer's full execution recipe.

### 12. Metadata

```json
"metadata": {
  "title": "<best-effort from DNR header — e.g. 'DNR Strečnianska v1.2'>",
  "client": "<from DNR header, e.g. 'Družstvo lekárov — Strečnianska'>",
  "project_ref": "<from DNR header, e.g. 'PON1107'>",
  "language": "<sk|en|cs>",
  "total_md_estimate": <sum of all tasklist md_estimate>,
  "source_dnr_path": "<as passed in>",
  "generated_at": "<ISO-8601 timestamp>"
}
```

## Edge cases

- **DNR has 1 section only** → 1 tasklist, more tasks (up to 15).
- **DNR has 7+ sections** → 7+ tasklists, fewer tasks each (6-8).
- **"Odhad pracnosti" missing** → estimate based on complexity, set
  `md_estimate` to your best guess, note this in the warning.
- **Variants A/B in a section** → encode as separate tasks within the same
  tasklist with `goal` explaining the chosen variant.
- **Workshop/clarification required mentioned in DNR** → add `dependencies`
  note like "Pred začatím prebehne workshop s klientom (DNR …)".
- **Document is not in sk/cs/en** → emit warning, default to `en`.

## Final check

Before returning, verify:
- [ ] JSON parses.
- [ ] Sum of `estimated_minutes` per tasklist matches `md_estimate * 480`.
- [ ] Every task has all required fields.
- [ ] Language is consistent across all output strings.
- [ ] Task names are business-friendly.
- [ ] Acceptance criteria are user-facing, not implementation details.
- [ ] Each tasklist `name` starts with `<section_ref> ` (e.g. `4.1 `).
- [ ] Each task `name` starts with `<section_ref>.<index> ` (e.g. `4.1.1 `).
- [ ] Description sub-headings use `** … **` bold markers, not `==`.
