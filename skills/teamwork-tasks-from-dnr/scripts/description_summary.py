#!/usr/bin/env python3
"""
description_summary — build a synthesized "Summary of acceptance criteria"
section appended to each tasklist description.

The summary picks one representative acceptance criterion from every High and
Medium priority task in the tasklist, prefixed with the task's section number
so PMs can scan what the whole feature delivers without opening every task.

Shared by `json_to_md.py` and `json_to_xlsx.py` so the MD report and the XLSX
DESCRIPTION cell stay byte-identical.
"""
from __future__ import annotations

LANGUAGE_HEADINGS = {
    "sk": "Sumár akceptačných kritérií (z hlavných úloh)",
    "cs": "Souhrn akceptačních kritérií (z hlavních úkolů)",
    "en": "Acceptance criteria summary (from key tasks)",
}

# Priorities that contribute to the summary. Low-priority tasks are
# intentionally excluded to keep the summary focused on the "must-have"
# outcomes.
INCLUDED_PRIORITIES = {"High", "Medium"}


def _task_short_ref(task_name: str) -> str:
    """Return the leading section number from a task name, e.g. '4.1.3'.

    Falls back to the first token if no recognisable number prefix is present.
    """
    name = (task_name or "").strip()
    if not name:
        return ""
    first_token = name.split(" ", 1)[0]
    return first_token


def build_summary_section(tasklist: dict, language: str = "sk") -> str:
    """Render a Markdown-formatted summary section for the given tasklist.

    Returns an empty string when no eligible tasks exist (e.g. all Low
    priority) so callers can safely concatenate the result unconditionally.
    The output uses the same `** … **` heading + `•` bullet style as the
    rest of tasklist descriptions, so Teamwork renders it consistently.
    """
    heading = LANGUAGE_HEADINGS.get(language, LANGUAGE_HEADINGS["sk"])
    bullets: list[str] = []
    for task in tasklist.get("tasks", []) or []:
        if task.get("priority") not in INCLUDED_PRIORITIES:
            continue
        criteria = task.get("acceptance_criteria") or []
        if not criteria:
            continue
        ref = _task_short_ref(task.get("name", ""))
        first = str(criteria[0]).strip()
        if not first:
            continue
        prefix = f"[{ref}] " if ref else ""
        bullets.append(f"• {prefix}{first}")

    if not bullets:
        return ""

    return f"** {heading} **\n" + "\n".join(bullets)


def append_summary_to_description(tasklist: dict, language: str = "sk") -> str:
    """Return the tasklist description with the summary section appended.

    Separates the original description and the summary with a single blank
    line so the two blocks render as distinct paragraphs in both Teamwork and
    plain Markdown viewers.
    """
    base = (tasklist.get("description") or "").rstrip()
    summary = build_summary_section(tasklist, language=language)
    if not summary:
        return base
    if not base:
        return summary
    return f"{base}\n\n{summary}"
