# teamwork-tasks-from-dnr

> Claude Code plugin + Claude.ai Skill — generuje Teamwork.com import-ready zoznam taskov (XLSX) a sprievodný plán (Markdown) z dokumentu **Detailný návrh riešenia (DNR)**.

## Čo to robí

Z DNR dokumentu (`.docx`, `.pdf`, `.md`):

1. Claude rozpozná štruktúru dokumentu (rozšírenia, sekcie, scenáre).
2. Vygeneruje pre každé rozšírenie **task list** a 6–12 detailných **taskov** s:
   - **business-friendly názvom** (zrozumiteľný aj pre PM/klienta),
   - **akceptačnými kritériami** ako `- [ ]` checkbox listom,
   - **cieľom** (1–3 vety pre rýchle pochopenie pri implementácii),
   - **technickým popisom** (cesty súborov, kód-snippety, edge cases),
   - **odhadom v minútach** zhodným s "Odhad pracnosti" z DNR.
3. Výstup:
   - `<basename>_TeamworkTasks.xlsx` — pripravený na Teamwork import (Options → Import → Microsoft Excel).
   - `<basename>_TeamworkTasks.md` — čitateľný plán pre review, PR description, alebo direct kopírovanie do Claude Code Plan mode.

## Inštalácia

### Claude Code (cez WAME marketplace)

```
/plugin marketplace add wamesk/claude-code
/plugin install teamwork-tasks-from-dnr@wame
```

### Claude.ai (online)

1. Stiahni priečinok `skills/teamwork-tasks-from-dnr/` z tohto repa.
2. Nahraj ho v Claude.ai Settings → Capabilities → Skills.

## Použitie

### Claude Code

```
/teamwork-tasks-from-dnr ~/projects/foo/DNR_v1.0.docx
/teamwork-tasks-from-dnr ~/projects/foo/DNR_v1.0.docx --output-dir=docs/plan
/teamwork-tasks-from-dnr ~/projects/foo/DNR_v1.0.docx --lang=en
/teamwork-tasks-from-dnr --init                          # vytvor per-project config
/teamwork-tasks-from-dnr --from-json plan.json           # skip LLM, regeneruj výstupy
```

### Claude.ai chat

Nahraj DNR súbor + napíš:

> Vytvor mi Teamwork tasky z tejto DNR.

Skill sa zapne podľa popisu a vygeneruje oba výstupy na stiahnutie.

## Vstup

| Formát | Status | Závislosť |
|---|---|---|
| `.docx` | ✅ Plne podporované | stdlib `zipfile` + `xml.etree` (žiadne deps) |
| `.md` / `.txt` | ✅ Plne podporované | stdlib |
| `.pdf` | ⚠️ Vyžaduje `pdftotext` (poppler-utils) | `brew install poppler` |

## Výstup

| Súbor | Účel |
|---|---|
| `*_TeamworkTasks.xlsx` | Teamwork.com bulk import (10 stĺpcov: TASKLIST, TASK, DESCRIPTION, ASSIGN TO, START DATE, DUE DATE, PRIORITY, ESTIMATED TIME, TAGS, STATUS) |
| `*_TeamworkTasks.md` | Human-readable plán s pôvodným znením DNR (blockquote) + per-task štruktúrou |

## Konfigurácia

Per-project config v `~/.claude/plugins/data/teamwork-tasks-from-dnr-wamesk/<project-hash>/config.json`. Vytvoríš ho:

```
/teamwork-tasks-from-dnr --init
```

Kľúčové nastavenia v `config.example.json`:

- `output_dir` — kam ukladať výstupy (default `docs`).
- `language` — `auto` (detekcia z DNR), alebo `sk`/`en`/`cs`.
- `priorities` — kľúčové slová pre auto-detekciu priority (High/Medium/Low).
- `xlsx_layout` — farby, šírky stĺpcov.
- `include_tags` — či sa do XLSX má zapísať stĺpec TAGS (default `false`).

## Architektúra

```
USER → /teamwork-tasks-from-dnr DNR.docx
         │
         ▼
       SKILL.md (orchestruje Claude)
         │
         ├── python3 teamwork_tasks.py --plan --dnr DNR.docx
         │     → vráti plain_text + metadata
         │
         ├── Claude (LLM): extract → JSON podľa schémy
         │
         └── python3 teamwork_tasks.py --build --json plan.json --output-dir docs
               → MD + XLSX
```

## Vývoj

```bash
git clone https://github.com/wamesk/claude-code-plugin-teamwork-tasks-from-dnr
cd claude-code-plugin-teamwork-tasks-from-dnr
python3 -m pytest tests/ -v
```

## Roadmap

- [x] Phase 1 — LLM extractor + XLSX/MD generátor (stdlib)
- [ ] Phase 2 — Teamwork API integration (cez Teamwork MCP server: `twprojects-create_tasklist`, `twprojects-create_task`)
- [ ] Phase 2 — `--update-existing` diff režim pre DNR v1.X → v1.Y
- [ ] Phase 2 — Git hook pre auto-aktualizáciu plánu pri zmene DNR

## Licencia

MIT — pozri `LICENSE`.
