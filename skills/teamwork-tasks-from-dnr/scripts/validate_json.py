#!/usr/bin/env python3
"""
validate_json — minimal JSON-schema validator for the Teamwork tasks plan.

Implements a subset of JSON Schema Draft-07 that covers the constructs used
in `prompts/json_schema.json`: type, required, properties, items, enum,
minItems, minLength, minimum, maximum. Avoids the `jsonschema` PyPI dependency
to stay stdlib-only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import cross_cutting

# Contract cross-validation constants.
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationError(Exception):
    def __init__(self, message: str, path: list):
        super().__init__(message)
        self.path = path

    def __str__(self) -> str:
        loc = "/".join(str(p) for p in self.path) or "<root>"
        return f"At {loc}: {self.args[0]}"


# ---------------------------------------------------------------------------

TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def validate(instance, schema, path: list | None = None) -> list[str]:
    """Validate `instance` against `schema`. Return list of error messages."""
    path = path or []
    errors: list[str] = []
    try:
        _validate_node(instance, schema, path)
    except ValidationError as e:
        errors.append(str(e))
    return errors


def _validate_node(instance, schema, path: list) -> None:
    # Type check.
    if "type" in schema:
        expected = schema["type"]
        py_type = TYPE_MAP.get(expected)
        if py_type and not isinstance(instance, py_type):
            # Special case: integer should not match bool (Python's bool is int).
            if expected == "integer" and isinstance(instance, bool):
                raise ValidationError(f"expected integer, got boolean", path)
            raise ValidationError(
                f"expected type '{expected}', got '{type(instance).__name__}'", path)

    # Enum check.
    if "enum" in schema:
        if instance not in schema["enum"]:
            raise ValidationError(
                f"value {instance!r} not in enum {schema['enum']}", path)

    # Object: required + properties.
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                raise ValidationError(f"missing required key '{req}'", path)
        for key, value in instance.items():
            if "properties" in schema and key in schema["properties"]:
                _validate_node(value, schema["properties"][key], path + [key])

    # Array: items + minItems.
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValidationError(
                f"array has {len(instance)} items, minimum {schema['minItems']}", path)
        if "items" in schema:
            for i, item in enumerate(instance):
                _validate_node(item, schema["items"], path + [i])

    # String: minLength.
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValidationError(
                f"string length {len(instance)} below minimum {schema['minLength']}", path)

    # Numeric: minimum / maximum.
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValidationError(
                f"value {instance} below minimum {schema['minimum']}", path)
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValidationError(
                f"value {instance} above maximum {schema['maximum']}", path)


# ---------------------------------------------------------------------------
# Plan-specific cross-field checks beyond JSON Schema's expressive power.
# ---------------------------------------------------------------------------


def cross_validate(plan: dict) -> list[str]:
    """Cross-field business validations on a plan."""
    issues: list[str] = []
    for tl_idx, tl in enumerate(plan.get("tasklists", [])):
        md_estimate = tl.get("md_estimate")
        total_min = sum(int(t.get("estimated_minutes", 0)) for t in tl.get("tasks", []))
        if md_estimate is not None and total_min > 0:
            expected_min = round(md_estimate * 480)
            # Tolerate 5 % drift.
            if abs(total_min - expected_min) > max(60, expected_min * 0.05):
                issues.append(
                    f"tasklists[{tl_idx}] '{tl.get('name', '')}' — sum of "
                    f"estimated_minutes ({total_min}) deviates from "
                    f"md_estimate × 480 ({expected_min}) by more than 5% or 60min")
        # Per-task minute divisibility.
        for t_idx, task in enumerate(tl.get("tasks", [])):
            minutes = int(task.get("estimated_minutes", 0))
            if minutes % 15 != 0:
                issues.append(
                    f"tasklists[{tl_idx}]/tasks[{t_idx}] '{task.get('name', '')}' — "
                    f"estimated_minutes ({minutes}) not divisible by 15")
    issues.extend(_contract_issues(plan))
    # A task that adds a new screen must say how a user reaches it.
    issues.extend(cross_cutting.issues(plan))
    return issues


def _contract_issues(plan: dict) -> list[str]:
    """Cross-field checks for the contract-first fields (spec §6).

    These only bite in backend mode (when `contracts` is present). Frontend /
    standalone plans reference a contract via `contract_ref` without carrying a
    `contracts[]` block, so the referential checks are skipped for them.
    """
    issues: list[str] = []
    contracts = plan.get("contracts") or []
    slugs = {c.get("feature_slug") for c in contracts if c.get("feature_slug")}

    for c_idx, contract in enumerate(contracts):
        slug = contract.get("feature_slug", "")
        if slug and not _KEBAB_RE.match(slug):
            issues.append(
                f"contracts[{c_idx}] feature_slug '{slug}' is not kebab-case")
        endpoints = (contract.get("openapi") or {}).get("endpoints") or []
        seen_ops: set[str] = set()
        for e_idx, endpoint in enumerate(endpoints):
            method = (endpoint.get("method") or "").lower()
            if method not in HTTP_METHODS:
                issues.append(
                    f"contracts[{c_idx}]/endpoints[{e_idx}] method "
                    f"'{endpoint.get('method')}' is not a valid HTTP method")
            op_id = endpoint.get("operation_id", "")
            if op_id and not op_id.isascii():
                issues.append(
                    f"contracts[{c_idx}]/endpoints[{e_idx}] operation_id "
                    f"'{op_id}' must be ASCII (English, goes into generated types)")
            if op_id and op_id in seen_ops:
                issues.append(
                    f"contracts[{c_idx}] duplicate operation_id '{op_id}'")
            seen_ops.add(op_id)

    # Referential integrity between tasks and contracts (backend mode only).
    contract_task_slugs: set[str] = set()
    for tl in plan.get("tasklists", []):
        for task in tl.get("tasks", []):
            ref = task.get("contract_ref")
            if ref:
                fslug = ref.get("feature_slug")
                if contracts and fslug not in slugs:
                    issues.append(
                        f"task '{task.get('name', '')}' references unknown "
                        f"contract feature_slug '{fslug}'")
                if task.get("task_kind") == "contract" and fslug:
                    contract_task_slugs.add(fslug)

    for slug in slugs:
        if slug not in contract_task_slugs:
            issues.append(
                f"contract '{slug}' has no 'Definovať API kontrakt' task "
                f"(task_kind='contract' with contract_ref.feature_slug='{slug}')")

    return issues


def validate_plan(plan: dict, schema: dict) -> tuple[bool, list[str]]:
    """Run schema + cross-field validation. Returns (ok, errors)."""
    errors = validate(plan, schema)
    errors.extend(cross_validate(plan))
    return (not errors, errors)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True, help="Plan JSON path")
    p.add_argument("--schema", required=True, help="Schema JSON path")
    args = p.parse_args()

    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    ok, errors = validate_plan(plan, schema)
    if ok:
        print("✅ Plan is valid.")
    else:
        print(f"❌ Plan has {len(errors)} validation issue(s):")
        for e in errors:
            print(f"  - {e}")
    import sys
    sys.exit(0 if ok else 1)
