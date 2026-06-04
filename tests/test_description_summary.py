"""Tests for the synthesized 'Summary of acceptance criteria' section."""
import description_summary
import json_to_md
import json_to_xlsx


def _tasklist_with_priorities() -> dict:
    return {
        "name": "4.1 Demo tasklist",
        "section_ref": "4.1",
        "description": "ROZŠÍRENIE Č. 1 — Demo (DNR sekcia 4.1)\n\n** 4.1.1 Biznisový účel **\nLorem ipsum.",
        "md_estimate": 1.0,
        "tasks": [
            {
                "name": "4.1.1 High priority task",
                "priority": "High",
                "estimated_minutes": 120,
                "goal": "g",
                "acceptance_criteria": [
                    "High AC representing the deliverable.",
                    "Secondary AC that should not appear in summary.",
                ],
                "technical_plan": "t",
            },
            {
                "name": "4.1.2 Medium priority task",
                "priority": "Medium",
                "estimated_minutes": 120,
                "goal": "g",
                "acceptance_criteria": ["Medium AC line."],
                "technical_plan": "t",
            },
            {
                "name": "4.1.3 Low priority task",
                "priority": "Low",
                "estimated_minutes": 120,
                "goal": "g",
                "acceptance_criteria": ["Low AC should NOT appear in summary."],
                "technical_plan": "t",
            },
            {
                "name": "4.1.4 High task with empty AC",
                "priority": "High",
                "estimated_minutes": 120,
                "goal": "g",
                "acceptance_criteria": [],
                "technical_plan": "t",
            },
        ],
    }


def test_summary_includes_only_high_and_medium():
    tl = _tasklist_with_priorities()
    summary = description_summary.build_summary_section(tl, language="sk")
    assert "[4.1.1] High AC representing the deliverable." in summary
    assert "[4.1.2] Medium AC line." in summary
    assert "Low AC should NOT appear" not in summary


def test_summary_takes_only_first_ac_per_task():
    tl = _tasklist_with_priorities()
    summary = description_summary.build_summary_section(tl, language="sk")
    assert "Secondary AC that should not appear in summary." not in summary


def test_summary_uses_localised_heading():
    tl = _tasklist_with_priorities()
    assert "Sumár akceptačných kritérií" in description_summary.build_summary_section(tl, language="sk")
    assert "Souhrn akceptačních kritérií" in description_summary.build_summary_section(tl, language="cs")
    assert "Acceptance criteria summary" in description_summary.build_summary_section(tl, language="en")


def test_summary_empty_when_only_low_or_no_ac():
    tl = {
        "tasks": [
            {"name": "1.1 Low", "priority": "Low", "acceptance_criteria": ["x"]},
            {"name": "1.2 High no AC", "priority": "High", "acceptance_criteria": []},
        ]
    }
    assert description_summary.build_summary_section(tl) == ""


def test_append_preserves_original_description():
    tl = _tasklist_with_priorities()
    rendered = description_summary.append_summary_to_description(tl, language="sk")
    assert rendered.startswith("ROZŠÍRENIE Č. 1 — Demo (DNR sekcia 4.1)")
    assert "** Sumár akceptačných kritérií" in rendered


def test_md_renderer_embeds_summary_in_quoted_dnr_block(expected_plan):
    md = json_to_md.render(expected_plan)
    # Each tasklist quote block should contain the summary heading at least once.
    assert "Sumár akceptačných kritérií" in md
    # The summary is rendered inside the `> ` blockquote of "Pôvodné znenie DNR".
    assert "> ** Sumár akceptačných kritérií" in md


def test_xlsx_description_cell_includes_summary(expected_plan, tmp_path):
    out = tmp_path / "out.xlsx"
    json_to_xlsx.write(expected_plan, out)
    # Quick smoke check: re-open as ZIP and verify the shared strings include the summary heading.
    import zipfile
    with zipfile.ZipFile(out) as z:
        shared_strings = z.read("xl/sharedStrings.xml").decode("utf-8")
    assert "Sumár akceptačných kritérií" in shared_strings
