"""Tests for the Markdown generator."""
import json_to_md


def test_renders_header(expected_plan):
    md = json_to_md.render(expected_plan)
    assert md.startswith("# DNR Strečnianska v1.2 — Teamwork Task Listy")
    assert "Klient: Družstvo lekárov" in md
    assert "Referencia: PON1107" in md


def test_renders_all_tasklists(expected_plan):
    md = json_to_md.render(expected_plan)
    for tl in expected_plan["tasklists"]:
        assert tl["name"] in md
    # 3 task lists, 25 tasks.
    assert md.count("## TASK LIST ") == 3
    # Each task has its own `### Task` heading.
    total_tasks = sum(len(tl["tasks"]) for tl in expected_plan["tasklists"])
    assert md.count("### Task ") == total_tasks


def test_acceptance_criteria_as_checkboxes(expected_plan):
    md = json_to_md.render(expected_plan)
    # Every acceptance criterion should appear with `- [ ]` prefix at least once.
    sample_crit = expected_plan["tasklists"][0]["tasks"][0]["acceptance_criteria"][0]
    assert f"- [ ] {sample_crit}" in md


def test_dependencies_block_when_present(expected_plan):
    # Task 1.5 has Závislosť in legacy data.
    md = json_to_md.render(expected_plan)
    has_dep_section = any("dependencies" in t for tl in expected_plan["tasklists"] for t in tl["tasks"])
    if has_dep_section:
        assert "### Závislosť" in md


def test_goal_and_technical_plan_appear(expected_plan):
    md = json_to_md.render(expected_plan)
    assert md.count("## Cieľ") >= 3
    assert md.count("## Technický popis") >= 3


def test_effort_summary_table(expected_plan):
    md = json_to_md.render(expected_plan)
    assert "| # | Task list | Tasky | MD | Hodín |" in md
    assert "| **Spolu** |" in md


def test_warnings_appended_when_present():
    plan = {
        "metadata": {"title": "x", "language": "sk", "total_md_estimate": 0.25},
        "tasklists": [{
            "name": "TL", "description": "desc",
            "tasks": [{
                "name": "task", "priority": "High", "estimated_minutes": 120,
                "goal": "g", "acceptance_criteria": ["a"], "technical_plan": "t",
            }],
        }],
        "warnings": ["Test warning"],
    }
    md = json_to_md.render(plan)
    assert "## Upozornenia z extrakcie" in md
    assert "Test warning" in md
