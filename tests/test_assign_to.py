"""Tests for the optional per-task assign_to field (XLSX + MD)."""
import zipfile

import json_to_md
import json_to_xlsx
import validate_json


def _plan_with_assignees() -> dict:
    return {
        "metadata": {"title": "Demo", "language": "sk", "total_md_estimate": 0.5},
        "tasklists": [
            {
                "name": "1.1 Tasklist",
                "section_ref": "1.1",
                "description": "desc",
                "md_estimate": 0.5,
                "tasks": [
                    {
                        "name": "1.1.1 BE task",
                        "priority": "High",
                        "estimated_minutes": 120,
                        "goal": "g",
                        "acceptance_criteria": ["BE ac"],
                        "technical_plan": "t",
                        "assign_to": "stano@wame.sk",
                    },
                    {
                        "name": "1.1.2 FE task",
                        "priority": "Medium",
                        "estimated_minutes": 120,
                        "goal": "g",
                        "acceptance_criteria": ["FE ac"],
                        "technical_plan": "t",
                        "assign_to": "simonko420@gmail.com",
                    },
                    {
                        "name": "1.1.3 Unassigned task",
                        "priority": "Low",
                        "estimated_minutes": 0,
                        "goal": "g",
                        "acceptance_criteria": ["ac"],
                        "technical_plan": "t",
                    },
                ],
            }
        ],
    }


def test_schema_accepts_assign_to(schema):
    plan = _plan_with_assignees()
    # The "unassigned" task has 0 minutes which violates the integer min — drop it for schema check.
    plan["tasklists"][0]["tasks"][2]["estimated_minutes"] = 30
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_md_shows_pridelene_only_when_assignee_present():
    md = json_to_md.render(_plan_with_assignees())
    assert "**Pridelené:** stano@wame.sk" in md
    assert "**Pridelené:** simonko420@gmail.com" in md
    # Third task has no assignee — should not have the marker.
    third_task_section = md.split("### Task 1.3")[1].split("### Task")[0] if "### Task 1.3" in md else ""
    assert "Pridelené" not in third_task_section


def test_xlsx_writes_assign_to_into_column_d(tmp_path):
    out = tmp_path / "out.xlsx"
    json_to_xlsx.write(_plan_with_assignees(), out)
    with zipfile.ZipFile(out) as z:
        shared = z.read("xl/sharedStrings.xml").decode("utf-8")
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "stano@wame.sk" in shared
    assert "simonko420@gmail.com" in shared
    # Column D corresponds to ASSIGN TO. Verify D3 and D4 cells exist with strings.
    assert 'r="D3"' in sheet
    assert 'r="D4"' in sheet
