# teamwork-tasks-from-dnr

> Claude Code plugin + Claude.ai Skill — generuje Teamwork.com import-ready zoznam taskov (XLSX) a sprievodný plán (Markdown) z dokumentu **Detailný návrh riešenia (DNR)**.

## Čo to robí

Z DNR dokumentu (`.docx`, `.pdf`, `.md`):

1. Claude rozpozná štruktúru dokumentu (rozšírenia, sekcie, scenáre).
2. Vygeneruje pre každé rozšírenie **task list** a 6–12 detailných **taskov** s:
   - **business-friendly názvom** (zrozumiteľný aj pre PM/klienta),
   - **akceptačnými kritériami** ako `- [ ]` checkbox listom (od v1.6.0 aj s pod-sekciou
     `### Prierezové požiadavky` — dostupnosť z menu a preklikmi, bezpečnosť, výkon, UI/UX),
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
/teamwork-tasks-from-dnr ~/projects/foo/DNR_v1.0.docx --no-contract   # preskoč contract-first flow
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

## Contract-first (od v1.3.0)

WAME backend (Laravel) a frontend (Ionic Vue) žijú v **dvoch samostatných
repozitároch**, takže FE task je dnes blokovaný, kým BE nedodá funkčné API.
Skill preto vie z DNR vygenerovať **kostru API kontraktu ešte pred
implementáciou**, aby BE a FE tasky bežali paralelne.

Skill najprv **deteguje typ repozitára** (`--detect-repo`) a podľa toho:

| Režim | Detekcia | Správanie |
|---|---|---|
| **backend** | `composer.json` má `laravel/framework` | **Vygeneruje** kontrakt z DNR |
| **frontend** | `package.json` má `@ionic/vue` / `@ionic/core` | **Odkáže** na existujúci kontrakt (negeneruje) |
| **standalone** | mimo repa / ani jedno | Negeneruje; do MD plánu pridá `## Chýbajúce artefakty` |

V **backend** režime vzniknú (idempotentne — existujúce súbory sa neprepíšu,
vznikne `*.proposed` + diff):

```
docs/contracts/
├── _shared/
│   └── wame-envelope.yaml        # WameSuccess / WameError obálka (raz na projekt)
└── <feature-slug>/
    ├── openapi.yaml              # OpenAPI 3.1 kostra (Sanctum bearer, $ref na obálku)
    └── data-model.md            # entity, polia, vzťahy, indexy (podklad pre migrácie)
```

- `openapi.yaml` je **garantovane validný OpenAPI 3.1 aj s `[DOPLNIŤ]`** — YAML
  emituje deterministicky Python (žiadna YAML závislosť), takže placeholder
  nikdy nerozbije štruktúru. Neisté endpointy nesú `x-wame-status: draft`.
- Do plánu pribudne task **„Definovať API kontrakt"** ako predchodca všetkých
  BE aj FE taskov, ktoré sa kontraktu dotýkajú; každý taký task má v popise
  sekciu `### Kontrakt` (cesta, verzia, repo, `Commit: [DOPLNIŤ po zmergovaní]`).
- **FE task** závisí od tasku kontraktu (nie od dokončenia BE) a do dodania BE
  pracuje proti mocku odvodenému z kontraktu.

Na začiatku behu sa skill spýta 3 otázky (chybový HTTP status, jazyk
`description`, cesta ku kontraktu). Celé to vypneš cez `--no-contract`
(správanie ako pred v1.3.0). Plugin **negeneruje commity ani nepushuje** —
zmergovanie kontraktu a doplnenie `Commit:` riadku je na tebe.

## Prierezové požiadavky (od v1.6.0)

DNR hovorí, čo má funkcia robiť, no málokedy povie, či sa nová obrazovka dá
*nájsť*. Tasky, ktoré pridávajú obrazovku, sekciu administrácie alebo modul s UI,
sú preto v JSON pláne označené `ui_surface: "new_screen"` a musia mať kritérium
`reachability`: položku v menu a preklik z nadradenej obrazovky, prípadne
výslovné vyhlásenie „zámerne len cez URL". `validate_json.py` plán zamietne, ak
nová obrazovka takéto kritérium nemá. Kritériá `security`, `performance` a
`ui_ux` pribudnú tam, kde sa týkajú. Kľúče zodpovedajú štyrom dimenziám, ktoré
`teamwork-task-test` kontroluje pri QA.

Renderery ich vkladajú do sekcie akceptačných kritérií pred prvé `---`, aby ich
`teamwork-task-test` vedel odškrtnúť. Nadpis sa riadi jazykom dokumentu:
`### Prierezové požiadavky` (sk), `### Průřezové požadavky` (cs),
`### Cross-cutting requirements` (en). Každý riadok má tvar
`- [ ] **Dostupnosť (reachability):** …`. Plán bez týchto polí sa vyrenderuje
presne ako doteraz. Odhad sa do kritéria nikdy nedostane.

Technický popis každého tasku, ktorý píše alebo mení kód, navyše končí riadkom
`**Framework:**`. Ten hovorí, že treba rešpektovať verzie frameworkov
nainštalované v repozitári a ich aktuálne idiómy. Verzie deteguje
`--detect-repo` z `composer.lock`, `package.json` a spol.; mimo repozitára ide o
všeobecný riadok. Patrí len do plánu, nikdy nie je akceptačným kritériom.

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
- [x] Phase 2 — Contract-first flow (repo detekcia + OpenAPI 3.1 kostra + data-model, od v1.3.0)
- [ ] Phase 3 — Generovanie TypeScript typov / Axios klienta z kontraktu na FE
- [ ] Phase 3 — Generovanie Pest contract testov (dnes len návrh v popise BE tasku)
- [ ] Phase 2 — Teamwork API integration (cez Teamwork MCP server: `twprojects-create_tasklist`, `twprojects-create_task`)
- [ ] Phase 2 — `--update-existing` diff režim pre DNR v1.X → v1.Y — **pri
      prepise existujúceho tasku musí pôvodný popis prežiť doslovne, vrátane
      inline obrázkov (`![image.png](https://tw-inlineimages.s3-accelerate.amazonaws.com/...)`),
      HTML `<img>` tagov a odkazov na prílohy.** Screenshot vložený do popisu
      nie je príloha a nikde inde sa nenachádza — zahodenie odkazu ho zmaže.
- [ ] Phase 2 — Git hook pre auto-aktualizáciu plánu pri zmene DNR

## Licencia

MIT — pozri `LICENSE`.
