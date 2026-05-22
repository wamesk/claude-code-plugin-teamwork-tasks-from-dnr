#!/usr/bin/env python3
"""
teamwork_tasks — orchestrator script for the teamwork-tasks-from-dnr plugin.

Modes:
    --init                          Create per-project config from template.
    --plan --dnr <path>             Extract DNR text + metadata as JSON.
    --validate --json <path>        Validate a plan JSON against schema.
    --build --json <path> [...]     Write MD + XLSX from a plan JSON.

Claude (via SKILL.md) does the LLM extraction between --plan and --build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

# Make sibling modules importable when this script is executed directly.
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROMPTS_DIR = SKILL_DIR / "prompts"
PLUGIN_ROOT = SKILL_DIR.parent.parent
DEFAULT_CONFIG_TEMPLATE = PLUGIN_ROOT / "config.example.json"

sys.path.insert(0, str(SCRIPT_DIR))

import dnr_to_text  # noqa: E402
import json_to_md  # noqa: E402
import json_to_xlsx  # noqa: E402
import validate_json  # noqa: E402

PLUGIN_SLUG = "teamwork-tasks-from-dnr-wamesk"
DATA_ROOT = Path.home() / ".claude" / "plugins" / "data" / PLUGIN_SLUG


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def project_config_dir(project_root: Path) -> Path:
    project_hash = hashlib.md5(str(project_root.resolve()).encode()).hexdigest()[:12]
    return DATA_ROOT / project_hash


def default_config() -> dict:
    if DEFAULT_CONFIG_TEMPLATE.exists():
        return json.loads(DEFAULT_CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    return {
        "output_dir": "docs",
        "output_basename": "auto",
        "language": "auto",
        "include_tags": False,
        "default_status": "Active",
    }


def load_config(project_root: Path) -> dict:
    cfg_path = project_config_dir(project_root) / "config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return default_config()


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------


def cmd_init(args) -> dict:
    project_root = Path.cwd()
    cfg_dir = project_config_dir(project_root)
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.json"
    if not cfg_path.exists() and DEFAULT_CONFIG_TEMPLATE.exists():
        shutil.copy(DEFAULT_CONFIG_TEMPLATE, cfg_path)
    return {"config_path": str(cfg_path), "project_root": str(project_root)}


def cmd_plan(args) -> dict:
    dnr_path = Path(args.dnr).expanduser().resolve()
    result = dnr_to_text.parse(dnr_path)
    if result.get("warning"):
        return result
    # Add prompt/schema paths so SKILL.md can locate them generically.
    result["prompt_path"] = str(PROMPTS_DIR / "extract_dnr_to_json.md")
    result["schema_path"] = str(PROMPTS_DIR / "json_schema.json")
    return result


def cmd_validate(args) -> dict:
    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    schema = json.loads(Path(args.schema or (PROMPTS_DIR / "json_schema.json"))
                        .read_text(encoding="utf-8"))
    ok, errors = validate_json.validate_plan(plan, schema)
    return {"valid": ok, "errors": errors}


def cmd_build(args) -> dict:
    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    schema = json.loads((PROMPTS_DIR / "json_schema.json").read_text(encoding="utf-8"))

    ok, errors = validate_json.validate_plan(plan, schema)
    if not ok:
        return {"ok": False, "errors": errors, "files": []}

    config = load_config(Path.cwd())
    output_dir = Path(args.output_dir or config.get("output_dir") or "docs")
    basename = args.basename or _derive_basename(plan, config)

    md_path = output_dir / f"{basename}_TeamworkTasks.md"
    xlsx_path = output_dir / f"{basename}_TeamworkTasks.xlsx"

    json_to_md.write(plan, md_path)
    json_to_xlsx.write(
        plan, xlsx_path,
        layout=config.get("xlsx_layout"),
        include_tags=config.get("include_tags", False),
        default_status=config.get("default_status", "Active"),
    )

    return {
        "ok": True,
        "files": [str(md_path), str(xlsx_path)],
        "stats": {
            "tasklists": len(plan.get("tasklists", [])),
            "tasks": sum(len(tl.get("tasks", [])) for tl in plan.get("tasklists", [])),
            "total_minutes": sum(
                int(t.get("estimated_minutes", 0))
                for tl in plan.get("tasklists", []) for t in tl.get("tasks", [])
            ),
            "total_md": plan.get("metadata", {}).get("total_md_estimate"),
        },
    }


def _derive_basename(plan: dict, config: dict) -> str:
    """Pick a sensible basename for output files."""
    if config.get("output_basename") and config["output_basename"] != "auto":
        return config["output_basename"]
    source = plan.get("metadata", {}).get("source_dnr_path")
    if source:
        return Path(source).stem
    title = plan.get("metadata", {}).get("title", "TeamworkTasks")
    return title.replace(" ", "_")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pretty", action="store_true")

    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--init", action="store_true")
    sub.add_argument("--plan", action="store_true")
    sub.add_argument("--validate", action="store_true")
    sub.add_argument("--build", action="store_true")

    parser.add_argument("--dnr", help="Path to DNR document (for --plan)")
    parser.add_argument("--json", help="Path to plan JSON (for --validate / --build)")
    parser.add_argument("--schema", help="Path to schema JSON (for --validate)")
    parser.add_argument("--output-dir", help="Output directory (for --build)")
    parser.add_argument("--basename", help="Output basename (for --build)")

    args = parser.parse_args()

    if args.init:
        result = cmd_init(args)
    elif args.plan:
        if not args.dnr:
            parser.error("--plan requires --dnr <path>")
        result = cmd_plan(args)
    elif args.validate:
        if not args.json:
            parser.error("--validate requires --json <path>")
        result = cmd_validate(args)
    elif args.build:
        if not args.json:
            parser.error("--build requires --json <path>")
        result = cmd_build(args)
    else:
        parser.print_help()
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0 if result.get("valid", True) and result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
