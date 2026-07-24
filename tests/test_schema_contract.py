"""Tests for contract-first schema fields + cross-validation (validate_json.py)."""
import validate_json


def _task(name, kind=None, ref=None, role=None):
    task = {
        "name": name, "priority": "High", "estimated_minutes": 60,
        "goal": "g", "acceptance_criteria": ["a"], "technical_plan": "t",
    }
    if kind:
        task["task_kind"] = kind
    if ref:
        task["contract_ref"] = ref
    if role:
        task["role"] = role
    return task


def _contract(slug="objednavky-editel-sync", op_id="syncX", method="post"):
    return {
        "feature_slug": slug, "title": "O", "version": "0.1.0",
        "openapi": {"endpoints": [
            {"method": method, "path": "/x", "operation_id": op_id}]},
        "data_model": {"entities": [{"name": "Order"}]},
    }


def _plan(contracts, tasks):
    return {
        "metadata": {"title": "X", "language": "sk", "total_md_estimate": 1.0},
        "contracts": contracts,
        "tasklists": [{"name": "4.1 TL", "description": "d", "md_estimate": 0.125,
                       "tasks": tasks}],
    }


def test_regression_existing_fixture_still_valid(schema, expected_plan):
    ok, errors = validate_json.validate_plan(expected_plan, schema)
    assert ok, errors


def test_valid_backend_plan(schema):
    ref = {"feature_slug": "objednavky-editel-sync", "version": "0.1.0"}
    plan = _plan([_contract()], [
        _task("4.1.0 Definovať API kontrakt", "contract", ref, "BE"),
        _task("4.1.1 Impl", ref=ref, role="BE"),
    ])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_non_kebab_slug_rejected(schema):
    ref = {"feature_slug": "Not_Kebab"}
    plan = _plan([_contract(slug="Not_Kebab")],
                 [_task("t", "contract", ref)])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert not ok
    assert any("kebab-case" in e for e in errors)


def test_unknown_contract_ref_rejected(schema):
    ref = {"feature_slug": "objednavky-editel-sync"}
    plan = _plan([_contract()], [
        _task("4.1.0 Def", "contract", ref),
        _task("4.1.1 Impl", ref={"feature_slug": "ghost"}),
    ])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert any("unknown contract" in e for e in errors)


def test_missing_contract_task_rejected(schema):
    ref = {"feature_slug": "objednavky-editel-sync"}
    plan = _plan([_contract()], [_task("4.1.1 Impl", ref=ref)])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert any("no 'Definovať API kontrakt'" in e for e in errors)


def test_non_ascii_operation_id_rejected(schema):
    ref = {"feature_slug": "objednavky-editel-sync"}
    plan = _plan([_contract(op_id="synchronizáciaX")],
                 [_task("t", "contract", ref)])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert any("ASCII" in e for e in errors)


def test_bad_http_method_rejected(schema):
    ref = {"feature_slug": "objednavky-editel-sync"}
    plan = _plan([_contract(method="fetch")], [_task("t", "contract", ref)])
    ok, errors = validate_json.validate_plan(plan, schema)
    assert any("HTTP method" in e for e in errors)


def test_frontend_ref_without_contracts_is_valid(schema):
    # Frontend/standalone: contract_ref present, no contracts[] -> no referential errors.
    ref = {"feature_slug": "orders"}
    plan = {
        "metadata": {"title": "X", "language": "sk", "total_md_estimate": 1.0,
                     "repo_mode": "frontend"},
        "tasklists": [{"name": "4.1", "description": "d",
                       "tasks": [_task("4.1.1 FE", ref=ref, role="FE")]}],
    }
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors


def test_metadata_contract_fields_accepted(schema):
    plan = {
        "metadata": {"title": "X", "language": "sk", "total_md_estimate": 1.0,
                     "repo_mode": "backend", "repo_name": "be-repo",
                     "error_http_convention": "http_status",
                     "contract_desc_language": "sk", "contract_dir": "docs/contracts"},
        "tasklists": [{"name": "4.1", "description": "d", "tasks": [_task("t")]}],
    }
    ok, errors = validate_json.validate_plan(plan, schema)
    assert ok, errors
