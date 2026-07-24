#!/usr/bin/env python3
"""
repo_detect — detect whether the current repository is a WAME backend
(Laravel), a WAME frontend (Ionic Vue), or neither (standalone).

The contract-first extension of this plugin only generates an API contract
inside a *backend* repository; a *frontend* repository merely references an
existing contract, and *standalone* runs (e.g. Claude.ai without a repo) skip
contract generation entirely.

Detection rules (spec §4), checked from the git root walking up from `cwd`:
    - composer.json contains `laravel/framework`            -> backend
    - package.json contains `@ionic/vue` or `@ionic/core`   -> frontend
    - both at once (monorepo)                               -> backend + warning
    - neither / not a git repo                              -> standalone

The Laravel/module detection helpers (`is_backend`, `detect_modules`) are
copied from the sibling plugin `laravel-docs`
(`skills/laravel-docs/scripts/laravel_docs.py`: `is_laravel_project`,
`detect_modules`). The spec forbids sharing code across the separate plugin
repositories, so the logic is duplicated here on purpose — keep the two in
sync when the module layout conventions change.

Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Git root
# ---------------------------------------------------------------------------


def find_git_root(start: Path) -> Path | None:
    """Walk upwards from `start` until a directory containing `.git` is found.

    `.git` may be a directory (normal checkout) or a file (git worktree /
    submodule). Returns the directory that holds it, or None if we reach the
    filesystem root without finding one.
    """
    start = Path(start).resolve()
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


# ---------------------------------------------------------------------------
# Package-manifest helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict | None:
    """Best-effort JSON load; returns None on missing file or parse error."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def is_backend(root: Path) -> bool:
    """True if composer.json declares laravel/framework (or laravel/laravel).

    Copied from laravel-docs `is_laravel_project`.
    """
    data = _load_json(root / "composer.json")
    if not data:
        return False
    deps = {**data.get("require", {}), **data.get("require-dev", {})}
    return "laravel/framework" in deps or "laravel/laravel" in deps


# Ionic packages that reliably mark a WAME frontend repository.
_IONIC_PACKAGES = ("@ionic/vue", "@ionic/core")


def is_frontend(root: Path) -> bool:
    """True if package.json depends on an Ionic package (`@ionic/vue|core`)."""
    data = _load_json(root / "package.json")
    if not data:
        return False
    deps = {
        **data.get("dependencies", {}),
        **data.get("devDependencies", {}),
    }
    return any(pkg in deps for pkg in _IONIC_PACKAGES)


# ---------------------------------------------------------------------------
# Repo name (for the `### Kontrakt` "Repo:" line)
# ---------------------------------------------------------------------------

# `url = <x>` line inside the `[remote "origin"]` section of .git/config.
_GIT_URL_RE = re.compile(r"^\s*url\s*=\s*(.+?)\s*$", re.MULTILINE)


def repo_name(root: Path) -> str:
    """Best-effort short repository name.

    Prefers the basename of the `origin` remote URL (without a trailing
    `.git`); falls back to the directory name. Cosmetic only — it appears in
    the `Repo:` line of the `### Kontrakt` block.
    """
    config = root / ".git" / "config"
    text = None
    if config.exists():
        try:
            text = config.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = None
    if text:
        url = _origin_url(text)
        if url:
            name = url.rstrip("/").rsplit("/", 1)[-1]
            name = name.rsplit(":", 1)[-1]  # handle scp-style git@host:owner/repo
            if name.endswith(".git"):
                name = name[: -len(".git")]
            if name:
                return name
    return root.name


def _origin_url(config_text: str) -> str | None:
    """Extract the origin remote URL from a .git/config text."""
    section = None
    origin_url = None
    first_url = None
    for line in config_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        match = _GIT_URL_RE.match(line)
        if match:
            url = match.group(1).strip()
            if first_url is None:
                first_url = url
            if section and 'remote "origin"' in section:
                origin_url = url
    return origin_url or first_url


# ---------------------------------------------------------------------------
# Modules (context for feature-slug derivation) — copied from laravel-docs
# ---------------------------------------------------------------------------


def detect_modules(root: Path) -> list[dict]:
    """Detect wamesk-style or nwidart Modules/ style modules.

    Copied from laravel-docs `detect_modules`. Used only as context so the
    LLM / SKILL can derive a sensible `<feature-slug>`; not required for mode
    detection.
    """
    modules: list[dict] = []

    wamesk_dir = root / "wamesk"
    if wamesk_dir.is_dir():
        for child in sorted(wamesk_dir.iterdir()):
            if not child.is_dir():
                continue
            if (child / "src").is_dir() and (child / "composer.json").exists():
                modules.append({
                    "name": child.name,
                    "root": str(child.relative_to(root)),
                    "style": "wamesk",
                })

    nwidart_dir = root / "Modules"
    if nwidart_dir.is_dir():
        for child in sorted(nwidart_dir.iterdir()):
            if not child.is_dir():
                continue
            if (child / "Models").is_dir() or (child / "app" / "Models").is_dir():
                modules.append({
                    "name": child.name,
                    "root": str(child.relative_to(root)),
                    "style": "nwidart",
                })
    return modules


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------


def detect_repo_mode(start: Path | str | None = None) -> dict:
    """Classify the repository containing `start` as backend/frontend/standalone.

    Returns a dict with:
        mode          — "backend" | "frontend" | "standalone"
        git_root      — absolute path of the git root, or None
        repo_name     — short repo name (only meaningful for backend/frontend)
        is_backend    — bool
        is_frontend   — bool
        modules       — list of detected modules (backend context)
        cwd           — the resolved starting directory
        warning       — present for the monorepo edge case, else None
    """
    start_path = Path(start).resolve() if start else Path.cwd()
    git_root = find_git_root(start_path)

    result = {
        "mode": "standalone",
        "git_root": str(git_root) if git_root else None,
        "repo_name": None,
        "is_backend": False,
        "is_frontend": False,
        "modules": [],
        "cwd": str(start_path),
        "warning": None,
    }

    if git_root is None:
        # Not a git repository — treat as standalone (e.g. Claude.ai sandbox).
        return result

    backend = is_backend(git_root)
    frontend = is_frontend(git_root)
    result["is_backend"] = backend
    result["is_frontend"] = frontend

    if backend and frontend:
        # Monorepo: prefer backend (that is where the contract is authored),
        # but flag it so the caller can surface the ambiguity.
        result["mode"] = "backend"
        result["warning"] = (
            "Repository looks like a monorepo (both composer.json/laravel and "
            "package.json/@ionic detected). Defaulting to 'backend' mode — the "
            "contract is authored on the backend side. Re-run from the frontend "
            "sub-package, or pass --no-contract, if that is not intended."
        )
    elif backend:
        result["mode"] = "backend"
    elif frontend:
        result["mode"] = "frontend"
    else:
        # A git repo that is neither Laravel nor Ionic — no contract to author
        # or consume here.
        result["mode"] = "standalone"

    if result["mode"] != "standalone":
        result["repo_name"] = repo_name(git_root)
    if backend:
        result["modules"] = detect_modules(git_root)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps(detect_repo_mode(target), indent=2, ensure_ascii=False))
