"""Tests for the OpenAPI / data-model emitter (contract_emit.py).

The emitter's job is to guarantee a *valid* OpenAPI 3.1 skeleton even with
`[DOPLNIŤ]` placeholders. We assert that structurally without a YAML parser
(the runtime is stdlib-only, no pyyaml), and additionally round-trip through
pyyaml when it happens to be installed in the test environment.
"""
import pytest

import contract_emit as ce

try:
    import yaml as _yaml
except ImportError:  # pyyaml is an optional dev extra, not a runtime dep
    _yaml = None


CONTRACT = {
    "feature_slug": "objednavky-editel-sync",
    "title": "Objednávky — Editel sync",
    "version": "0.1.0",
    "openapi": {
        "servers": [{"url": "/api/v1", "description": "Primárny server"}],
        "endpoints": [
            {
                "method": "post",
                "path": "/orders/{id}/sync",
                "operation_id": "syncOrder",
                "summary": "Synchronizácia objednávky",
                "description": "[DOPLNIŤ] presné pravidlá mapovania.",
                "tags": ["Orders"],
                "status": "draft",
                "request_schema": "SyncOrderRequest",
                "success_data_schema": "OrderSyncResult",
                "error_statuses": [401, 422],
            },
            {
                "method": "get",
                "path": "/orders",
                "operation_id": "listOrders",
                "summary": "Zoznam objednávok",
                "status": "stable",
            },
        ],
        "schemas": [
            {"name": "SyncOrderRequest", "fields": [
                {"name": "force", "type": "boolean", "nullable": False}]},
            {"name": "OrderSyncResult", "fields": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "editel_ref", "type": "string", "nullable": True}]},
        ],
    },
}


# --- to_yaml unit behaviour ------------------------------------------------

def test_bracket_string_is_quoted():
    # The crux: [DOPLNIŤ] must never be emitted as a bare (flow-sequence) value.
    out = ce.to_yaml({"description": "[DOPLNIŤ]"})
    assert out.strip() == 'description: "[DOPLNIŤ]"'


def test_null_string_is_quoted():
    assert ce.to_yaml({"type": ["string", "null"]}).strip() == 'type: [string, "null"]'


def test_numeric_string_is_quoted():
    assert ce.to_yaml({"version": "0.1.0"}).strip() == 'version: "0.1.0"'
    assert ce.to_yaml({"v": "1.0"}).strip() == 'v: "1.0"'


def test_plain_scalar_stays_unquoted():
    assert ce.to_yaml({"type": "object"}).strip() == "type: object"


def test_colon_and_hash_force_quoting():
    assert ce.to_yaml({"s": "A: B #c"}).strip() == 's: "A: B #c"'


def test_newline_and_tab_are_escaped():
    assert ce.to_yaml({"s": "a\nb\tc"}).strip() == 's: "a\\nb\\tc"'


# --- openapi structure -----------------------------------------------------

def test_openapi_header_and_version():
    text = ce.emit_openapi_yaml(CONTRACT, "http_status", "sk")
    assert text.startswith("# API contract skeleton")
    assert 'openapi: "3.1.0"' in text
    assert 'version: "0.1.0"' in text


def test_doplnit_never_unquoted_anywhere():
    text = ce.emit_openapi_yaml(CONTRACT, "http_status", "sk")
    # No `: [DOPLNIŤ` — it must always be inside a double-quoted scalar.
    assert ": [DOPLNIŤ" not in text
    assert '"[DOPLNIŤ]' in text or '[DOPLNIŤ]"' in text


def test_security_scheme_is_sanctum_bearer():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    scheme = doc["components"]["securitySchemes"]["sanctum"]
    assert scheme["type"] == "http" and scheme["scheme"] == "bearer"
    assert doc["security"] == [{"sanctum": []}]


def test_x_wame_status_present():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    assert doc["paths"]["/orders/{id}/sync"]["post"]["x-wame-status"] == "draft"
    assert doc["paths"]["/orders"]["get"]["x-wame-status"] == "stable"


def test_path_parameters_are_generated():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    params = doc["paths"]["/orders/{id}/sync"]["post"]["parameters"]
    assert params == [{"name": "id", "in": "path", "required": True,
                       "schema": {"type": "integer"}}]
    # Non-templated path has no parameters key.
    assert "parameters" not in doc["paths"]["/orders"]["get"]


def test_path_parameter_type_inference():
    contract = {"title": "t", "version": "0.1.0", "openapi": {"endpoints": [
        {"method": "get", "path": "/a/{slug}/b/{customerId}", "operation_id": "x"}]}}
    doc = ce.build_openapi(contract, "http_status", "sk")
    params = {p["name"]: p["schema"]["type"]
              for p in doc["paths"]["/a/{slug}/b/{customerId}"]["get"]["parameters"]}
    assert params == {"slug": "string", "customerId": "integer"}


def test_nullable_field_becomes_null_union():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    prop = doc["components"]["schemas"]["OrderSyncResult"]["properties"]["editel_ref"]
    assert prop["type"] == ["string", "null"]


def test_success_uses_envelope_allof():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    schema = doc["paths"]["/orders/{id}/sync"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    refs = [m.get("$ref") for m in schema["allOf"] if "$ref" in m]
    assert any("WameSuccess" in r for r in refs)


def test_http_status_convention_declares_error_codes():
    doc = ce.build_openapi(CONTRACT, "http_status", "sk")
    responses = doc["paths"]["/orders/{id}/sync"]["post"]["responses"]
    assert "401" in responses and "422" in responses
    assert "WameError" in responses["401"]["content"]["application/json"]["schema"]["$ref"]


def test_ok_convention_uses_oneof_on_200():
    doc = ce.build_openapi(CONTRACT, "ok", "sk")
    schema = doc["paths"]["/orders/{id}/sync"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert "oneOf" in schema
    # No separate 4xx response in the "ok" convention.
    assert set(doc["paths"]["/orders/{id}/sync"]["post"]["responses"]) == {"200"}


# --- data-model ------------------------------------------------------------

def test_data_model_md_table_and_labels():
    dm = {"entities": [{
        "name": "Order", "description": "Objednávka",
        "fields": [{"name": "id", "type": "bigint", "nullable": False, "description": "PK"}],
        "relations": [{"kind": "belongsTo", "target": "Customer"}],
        "indexes": [{"columns": ["id"], "unique": True}],
        "notes": ["Poznámka"],
    }]}
    md = ce.emit_data_model_md(dm, "Feature", "sk")
    assert "## Order" in md
    assert "| Pole | Typ | Nullable | Default | Popis |" in md
    assert "belongsTo `Customer`" in md
    assert "**Poznámky:**" in md


def test_data_model_pipe_escaped():
    dm = {"entities": [{"name": "E", "fields": [
        {"name": "f", "type": "string", "description": "a | b"}]}]}
    md = ce.emit_data_model_md(dm, "F", "sk")
    assert "a \\| b" in md


def test_data_model_empty():
    md = ce.emit_data_model_md({"entities": []}, "F", "en")
    assert "No entities" in md


# --- full parse round-trip (only when pyyaml is available) -----------------

@pytest.mark.skipif(_yaml is None, reason="pyyaml not installed (optional dev extra)")
@pytest.mark.parametrize("convention", ["http_status", "ok"])
def test_openapi_parses_as_valid_yaml(convention):
    text = ce.emit_openapi_yaml(CONTRACT, convention, "sk")
    doc = _yaml.safe_load(text)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["version"] == "0.1.0"
    desc = doc["paths"]["/orders/{id}/sync"]["post"]["description"]
    assert isinstance(desc, str) and desc.startswith("[DOPLNIŤ]")
    assert doc["components"]["schemas"]["OrderSyncResult"]["properties"]["editel_ref"]["type"] == ["string", "null"]
