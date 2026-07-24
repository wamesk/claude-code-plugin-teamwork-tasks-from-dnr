#!/usr/bin/env python3
"""
contract_writer — idempotent, preview-then-apply writing of the API contract
artifacts under `docs/contracts/`.

Safety rules (spec §7):
  - Contract files are written only if they do not already exist.
  - If an `openapi.yaml` / `data-model.md` already exists and differs, we write
    a sibling `*.proposed` file and surface a unified diff instead of silently
    overwriting a hand-edited contract.
  - The shared `_shared/wame-envelope.yaml` is only ever *created* (never
    overwritten, never `.proposed`d) — it is a static, feature-independent file.
  - `--force` (apply only) overwrites the original in place; nothing else does.

The module is deliberately two-phase: `plan_writes()` computes what *would*
happen (including diffs) without touching the filesystem, so the SKILL can show
a preview and ask for confirmation; `apply_writes()` performs it.

Stdlib only.
"""
from __future__ import annotations

import difflib
from pathlib import Path

import contract_emit

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PLUGIN_ROOT = SKILL_DIR.parent.parent
DEFAULT_ENVELOPE_ASSET = PLUGIN_ROOT / "assets" / "wame-envelope.yaml"

# Embedded copy of the shared envelope. Used when the shipped asset file cannot
# be located (e.g. a trimmed Claude.ai skill upload). Keep byte-identical with
# `assets/wame-envelope.yaml`.
FALLBACK_ENVELOPE = """\
# WAME shared response envelope — referenced by every contract's openapi.yaml
# via `$ref: ../_shared/wame-envelope.yaml#/components/schemas/...`.
# This file is created once per project and is intentionally feature-agnostic.
openapi: "3.1.0"
info:
  title: WAME shared response envelope
  version: "0.1.0"
paths: {}
components:
  schemas:
    WameSuccess:
      type: object
      required: [type, code, data]
      properties:
        type:
          type: string
          const: success
          description: Discriminator — always the literal "success".
        code:
          type: string
          description: Machine code / translation key (e.g. order.synced).
        data:
          description: Endpoint-specific payload (concretised via allOf).
    WameError:
      type: object
      required: [type, code, message]
      properties:
        type:
          type: string
          const: error
          description: Discriminator — always the literal "error".
        code:
          type: string
          description: Machine code / translation key (e.g. order.not_found).
        message:
          type: string
          description: Human-readable error message.
        exception:
          type: [string, "null"]
          description: Exception class / detail, null in production.
"""


# ---------------------------------------------------------------------------
# Target computation (single source of truth for both phases)
# ---------------------------------------------------------------------------


def _envelope_content(envelope_asset: Path) -> str:
    asset = Path(envelope_asset)
    if asset.exists():
        try:
            return asset.read_text(encoding="utf-8")
        except OSError:
            pass
    return FALLBACK_ENVELOPE


def build_targets(base_dir: Path, plan: dict, *,
                  error_convention: str = "http_status",
                  envelope_asset: Path = DEFAULT_ENVELOPE_ASSET) -> list[dict]:
    """Return the list of files this plan would produce under `base_dir`.

    Each target: {path: Path, content: str, only_if_absent: bool,
                  role: envelope|openapi|data-model, slug: str|None}.
    The shared envelope is emitted once; every contract yields an openapi.yaml
    and a data-model.md.
    """
    base_dir = Path(base_dir)
    language = (plan.get("metadata", {}) or {}).get("language", "sk")
    contracts = plan.get("contracts") or []

    targets: list[dict] = []
    if contracts:
        targets.append({
            "path": base_dir / "_shared" / "wame-envelope.yaml",
            "content": _envelope_content(envelope_asset),
            "only_if_absent": True,
            "role": "envelope",
            "slug": None,
        })

    for contract in contracts:
        slug = contract.get("feature_slug") or "kontrakt"
        title = contract.get("title") or slug
        cdir = base_dir / slug
        targets.append({
            "path": cdir / "openapi.yaml",
            "content": contract_emit.emit_openapi_yaml(
                contract, error_convention, language),
            "only_if_absent": False,
            "role": "openapi",
            "slug": slug,
        })
        targets.append({
            "path": cdir / "data-model.md",
            "content": contract_emit.emit_data_model_md(
                contract.get("data_model") or {}, title, language),
            "only_if_absent": False,
            "role": "data-model",
            "slug": slug,
        })
    return targets


def _proposed_path(path: Path) -> Path:
    return path.with_name(path.name + ".proposed")


# ---------------------------------------------------------------------------
# Phase 1 — plan (no filesystem writes)
# ---------------------------------------------------------------------------


def plan_writes(base_dir: Path, plan: dict, *,
                error_convention: str = "http_status",
                envelope_asset: Path = DEFAULT_ENVELOPE_ASSET) -> dict:
    """Compute intended actions + diffs without writing anything."""
    targets = build_targets(base_dir, plan, error_convention=error_convention,
                            envelope_asset=envelope_asset)
    actions: list[dict] = []
    for target in targets:
        path: Path = target["path"]
        content: str = target["content"]
        entry = {
            "path": str(path),
            "role": target["role"],
            "slug": target["slug"],
            "bytes": len(content.encode("utf-8")),
            "lines": content.count("\n"),
        }
        if not path.exists():
            entry["action"] = "create"
        else:
            existing = _safe_read(path)
            if existing == content:
                entry["action"] = "unchanged"
            elif target["only_if_absent"]:
                entry["action"] = "skip"  # envelope present — leave untouched
            else:
                proposed = _proposed_path(path)
                entry["action"] = "exists"
                entry["proposed_path"] = str(proposed)
                entry["diff"] = _unified_diff(existing, content, path, proposed)
        actions.append(entry)

    return {
        "base_dir": str(Path(base_dir)),
        "contracts": [c.get("feature_slug") for c in (plan.get("contracts") or [])],
        "actions": actions,
        "needs_confirmation": any(a["action"] == "exists" for a in actions),
    }


# ---------------------------------------------------------------------------
# Phase 2 — apply
# ---------------------------------------------------------------------------


def apply_writes(base_dir: Path, plan: dict, *, force: bool = False,
                 error_convention: str = "http_status",
                 envelope_asset: Path = DEFAULT_ENVELOPE_ASSET) -> dict:
    """Perform the writes computed from the plan. Returns a per-file summary."""
    targets = build_targets(base_dir, plan, error_convention=error_convention,
                            envelope_asset=envelope_asset)
    results: list[dict] = []
    for target in targets:
        path: Path = target["path"]
        content: str = target["content"]
        result = {"path": str(path), "role": target["role"], "slug": target["slug"]}

        if not path.exists():
            _write(path, content)
            result["action"] = "created"
        elif _safe_read(path) == content:
            result["action"] = "unchanged"
        elif target["only_if_absent"]:
            result["action"] = "skipped"
        elif force:
            _write(path, content)
            result["action"] = "overwritten"
        else:
            proposed = _proposed_path(path)
            _write(proposed, content)
            result["action"] = "proposed"
            result["proposed_path"] = str(proposed)
        results.append(result)

    return {
        "base_dir": str(Path(base_dir)),
        "results": results,
        "proposed": [r for r in results if r["action"] == "proposed"],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _unified_diff(existing: str, proposed: str, from_path: Path, to_path: Path) -> str:
    return "".join(difflib.unified_diff(
        existing.splitlines(keepends=True),
        proposed.splitlines(keepends=True),
        fromfile=str(from_path),
        tofile=str(to_path),
    ))


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True, help="Plan JSON with contracts[]")
    p.add_argument("--contract-dir", default="docs/contracts")
    p.add_argument("--error-convention", default="http_status",
                   choices=["http_status", "ok"])
    p.add_argument("--apply", action="store_true", help="Write (default is plan/preview)")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if args.apply:
        out = apply_writes(args.contract_dir, plan, force=args.force,
                           error_convention=args.error_convention)
    else:
        out = plan_writes(args.contract_dir, plan,
                          error_convention=args.error_convention)
    print(json.dumps(out, indent=2, ensure_ascii=False))
