#!/usr/bin/env python3
"""
contract_render — shared rendering of the `### Kontrakt` block and the
`## Chýbajúce artefakty` section.

Shared by `json_to_md.py` and `json_to_xlsx.py` (same pattern as
`description_summary.py`) so the Markdown report and the XLSX DESCRIPTION cell
stay byte-identical.

- `render_contract_ref_block()` produces the canonical WAME contract footer
  appended to the end of a task's technical description whenever the task
  carries a `contract_ref`. The `Commit:` line is intentionally left as a
  `[DOPLNIŤ …]` placeholder — the plugin has no way to know the merge SHA at
  generation time.
- `render_missing_artifacts()` builds the standalone-mode section that lists the
  contract(s) that still need to be generated in the backend repo and the tasks
  waiting on them.

Stdlib only.
"""
from __future__ import annotations

DEFAULT_CONTRACT_DIR = "docs/contracts"

_CONTRACT_LABELS = {
    "sk": {
        "heading": "Kontrakt", "file": "Súbor", "version": "Verzia",
        "repo": "Repo", "commit": "Commit",
        "commit_todo": "[DOPLNIŤ po zmergovaní]",
    },
    "cs": {
        "heading": "Kontrakt", "file": "Soubor", "version": "Verze",
        "repo": "Repo", "commit": "Commit",
        "commit_todo": "[DOPLNIŤ po zmergování]",
    },
    "en": {
        "heading": "Contract", "file": "File", "version": "Version",
        "repo": "Repo", "commit": "Commit",
        "commit_todo": "[DOPLNIŤ after merge]",
    },
}

_MISSING_LABELS = {
    "sk": {
        "heading": "Chýbajúce artefakty",
        "intro": ("Tento beh prebehol mimo backend repozitára — API kontrakt sa "
                  "negeneroval. Dogeneruj ho spustením tohto skillu v BE repe. "
                  "Nasledujúce úlohy naň čakajú:"),
        "regenerate": "treba dogenerovať v BE repe (spusti tam tento skill)",
        "waiting": "Čakajúce úlohy",
    },
    "cs": {
        "heading": "Chybějící artefakty",
        "intro": ("Tento běh proběhl mimo backend repozitář — API kontrakt se "
                  "nevygeneroval. Vygeneruj ho spuštěním tohoto skillu v BE repu. "
                  "Následující úkoly na něj čekají:"),
        "regenerate": "je třeba vygenerovat v BE repu (spusť tam tento skill)",
        "waiting": "Čekající úkoly",
    },
    "en": {
        "heading": "Missing artifacts",
        "intro": ("This run happened outside a backend repository — the API "
                  "contract was not generated. Generate it by running this skill "
                  "in the BE repo. The following tasks depend on it:"),
        "regenerate": "must be generated in the BE repo (run this skill there)",
        "waiting": "Waiting tasks",
    },
}


def _labels(table: dict, language: str) -> dict:
    return table.get((language or "sk").lower(), table["en"] if "en" in table else table["sk"])


def render_contract_ref_block(contract_ref: dict, repo_name: str | None = None,
                              language: str = "sk",
                              contract_dir: str = DEFAULT_CONTRACT_DIR) -> str:
    """Render the `### Kontrakt` block for a task's `contract_ref`."""
    labels = _labels(_CONTRACT_LABELS, language)
    slug = (contract_ref or {}).get("feature_slug") or "[DOPLNIŤ]"
    version = (contract_ref or {}).get("version") or "0.1.0"
    repo = repo_name or (contract_ref or {}).get("repo") or "[DOPLNIŤ]"
    path = f"{contract_dir.rstrip('/')}/{slug}/openapi.yaml"
    return (
        f"### {labels['heading']}\n"
        f"- {labels['file']}: {path}\n"
        f"- {labels['version']}: {version}\n"
        f"- {labels['repo']}: {repo}\n"
        f"- {labels['commit']}: {labels['commit_todo']}"
    )


def append_contract_ref(technical_plan: str, contract_ref: dict | None,
                        repo_name: str | None = None, language: str = "sk",
                        contract_dir: str = DEFAULT_CONTRACT_DIR) -> str:
    """Return the technical plan text with the `### Kontrakt` block appended.

    A no-op (returns the text unchanged) when the task has no `contract_ref`,
    which keeps the renderers' output byte-identical for non-contract runs.
    """
    base = (technical_plan or "").rstrip()
    if not contract_ref:
        return base
    block = render_contract_ref_block(contract_ref, repo_name, language, contract_dir)
    if not base:
        return block
    return f"{base}\n\n{block}"


def render_missing_artifacts(plan: dict, language: str = "sk",
                             contract_dir: str = DEFAULT_CONTRACT_DIR) -> str:
    """Build the `## Chýbajúce artefakty` section for standalone-mode runs.

    Lists every contract slug referenced by a task (grouped) and the tasks
    waiting on it. Returns an empty string when no task references a contract.
    """
    labels = _labels(_MISSING_LABELS, language)
    by_slug: dict[str, list[str]] = {}
    for tasklist in plan.get("tasklists", []) or []:
        for task in tasklist.get("tasks", []) or []:
            ref = task.get("contract_ref")
            if not ref:
                continue
            slug = ref.get("feature_slug") or "[DOPLNIŤ]"
            by_slug.setdefault(slug, []).append(task.get("name", ""))

    if not by_slug:
        return ""

    dir_clean = contract_dir.rstrip("/")
    lines = [f"## {labels['heading']}", "", labels["intro"], ""]
    for slug, names in by_slug.items():
        lines.append(f"### {slug}")
        lines.append(f"- `{dir_clean}/{slug}/openapi.yaml` {labels['regenerate']}.")
        lines.append(f"- {labels['waiting']}:")
        for name in names:
            lines.append(f"  - {name}")
        lines.append("")
    return "\n".join(lines).rstrip()
