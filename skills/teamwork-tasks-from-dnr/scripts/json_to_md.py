#!/usr/bin/env python3
"""
json_to_md — render a Teamwork tasks plan JSON to a human-readable Markdown.

Layout mirrors the gold-standard format the team uses for review:
1. Document header (title, source, project ref).
2. Conventions block.
3. Effort summary table.
4. Per tasklist: original DNR text (blockquote) + per-task structure with
   Acceptance criteria (checkbox list), optional Dependencies, Goal, Technical
   plan.
"""
from __future__ import annotations

from pathlib import Path

from description_summary import append_summary_to_description


def render(plan: dict) -> str:
    """Return the Markdown text for the plan."""
    md = plan.get("metadata", {})
    lines: list[str] = []

    title = md.get("title") or "Teamwork Tasks Plan"
    lines.append(f"# {title} — Teamwork Task Listy")
    lines.append("")
    if md.get("source_dnr_path"):
        lines.append(f"Zdroj: `{md['source_dnr_path']}`")
    if md.get("client"):
        lines.append(f"Klient: {md['client']}")
    if md.get("project_ref"):
        lines.append(f"Referencia: {md['project_ref']}")
    lines.append("")
    lines.append("Sprievodný súbor `*_TeamworkTasks.xlsx` v tom istom adresári je "
                 "1:1 import-ready pre Teamwork (Options → Import → Microsoft Excel).")
    lines.append("")

    lines.append("## Konvencie")
    lines.append("")
    lines.append("- **Akceptačné kritériá** sú checkbox list (`- [ ]`), píše sa z pohľadu používateľa.")
    lines.append("- **Cieľ** je 1–3 vety pre rýchle pochopenie účelu tasku (Plan-mode friendly).")
    lines.append("- **Technický popis** obsahuje cesty súborov, snippety, edge cases.")
    lines.append("- **Závislosť** (ak je) je samostatná pod-sekcia v akceptačných kritériách.")
    lines.append("")

    lines.append("## Mapovanie pracnosti")
    lines.append("")
    lines.append("| # | Task list | Tasky | MD | Hodín |")
    lines.append("|---|---|---|---|---|")
    total_minutes = 0
    for i, tl in enumerate(plan.get("tasklists", []), start=1):
        tl_minutes = sum(int(t.get("estimated_minutes", 0)) for t in tl.get("tasks", []))
        total_minutes += tl_minutes
        md_value = tl.get("md_estimate") or (tl_minutes / 480)
        lines.append(f"| {i} | {tl.get('name', '')} | {len(tl.get('tasks', []))} | "
                     f"{md_value:g} | {tl_minutes / 60:.1f} |")
    lines.append(f"| **Spolu** | | **{sum(len(tl.get('tasks', [])) for tl in plan.get('tasklists', []))}** | "
                 f"**{total_minutes / 480:g}** | **{total_minutes / 60:.1f}** |")
    lines.append("")

    language = (md.get("language") or "sk").lower()
    for i, tl in enumerate(plan.get("tasklists", []), start=1):
        lines.append("---")
        lines.append("")
        lines.append(f"## TASK LIST {i}: {tl.get('name', '')}")
        lines.append("")
        lines.append("### Pôvodné znenie DNR")
        lines.append("")
        description_with_summary = append_summary_to_description(tl, language=language)
        for paragraph in description_with_summary.strip().split("\n"):
            lines.append("> " + paragraph if paragraph else ">")
        lines.append("")

        for j, task in enumerate(tl.get("tasks", []), start=1):
            hours = int(task.get("estimated_minutes", 0)) / 60
            lines.append(f"### Task {i}.{j} — {task.get('name', '')}")
            lines.append("")
            lines.append(f"**Priorita:** {task.get('priority', '')} · "
                         f"**Odhad:** {hours:g}h ({task.get('estimated_minutes', 0)} min)")
            lines.append("")

            lines.append("## Akceptačné kritériá")
            for crit in task.get("acceptance_criteria", []):
                lines.append(f"- [ ] {crit}")

            deps = task.get("dependencies") or []
            if deps:
                lines.append("")
                lines.append("### Závislosť")
                for d in deps:
                    lines.append(f"- {d}")

            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## Cieľ")
            lines.append((task.get("goal") or "").strip())
            lines.append("")
            lines.append("## Technický popis")
            lines.append((task.get("technical_plan") or "").rstrip())
            lines.append("")

    warnings = plan.get("warnings") or []
    if warnings:
        lines.append("---")
        lines.append("")
        lines.append("## Upozornenia z extrakcie")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


def write(plan: dict, output_path: Path) -> Path:
    """Write plan as Markdown to output_path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(plan), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    out = write(plan, Path(args.out))
    print(f"Wrote: {out}")
