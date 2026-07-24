#!/usr/bin/env python3
"""
contract_emit — deterministically render an OpenAPI 3.1 skeleton and a
data-model Markdown from a structured `contract` object.

Design rationale
----------------
The plugin keeps the same split it already uses for tasks: Claude (the LLM)
produces a *structured* `contract` JSON, and Python renders the final
artifacts. Rendering YAML deterministically — instead of letting the LLM emit
raw YAML — is what lets us guarantee the acceptance criterion that the
generated `openapi.yaml` is valid OpenAPI 3.1 *even with `[DOPLNIŤ]`
placeholders*: placeholders only ever land inside scalar string values
(`summary` / `description`), and the emitter always quotes any string that is
not plainly safe, so `[DOPLNIŤ]` (which contains `[`/`]`) can never be
misread as a YAML flow sequence.

Stdlib only — no `pyyaml`, no `openpyxl`.
"""
from __future__ import annotations

import re

# Relative $ref from `docs/contracts/<slug>/openapi.yaml` to the shared
# envelope at `docs/contracts/_shared/wame-envelope.yaml`.
ENVELOPE_REF = "../_shared/wame-envelope.yaml"
WAME_SUCCESS = f"{ENVELOPE_REF}#/components/schemas/WameSuccess"
WAME_ERROR = f"{ENVELOPE_REF}#/components/schemas/WameError"

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
DEFAULT_ERROR_STATUSES = [401, 422]

# Response `description` defaults (OpenAPI requires a non-empty description on
# every response). Overridable per endpoint; localised to the DNR language.
_RESPONSE_DESC = {
    "sk": {
        "success": "Úspešná odpoveď (WAME success obálka).",
        "error": "Chybová odpoveď (WAME error obálka).",
    },
    "cs": {
        "success": "Úspěšná odpověď (WAME success obálka).",
        "error": "Chybová odpověď (WAME error obálka).",
    },
    "en": {
        "success": "Successful response (WAME success envelope).",
        "error": "Error response (WAME error envelope).",
    },
}


# ===========================================================================
# Minimal block-style YAML emitter (JSON-compatible types only)
# ===========================================================================

# A string may be written as a *plain* (unquoted) scalar only when it is
# unambiguous. Keys must start with a letter/underscore; values may also start
# with `/` (paths, server URLs). Anything else is double-quoted — including
# every non-ASCII string (Slovak text), every numeric-looking string, and
# every string containing YAML-significant punctuation such as `[`, `]`, `:`,
# `#`, `{`, `}`, `$` — which is exactly what keeps `[DOPLNIŤ]` safe.
_PLAIN_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9._/\-]*$")
_PLAIN_VALUE_RE = re.compile(r"^[A-Za-z/][A-Za-z0-9 ._/\-]*$")

# Words a YAML parser would coerce to a bool/null — must be quoted when meant
# as strings (e.g. OpenAPI 3.1 nullable: `type: [string, "null"]`).
_RESERVED = {
    "true", "false", "null", "yes", "no", "on", "off", "none", "y", "n", "~", "",
}

# XML/JSON control characters we never want raw in output.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _double_quote(s: str) -> str:
    """Return a YAML double-quoted scalar, escaping specials and newlines."""
    s = _CONTROL_RE.sub("", s)
    out = (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{out}"'


def _fmt_key(key) -> str:
    key = str(key)
    if _PLAIN_KEY_RE.match(key) and key.lower() not in _RESERVED:
        return key
    return _double_quote(key)


def _fmt_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    text = str(value)
    if (
        text
        and text[-1] != " "
        and _PLAIN_VALUE_RE.match(text)
        and text.lower() not in _RESERVED
    ):
        return text
    return _double_quote(text)


def _is_scalar(value) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _dump(obj, indent: int) -> list[str]:
    """Render `obj` as block-style YAML lines (no trailing newline)."""
    pad = "  " * indent
    lines: list[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            fkey = _fmt_key(key)
            if isinstance(value, dict):
                if value:
                    lines.append(f"{pad}{fkey}:")
                    lines.extend(_dump(value, indent + 1))
                else:
                    lines.append(f"{pad}{fkey}: {{}}")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{pad}{fkey}: []")
                elif all(_is_scalar(v) for v in value):
                    inline = ", ".join(_fmt_scalar(v) for v in value)
                    lines.append(f"{pad}{fkey}: [{inline}]")
                else:
                    lines.append(f"{pad}{fkey}:")
                    lines.extend(_dump(value, indent + 1))
            else:
                lines.append(f"{pad}{fkey}: {_fmt_scalar(value)}")

    elif isinstance(obj, list):
        child_pad = "  " * (indent + 1)
        for item in obj:
            if isinstance(item, dict) and item:
                item_lines = _dump(item, indent + 1)
                first = item_lines[0][len(child_pad):]
                lines.append(f"{pad}- {first}")
                lines.extend(item_lines[1:])
            elif isinstance(item, list) and item:
                lines.append(f"{pad}-")
                lines.extend(_dump(item, indent + 1))
            elif isinstance(item, dict):
                lines.append(f"{pad}- {{}}")
            elif isinstance(item, list):
                lines.append(f"{pad}- []")
            else:
                lines.append(f"{pad}- {_fmt_scalar(item)}")

    else:  # top-level scalar (not used for OpenAPI docs, but keep it total)
        lines.append(f"{pad}{_fmt_scalar(obj)}")

    return lines


def to_yaml(obj) -> str:
    """Serialize a JSON-compatible object to block-style YAML text."""
    return "\n".join(_dump(obj, 0)) + "\n"


# ===========================================================================
# OpenAPI 3.1 document builder
# ===========================================================================


def _field_type(field: dict):
    """OpenAPI 3.1 type; nullable becomes a `[type, "null"]` union."""
    ftype = field.get("type") or "string"
    if field.get("nullable"):
        return [ftype, "null"]
    return ftype


def _property_schema(field: dict) -> dict:
    schema: dict = {"type": _field_type(field)}
    if field.get("format"):
        schema["format"] = field["format"]
    if field.get("description"):
        schema["description"] = field["description"]
    return schema


def _component_schema(schema: dict) -> dict:
    fields = schema.get("fields") or []
    obj: dict = {"type": "object"}
    if schema.get("description"):
        obj["description"] = schema["description"]
    required = [
        f["name"]
        for f in fields
        if f.get("required", not f.get("nullable", False))
    ]
    if required:
        obj["required"] = required
    obj["properties"] = {f["name"]: _property_schema(f) for f in fields}
    return obj


def _success_schema(endpoint: dict) -> dict:
    """Success body: WameSuccess envelope with the data slot concretised."""
    data_schema = endpoint.get("success_data_schema")
    if data_schema:
        return {
            "allOf": [
                {"$ref": WAME_SUCCESS},
                {"type": "object", "properties": {
                    "data": {"$ref": f"#/components/schemas/{data_schema}"}}},
            ]
        }
    return {"$ref": WAME_SUCCESS}


def _content(schema: dict) -> dict:
    return {"application/json": {"schema": schema}}


def _build_responses(endpoint: dict, error_convention: str, lang: str) -> dict:
    desc = _RESPONSE_DESC.get(lang, _RESPONSE_DESC["en"])
    success_desc = endpoint.get("success_description") or desc["success"]
    error_desc = endpoint.get("error_description") or desc["error"]

    responses: dict = {}
    if error_convention == "ok":
        # WAME variant where errors are returned with HTTP 200 and signalled by
        # the envelope `type: error`. A single 200 may be success OR error.
        responses["200"] = {
            "description": success_desc,
            "content": _content({"oneOf": [
                _success_schema(endpoint),
                {"$ref": WAME_ERROR},
            ]}),
        }
    else:  # "http_status"
        responses["200"] = {
            "description": success_desc,
            "content": _content(_success_schema(endpoint)),
        }
        statuses = endpoint.get("error_statuses") or DEFAULT_ERROR_STATUSES
        for status in statuses:
            responses[str(status)] = {
                "description": error_desc,
                "content": _content({"$ref": WAME_ERROR}),
            }
    return responses


_PATH_PARAM_RE = re.compile(r"\{([^}]+)\}")


def _path_parameters(endpoint: dict) -> list[dict]:
    """Derive OpenAPI path parameters from `{name}` templates in the path.

    A templated path (`/orders/{id}`) is only well-formed OpenAPI when the
    parameter is declared, so we emit one entry per `{name}`. Types are
    inferred (`id` / `*_id` / `*Id` → integer, else string); the endpoint may
    override via a `parameters` list keyed by name.
    """
    path = endpoint.get("path") or ""
    overrides = {p.get("name"): p for p in (endpoint.get("parameters") or [])}
    params: list[dict] = []
    for name in _PATH_PARAM_RE.findall(path):
        spec = overrides.get(name, {})
        ptype = spec.get("type")
        if not ptype:
            ptype = "integer" if (name == "id" or name.endswith("_id")
                                  or name.endswith("Id")) else "string"
        param = {"name": name, "in": "path", "required": True,
                 "schema": {"type": ptype}}
        if spec.get("description"):
            param["description"] = spec["description"]
        params.append(param)
    return params


def _build_operation(endpoint: dict, error_convention: str, lang: str) -> dict:
    op: dict = {"operationId": endpoint.get("operation_id") or "operationId"}
    if endpoint.get("tags"):
        op["tags"] = list(endpoint["tags"])
    if endpoint.get("summary"):
        op["summary"] = endpoint["summary"]

    status = endpoint.get("status") or "draft"
    description = endpoint.get("description")
    if not description and status == "draft":
        description = "[DOPLNIŤ]"
    if description:
        op["description"] = description
    op["x-wame-status"] = status

    parameters = _path_parameters(endpoint)
    if parameters:
        op["parameters"] = parameters

    if endpoint.get("request_schema"):
        op["requestBody"] = {
            "required": True,
            "content": _content(
                {"$ref": f"#/components/schemas/{endpoint['request_schema']}"}),
        }

    op["responses"] = _build_responses(endpoint, error_convention, lang)
    return op


def build_openapi(contract: dict, error_convention: str = "http_status",
                  language: str = "sk") -> dict:
    """Assemble an OpenAPI 3.1 document dict from a structured contract."""
    spec = contract.get("openapi") or {}
    servers = spec.get("servers") or [{"url": "/api/v1"}]
    lang = language if language in _RESPONSE_DESC else "en"

    paths: dict = {}
    for endpoint in spec.get("endpoints") or []:
        method = (endpoint.get("method") or "get").lower()
        if method not in HTTP_METHODS:
            method = "get"
        path = endpoint.get("path") or "/[DOPLNIŤ]"
        paths.setdefault(path, {})[method] = _build_operation(
            endpoint, error_convention, lang)

    schemas = {
        s["name"]: _component_schema(s)
        for s in (spec.get("schemas") or [])
        if s.get("name")
    }

    document: dict = {
        "openapi": "3.1.0",
        "info": {
            "title": contract.get("title") or "API contract",
            "version": str(contract.get("version") or "0.1.0"),
        },
        "servers": servers,
        "security": [{"sanctum": []}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "sanctum": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Laravel Sanctum bearer token.",
                }
            },
        },
    }
    if schemas:
        document["components"]["schemas"] = schemas
    return document


_HEADER = (
    "# API contract skeleton — generated by teamwork-tasks-from-dnr.\n"
    "# Endpoints marked `x-wame-status: draft` and any `[DOPLNIŤ]` value need\n"
    "# review before the contract is merged. Re-running the skill diffs against\n"
    "# this file instead of overwriting it — do not lose manual edits.\n"
)


def emit_openapi_yaml(contract: dict, error_convention: str = "http_status",
                      language: str = "sk") -> str:
    """Render the full `openapi.yaml` text (header comment + YAML body)."""
    document = build_openapi(contract, error_convention, language)
    return _HEADER + to_yaml(document)


# ===========================================================================
# data-model.md renderer
# ===========================================================================

_DM_LABELS = {
    "sk": {
        "suffix": "Dátový model",
        "intro": "Kostra dátového modelu odvodená z DNR — podklad pre migrácie a ERD.",
        "cols": ["Pole", "Typ", "Nullable", "Default", "Popis"],
        "yes": "áno", "no": "nie",
        "relations": "Vzťahy", "indexes": "Indexy", "notes": "Poznámky",
        "unique": "unikátny",
        "no_entities": "_Žiadne entity neboli odvodené z DNR — [DOPLNIŤ]._",
    },
    "cs": {
        "suffix": "Datový model",
        "intro": "Kostra datového modelu odvozená z DNR — podklad pro migrace a ERD.",
        "cols": ["Pole", "Typ", "Nullable", "Default", "Popis"],
        "yes": "ano", "no": "ne",
        "relations": "Vztahy", "indexes": "Indexy", "notes": "Poznámky",
        "unique": "unikátní",
        "no_entities": "_Žádné entity nebyly odvozeny z DNR — [DOPLNIŤ]._",
    },
    "en": {
        "suffix": "Data model",
        "intro": "Data-model skeleton derived from the DNR — basis for migrations and ERD.",
        "cols": ["Field", "Type", "Nullable", "Default", "Description"],
        "yes": "yes", "no": "no",
        "relations": "Relations", "indexes": "Indexes", "notes": "Notes",
        "unique": "unique",
        "no_entities": "_No entities were derived from the DNR — [DOPLNIŤ]._",
    },
}


def _md_cell(value) -> str:
    """Escape a Markdown table cell (pipes and newlines)."""
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def emit_data_model_md(data_model: dict, title: str, language: str = "sk") -> str:
    lang = language if language in _DM_LABELS else "en"
    labels = _DM_LABELS[lang]
    lines: list[str] = [f"# {title} — {labels['suffix']}", "", f"> {labels['intro']}", ""]

    entities = (data_model or {}).get("entities") or []
    if not entities:
        lines.append(labels["no_entities"])
        lines.append("")
        return "\n".join(lines)

    for entity in entities:
        lines.append(f"## {entity.get('name', '[DOPLNIŤ]')}")
        lines.append("")
        if entity.get("description"):
            lines.append(entity["description"].strip())
            lines.append("")

        cols = labels["cols"]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for field in entity.get("fields") or []:
            nullable = labels["yes"] if field.get("nullable") else labels["no"]
            lines.append("| " + " | ".join([
                _md_cell(field.get("name")),
                _md_cell(field.get("type")),
                nullable,
                _md_cell(field.get("default")),
                _md_cell(field.get("description")),
            ]) + " |")
        lines.append("")

        relations = entity.get("relations") or []
        if relations:
            lines.append(f"**{labels['relations']}:**")
            for rel in relations:
                kind = rel.get("kind", "")
                target = rel.get("target", "")
                desc = rel.get("description", "")
                tail = f" — {desc}" if desc else ""
                lines.append(f"- {kind} `{target}`{tail}".rstrip())
            lines.append("")

        indexes = entity.get("indexes") or []
        if indexes:
            lines.append(f"**{labels['indexes']}:**")
            for idx in indexes:
                columns = ", ".join(idx.get("columns") or [])
                flag = f" ({labels['unique']})" if idx.get("unique") else ""
                desc = idx.get("description", "")
                tail = f" — {desc}" if desc else ""
                lines.append(f"- ({columns}){flag}{tail}".rstrip())
            lines.append("")

        notes = entity.get("notes") or []
        if notes:
            lines.append(f"**{labels['notes']}:**")
            for note in notes:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", required=True, help="Path to a single contract JSON")
    p.add_argument("--error-convention", default="http_status",
                   choices=["http_status", "ok"])
    p.add_argument("--language", default="sk")
    args = p.parse_args()

    data = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    print(emit_openapi_yaml(data, args.error_convention, args.language))
