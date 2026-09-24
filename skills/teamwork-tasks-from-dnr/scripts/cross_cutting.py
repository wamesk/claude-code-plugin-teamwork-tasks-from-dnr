#!/usr/bin/env python3
"""
cross_cutting — shared rendering + checks for a task's cross-cutting requirements.

A DNR describes what a feature must *do*. It almost never says whether a new
screen can be *found* (menu entry, links from the parent screen), who may open
it, or what its list does with a year of data. `teamwork-task-test` checks
exactly those four things at QA time — its review dimensions `ui_ux`,
`performance`, `security` and `reachability`. A task may therefore carry
optional `cross_cutting` items keyed by the same four names, plus a
`ui_surface` flag saying whether it adds a new screen.

- `render_block()` produces the sub-heading block that the renderers insert
  INSIDE the task's acceptance-criteria section — after the ordinary criteria,
  before `### Závislosť` and before the first `---`. `teamwork-task-test` reads
  and ticks only the block between the acceptance heading and the first `---`,
  so the items stay tickable `- [ ]` lines.
- `issues()` is the validator gate: a task flagged `ui_surface: "new_screen"`
  must carry at least one `reachability` item. A deliberately URL-only page
  still passes — its reachability item simply says so.

Shared by `json_to_md.py` and `json_to_xlsx.py` (same pattern as
`description_summary.py` / `contract_render.py`) so the Markdown report and the
XLSX DESCRIPTION cell stay byte-identical. A task without `cross_cutting`
renders exactly as before. Stdlib only.
"""
from __future__ import annotations

# The keys are teamwork-task-test's review dimensions — never rename them.
# Its fifth dimension, `framework`, is deliberately absent: the tester treats it
# as an advisory recommendation (never ticked), so it lives in the technical
# plan only (prompt §11 "Framework line"), never as an acceptance checkbox.
DIMENSIONS = ("ui_ux", "performance", "security", "reachability")

# Render order: reachability first (the requirement most often missing from a
# spec), then who may use it, how it scales, how it looks.
RENDER_ORDER = ("reachability", "security", "performance", "ui_ux")

UI_SURFACES = ("new_screen", "existing_screen")

_LABELS = {
    "sk": {
        "heading": "Prierezové požiadavky",
        "reachability": "Dostupnosť", "security": "Bezpečnosť",
        "performance": "Výkon", "ui_ux": "UI/UX",
    },
    "cs": {
        "heading": "Průřezové požadavky",
        "reachability": "Dostupnost", "security": "Bezpečnost",
        "performance": "Výkon", "ui_ux": "UI/UX",
    },
    "en": {
        "heading": "Cross-cutting requirements",
        "reachability": "Reachability", "security": "Security",
        "performance": "Performance", "ui_ux": "UI/UX",
    },
}


def labels(language: str = "sk") -> dict:
    """Return the label table for a document language (unknown → sk)."""
    return _LABELS.get((language or "sk").lower(), _LABELS["sk"])


def _sorted_items(items) -> list[dict]:
    """Stable-sort items by RENDER_ORDER; unknown dimensions go last."""
    rank = {key: i for i, key in enumerate(RENDER_ORDER)}
    valid = [it for it in (items or []) if isinstance(it, dict)
             and str(it.get("criterion") or "").strip()]
    return sorted(valid, key=lambda it: rank.get(it.get("dimension"), len(rank)))


def render_block(items, language: str = "sk") -> str:
    """Render the `### <heading>` block for a task's `cross_cutting` items.

    Returns an empty string when there is nothing to render, so callers can
    skip it unconditionally and a task without the field is unchanged.
    Each line is `- [ ] **<Label> (<key>):** <criterion>` — the localised label
    for the reader, the teamwork-task-test key for the QA pass.
    """
    rows = _sorted_items(items)
    if not rows:
        return ""
    lab = labels(language)
    lines = [f"### {lab['heading']}"]
    for it in rows:
        key = it.get("dimension") or ""
        label = lab.get(key, key)
        lines.append(f"- [ ] **{label} ({key}):** {str(it['criterion']).strip()}")
    return "\n".join(lines)


def has_cross_cutting(plan: dict) -> bool:
    """True when any task in the plan carries at least one renderable item."""
    for tl in plan.get("tasklists", []) or []:
        for task in tl.get("tasks", []) or []:
            if _sorted_items(task.get("cross_cutting")):
                return True
    return False


def issues(plan: dict) -> list[str]:
    """Validator gate for the cross-cutting fields.

    Only reachability is enforced: a task that adds a new screen must say how a
    user gets there. The other three dimensions are judgement calls the
    extraction prompt asks for, not hard rules — enforcing them would push the
    model into boilerplate on tasks where they do not apply.
    """
    found: list[str] = []
    for tl_idx, tl in enumerate(plan.get("tasklists", []) or []):
        for t_idx, task in enumerate(tl.get("tasks", []) or []):
            if task.get("ui_surface") != "new_screen":
                continue
            dims = {it.get("dimension") for it in _sorted_items(task.get("cross_cutting"))}
            if "reachability" not in dims:
                found.append(
                    f"tasklists[{tl_idx}]/tasks[{t_idx}] '{task.get('name', '')}' — "
                    f"ui_surface is 'new_screen' but cross_cutting has no "
                    f"'reachability' item (name the menu entry and the inbound "
                    f"link from the parent screen, or state that the page is "
                    f"deliberately URL-only)")
    return found
