"""Tests for the stdlib XLSX generator (no openpyxl in production code; the
test suite uses openpyxl as a verification-only dependency)."""
import pytest

import json_to_xlsx

openpyxl = pytest.importorskip("openpyxl")


def test_xlsx_writes_valid_file(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    assert out.exists()
    assert out.stat().st_size > 1000

    wb = openpyxl.load_workbook(out)
    ws = wb.active
    assert ws.title == "Tasks"
    assert ws.max_column == 10
    # Header + 3 tasklist headers + 25 tasks = 29 rows.
    assert ws.max_row == 29


def test_header_row_values(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    header = [ws.cell(row=1, column=c).value for c in range(1, 11)]
    assert header == [
        "TASKLIST", "TASK", "DESCRIPTION", "ASSIGN TO", "START DATE",
        "DUE DATE", "PRIORITY", "ESTIMATED TIME", "TAGS", "STATUS",
    ]


def test_tags_column_empty_by_default(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx", include_tags=False)
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    # No row should have a value in column I (TAGS) under default behavior.
    for r in range(2, ws.max_row + 1):
        assert ws.cell(row=r, column=9).value in (None, ""), \
            f"Row {r}: TAGS should be empty, got {ws.cell(row=r, column=9).value!r}"


def test_task_description_contains_checkbox_criteria(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    # Row 3 = first task.
    desc = ws.cell(row=3, column=3).value
    assert "## Akceptačné kritériá" in desc
    assert "- [ ] " in desc
    assert "## Cieľ" in desc
    assert "## Technický popis" in desc
    # `---` separator between acceptance and goal.
    parts = desc.split("\n---\n")
    assert len(parts) >= 2


def test_task_priority_and_minutes(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    # Row 3 = first task of first tasklist.
    first_task = expected_plan["tasklists"][0]["tasks"][0]
    assert ws.cell(row=3, column=7).value == first_task["priority"]
    assert ws.cell(row=3, column=8).value == first_task["estimated_minutes"]


def test_status_always_active(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    for r in range(2, ws.max_row + 1):
        assert ws.cell(row=r, column=10).value == "Active"


def test_total_minutes_matches_plan(expected_plan, tmp_path):
    out = json_to_xlsx.write(expected_plan, tmp_path / "out.xlsx")
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    total = 0
    for r in range(2, ws.max_row + 1):
        val = ws.cell(row=r, column=8).value
        if isinstance(val, int):
            total += val
    expected_total = sum(int(t["estimated_minutes"])
                         for tl in expected_plan["tasklists"]
                         for t in tl["tasks"])
    assert total == expected_total == 2880
