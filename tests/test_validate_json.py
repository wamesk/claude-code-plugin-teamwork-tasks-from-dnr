"""Tests for the JSON schema validator + cross-field plan checks."""
import copy

import validate_json


def test_expected_plan_is_valid(expected_plan, schema):
    ok, errors = validate_json.validate_plan(expected_plan, schema)
    assert ok, f"Gold-standard plan should validate; errors: {errors}"


def test_missing_required_field(expected_plan, schema):
    plan = copy.deepcopy(expected_plan)
    del plan["metadata"]["title"]
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("title" in e for e in errors)


def test_invalid_priority_enum(expected_plan, schema):
    plan = copy.deepcopy(expected_plan)
    plan["tasklists"][0]["tasks"][0]["priority"] = "Critical"
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("enum" in e for e in errors)


def test_estimated_minutes_below_min(expected_plan, schema):
    plan = copy.deepcopy(expected_plan)
    plan["tasklists"][0]["tasks"][0]["estimated_minutes"] = 5
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("minimum" in e.lower() for e in errors)


def test_minutes_not_divisible_by_15(expected_plan, schema):
    plan = copy.deepcopy(expected_plan)
    # 100 is in range but not divisible by 15.
    plan["tasklists"][0]["tasks"][0]["estimated_minutes"] = 100
    # We need to also adjust md_estimate or another task minutes to satisfy
    # cross-field check; here we just check that the per-task issue is raised.
    plan["tasklists"][0]["md_estimate"] = None  # disable md cross-check
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("divisible by 15" in e for e in errors)


def test_md_estimate_mismatch(expected_plan, schema):
    plan = copy.deepcopy(expected_plan)
    plan["tasklists"][0]["md_estimate"] = 5.0  # actual sum is 2.5
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("md_estimate" in e for e in errors)


def test_empty_tasklists_fails(schema):
    plan = {"metadata": {"title": "x", "language": "sk", "total_md_estimate": 1.0}, "tasklists": []}
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("minItems" in e or "items" in e.lower() for e in errors)
