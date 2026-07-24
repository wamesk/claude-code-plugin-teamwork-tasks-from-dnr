"""Tests for idempotent contract writing (contract_writer.py)."""
import contract_writer as cw


def _plan():
    return {
        "metadata": {"language": "sk", "title": "Editel"},
        "contracts": [{
            "feature_slug": "objednavky-editel-sync",
            "title": "Objednávky",
            "version": "0.1.0",
            "openapi": {"endpoints": [
                {"method": "post", "path": "/orders/sync", "operation_id": "syncOrders",
                 "status": "draft"}]},
            "data_model": {"entities": [{"name": "Order"}]},
        }],
        "tasklists": [],
    }


def _paths(base):
    slug = "objednavky-editel-sync"
    return (
        base / "_shared" / "wame-envelope.yaml",
        base / slug / "openapi.yaml",
        base / slug / "data-model.md",
    )


def test_plan_writes_touches_nothing(tmp_path):
    base = tmp_path / "docs" / "contracts"
    result = cw.plan_writes(base, _plan())
    assert all(a["action"] == "create" for a in result["actions"])
    assert result["needs_confirmation"] is False
    assert not base.exists()  # preview must not create anything


def test_apply_creates_all_files(tmp_path):
    base = tmp_path / "docs" / "contracts"
    result = cw.apply_writes(base, _plan())
    env, openapi, datamodel = _paths(base)
    assert env.exists() and openapi.exists() and datamodel.exists()
    assert all(r["action"] == "created" for r in result["results"])
    assert "WameSuccess" in env.read_text(encoding="utf-8")


def test_second_apply_is_unchanged(tmp_path):
    base = tmp_path / "docs" / "contracts"
    cw.apply_writes(base, _plan())
    result = cw.apply_writes(base, _plan())
    assert all(r["action"] == "unchanged" for r in result["results"])


def test_edited_openapi_gets_proposed_not_overwritten(tmp_path):
    base = tmp_path / "docs" / "contracts"
    cw.apply_writes(base, _plan())
    _, openapi, _ = _paths(base)
    edited = openapi.read_text(encoding="utf-8") + "\n# manual edit\n"
    openapi.write_text(edited, encoding="utf-8")

    result = cw.apply_writes(base, _plan())
    actions = {r["role"]: r["action"] for r in result["results"]}
    assert actions["openapi"] == "proposed"
    # Original preserved; a sibling .proposed exists.
    assert "# manual edit" in openapi.read_text(encoding="utf-8")
    assert (openapi.parent / "openapi.yaml.proposed").exists()


def test_plan_shows_diff_for_existing(tmp_path):
    base = tmp_path / "docs" / "contracts"
    cw.apply_writes(base, _plan())
    _, openapi, _ = _paths(base)
    openapi.write_text("openapi: nonsense\n", encoding="utf-8")

    result = cw.plan_writes(base, _plan())
    exists = [a for a in result["actions"] if a["action"] == "exists"]
    assert exists and result["needs_confirmation"] is True
    assert "diff" in exists[0] and exists[0]["diff"]


def test_envelope_never_proposed_only_created_once(tmp_path):
    base = tmp_path / "docs" / "contracts"
    cw.apply_writes(base, _plan())
    env, _, _ = _paths(base)
    env.write_text("hand edited envelope\n", encoding="utf-8")

    result = cw.apply_writes(base, _plan())
    env_result = next(r for r in result["results"] if r["role"] == "envelope")
    assert env_result["action"] == "skipped"  # only_if_absent → left alone
    assert env.read_text(encoding="utf-8") == "hand edited envelope\n"
    assert not (env.parent / "wame-envelope.yaml.proposed").exists()


def test_force_overwrites(tmp_path):
    base = tmp_path / "docs" / "contracts"
    cw.apply_writes(base, _plan())
    _, openapi, _ = _paths(base)
    openapi.write_text("stale\n", encoding="utf-8")

    result = cw.apply_writes(base, _plan(), force=True)
    action = next(r["action"] for r in result["results"] if r["role"] == "openapi")
    assert action == "overwritten"
    assert "openapi" in openapi.read_text(encoding="utf-8")


def test_no_contracts_yields_no_targets(tmp_path):
    base = tmp_path / "docs" / "contracts"
    plan = {"metadata": {"language": "sk"}, "contracts": [], "tasklists": []}
    assert cw.plan_writes(base, plan)["actions"] == []
