"""Tests for the shared contract rendering (contract_render.py)."""
import contract_render as cr


def test_contract_block_sk():
    block = cr.render_contract_ref_block(
        {"feature_slug": "objednavky-editel-sync", "version": "0.1.0"},
        "some-backend", "sk")
    assert block.startswith("### Kontrakt")
    assert "- Súbor: docs/contracts/objednavky-editel-sync/openapi.yaml" in block
    assert "- Verzia: 0.1.0" in block
    assert "- Repo: some-backend" in block
    assert "- Commit: [DOPLNIŤ po zmergovaní]" in block


def test_contract_block_en_labels():
    block = cr.render_contract_ref_block(
        {"feature_slug": "orders", "version": "0.2.0"}, "be-repo", "en")
    assert "### Contract" in block
    assert "- File: docs/contracts/orders/openapi.yaml" in block
    assert "- Version: 0.2.0" in block
    assert "[DOPLNIŤ after merge]" in block


def test_custom_contract_dir():
    block = cr.render_contract_ref_block(
        {"feature_slug": "x"}, "r", "sk", contract_dir="api/contracts")
    assert "api/contracts/x/openapi.yaml" in block


def test_missing_repo_becomes_placeholder():
    block = cr.render_contract_ref_block({"feature_slug": "x"}, None, "sk")
    assert "- Repo: [DOPLNIŤ]" in block


def test_append_contract_ref_noop_without_ref():
    # No contract_ref -> output identical to the plain rstripped technical plan.
    text = "Some technical plan.\n\n"
    assert cr.append_contract_ref(text, None) == "Some technical plan."


def test_append_contract_ref_adds_block():
    result = cr.append_contract_ref(
        "Technical steps.", {"feature_slug": "orders", "version": "0.1.0"},
        repo_name="be", language="sk")
    assert result.startswith("Technical steps.\n\n### Kontrakt")


def test_append_contract_ref_empty_plan():
    result = cr.append_contract_ref("", {"feature_slug": "orders"}, "be", "sk")
    assert result.startswith("### Kontrakt")


def test_missing_artifacts_lists_tasks():
    plan = {
        "tasklists": [
            {"name": "4.1", "tasks": [
                {"name": "4.1.1 FE napojenie", "contract_ref": {"feature_slug": "orders"}},
                {"name": "4.1.2 nič", "technical_plan": "x"},
            ]},
        ]
    }
    section = cr.render_missing_artifacts(plan, "sk")
    assert "## Chýbajúce artefakty" in section
    assert "### orders" in section
    assert "docs/contracts/orders/openapi.yaml" in section
    assert "4.1.1 FE napojenie" in section
    assert "4.1.2 nič" not in section  # task without contract_ref not listed


def test_missing_artifacts_empty_when_no_refs():
    plan = {"tasklists": [{"name": "x", "tasks": [{"name": "t"}]}]}
    assert cr.render_missing_artifacts(plan, "sk") == ""
