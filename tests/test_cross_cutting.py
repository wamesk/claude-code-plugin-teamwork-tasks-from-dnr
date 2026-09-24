"""Tests for the cross-cutting requirements (cross_cutting.py) and their wiring
into the renderers and the validator."""
import copy
import re

import cross_cutting as cc
import json_to_md
import json_to_xlsx
import validate_json


def _plan(task_overrides=None, language="sk"):
    task = {
        "name": "4.1.3 [FE] Obrazovka splátok",
        "priority": "High",
        "estimated_minutes": 120,
        "goal": "g",
        "acceptance_criteria": ["Používateľ vidí zoznam splátok."],
        "dependencies": ["4.1.1 Príprava dát"],
        "technical_plan": "t",
    }
    task.update(task_overrides or {})
    return {
        "metadata": {"title": "x", "language": language, "total_md_estimate": 0.25},
        "tasklists": [{"name": "4.1 TL", "description": "desc", "tasks": [task]}],
    }


REACH = {"dimension": "reachability",
         "criterion": "Sekcia Splátky je dostupná z menu Fakturácia a z detailu zmluvy."}
SEC = {"dimension": "security",
       "criterion": "Sekciu vidí len rola Účtovník; cudzí záznam vráti 403."}
UIUX = {"dimension": "ui_ux", "criterion": "Prázdny a chybový stav sú navrhnuté."}


# --- render_block ------------------------------------------------------------

def test_render_block_empty_is_noop():
    assert cc.render_block(None) == ""
    assert cc.render_block([]) == ""
    assert cc.render_block([{"dimension": "security", "criterion": "   "}]) == ""


def test_render_block_sk_labels_and_keys():
    block = cc.render_block([SEC, REACH], "sk")
    lines = block.split("\n")
    assert lines[0] == "### Prierezové požiadavky"
    # Reachability renders first regardless of input order.
    assert lines[1] == f"- [ ] **Dostupnosť (reachability):** {REACH['criterion']}"
    assert lines[2] == f"- [ ] **Bezpečnosť (security):** {SEC['criterion']}"


def test_render_block_cs_and_en_headings():
    assert cc.render_block([UIUX], "cs").startswith("### Průřezové požadavky\n")
    assert "**Výkon (performance):**" in cc.render_block(
        [{"dimension": "performance", "criterion": "x"}], "cs")
    en = cc.render_block([REACH, UIUX], "en")
    assert en.startswith("### Cross-cutting requirements\n")
    assert "**Reachability (reachability):**" in en
    assert "**UI/UX (ui_ux):**" in en


# --- renderer placement --------------------------------------------------------

def _ac_section(desc: str) -> str:
    """The block teamwork-task-test reads and ticks: heading → first `---`."""
    m = re.search(r"(##\s*Akceptačné kritériá\s*\n)(.*?)(\n---)", desc, re.S)
    assert m, "acceptance-criteria block not found"
    return m.group(2)


def test_xlsx_description_places_block_inside_acceptance_section():
    plan = _plan({"ui_surface": "new_screen", "cross_cutting": [REACH, SEC]})
    task = plan["tasklists"][0]["tasks"][0]
    desc = json_to_xlsx._render_task_description(task, language="sk")
    ac = _ac_section(desc)
    assert "### Prierezové požiadavky" in ac
    assert f"- [ ] **Dostupnosť (reachability):** {REACH['criterion']}" in ac
    # Before Závislosť, after the ordinary criteria.
    assert ac.index("Používateľ vidí zoznam splátok.") < ac.index("### Prierezové požiadavky")
    assert ac.index("### Prierezové požiadavky") < ac.index("### Závislosť")
    # The block itself never introduces a separator.
    assert "---" not in cc.render_block([REACH, SEC], "sk")


def test_xlsx_description_unchanged_without_field():
    plan = _plan()
    task = plan["tasklists"][0]["tasks"][0]
    before = json_to_xlsx._render_task_description(task, language="sk")
    task_empty = dict(task, cross_cutting=[])
    assert json_to_xlsx._render_task_description(task_empty, language="sk") == before
    assert "Prierezové" not in before


def test_md_and_xlsx_render_the_same_block():
    plan = _plan({"ui_surface": "new_screen", "cross_cutting": [REACH, UIUX]}, language="en")
    md = json_to_md.render(plan)
    block = cc.render_block([REACH, UIUX], "en")
    assert block in md
    task = plan["tasklists"][0]["tasks"][0]
    assert block in json_to_xlsx._render_task_description(task, language="en")
    # MD conventions mention the sub-block only when a plan uses it.
    assert "**Prierezové požiadavky**" in md


def test_gold_plan_renders_without_cross_cutting(expected_plan):
    md = json_to_md.render(expected_plan)
    assert "Prierezové" not in md
    assert not cc.has_cross_cutting(expected_plan)


# --- validation ------------------------------------------------------------------

def test_new_screen_without_reachability_fails(schema):
    plan = _plan({"ui_surface": "new_screen", "cross_cutting": [SEC]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("reachability" in e and "new_screen" in e for e in errors)


def test_new_screen_without_any_items_fails(schema):
    ok, errors = validate_json.validate_plan(_plan({"ui_surface": "new_screen"}), schema)
    assert not ok
    assert any("reachability" in e for e in errors)


def test_new_screen_with_reachability_passes(schema):
    plan = _plan({"ui_surface": "new_screen", "cross_cutting": [REACH, SEC]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_url_only_page_passes_with_its_reachability_statement(schema):
    url_only = {"dimension": "reachability",
                "criterion": "Stránka je zámerne dostupná len cez odkaz z e-mailu, bez položky v menu."}
    plan = _plan({"ui_surface": "new_screen", "cross_cutting": [url_only]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_existing_screen_does_not_require_reachability(schema):
    plan = _plan({"ui_surface": "existing_screen", "cross_cutting": [UIUX]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_unknown_dimension_rejected_by_schema(schema):
    plan = _plan({"cross_cutting": [{"dimension": "usability", "criterion": "x"}]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("usability" in e for e in errors)


def test_unknown_ui_surface_rejected_by_schema(schema):
    ok, errors = validate_json.validate_plan(_plan({"ui_surface": "screen"}), schema)
    assert not ok


def test_empty_criterion_rejected_by_schema(schema):
    plan = _plan({"cross_cutting": [{"dimension": "security", "criterion": ""}]})
    ok, _ = validate_json.validate_plan(plan, schema)
    assert not ok


def test_gold_plan_still_valid(expected_plan, schema):
    ok, errors = validate_json.validate_plan(copy.deepcopy(expected_plan), schema)
    assert ok, errors


def test_framework_is_never_an_acceptance_criterion(schema):
    # `framework` lives in the technical plan only: teamwork-task-test treats it
    # as an advisory recommendation, so a checkbox for it could never be ticked.
    assert "framework" not in cc.DIMENSIONS
    plan = _plan({"cross_cutting": [{"dimension": "framework",
                                     "criterion": "Použiť casts() metódu."}]})
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("framework" in e for e in errors)
