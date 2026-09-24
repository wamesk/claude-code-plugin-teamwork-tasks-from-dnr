#!/usr/bin/env python3
"""
repo_detect — detect whether the current repository is a WAME backend
(Laravel), a WAME frontend (Ionic Vue), or neither (standalone).

The contract-first extension of this plugin only generates an API contract
inside a *backend* repository; a *frontend* repository merely references an
existing contract, and *standalone* runs (e.g. Claude.ai without a repo) skip
contract generation entirely.

It also reports the framework / language versions installed in the repo
(`detect_versions`), so the technical plan of every generated task can tell the
implementer to respect those versions and their current idioms.

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
    except (ValueError, OSError):
        # ValueError covers JSONDecodeError and UnicodeDecodeError (a lock
        # file with stray bytes must not crash --detect-repo).
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
# Installed framework versions (context for the technical plan)
# ---------------------------------------------------------------------------

# Composer packages whose installed version shapes which idioms a task may use.
_COMPOSER_PACKAGES = (
    ("laravel/framework", "Laravel"),
    ("laravel/nova", "Nova"),
    ("livewire/livewire", "Livewire"),
    ("inertiajs/inertia-laravel", "Inertia (Laravel)"),
    ("pestphp/pest", "Pest"),
)

# npm packages, same purpose. The installed version from package-lock.json
# wins; otherwise the range declared in package.json.
_NPM_PACKAGES = (
    ("vue", "Vue"),
    ("nuxt", "Nuxt"),
    ("react", "React"),
    ("@ionic/vue", "Ionic Vue"),
    ("@inertiajs/vue3", "Inertia (Vue 3)"),
    ("tailwindcss", "Tailwind CSS"),
    ("vite", "Vite"),
    ("typescript", "TypeScript"),
)


def _strip_v(version) -> str:
    """`v12.28.1` → `12.28.1` (Composer tags often carry a `v` prefix)."""
    version = str(version or "").strip()
    if version[:1] in ("v", "V") and version[1:2].isdigit():
        return version[1:]
    return version


def detect_versions(root: Path) -> dict:
    """Read the framework / language versions the repository actually uses.

    The technical plan of a generated task tells the implementer to respect
    the *installed* versions and their current idioms, so the versions come
    from the manifest and lock files — never from anyone's memory. Sources,
    all optional:

        composer.json    `config.platform.php`, else `require.php`  -> "php"
        composer.lock    installed version of `_COMPOSER_PACKAGES`
        package-lock     installed version of `_NPM_PACKAGES`
                         (lockfileVersion 2/3 `packages`, v1 `dependencies`)
        package.json     declared range when there is no lock entry,
                         `engines.node`, `browserslist`
        .nvmrc           Node version (wins over `engines.node`)
        .browserslistrc  browser targets (win over `browserslist`)

    Returns an ordered dict `{package: version}`; empty when nothing is found.
    A missing or malformed file is skipped — this is plan context, not a gate,
    and the plan then falls back to the generic framework line.
    """
    root = Path(root)
    versions: dict[str, str] = {}

    composer = _obj(_load_json(root / "composer.json"))
    platform = _obj(_obj(composer.get("config")).get("platform"))
    php = platform.get("php") or _obj(composer.get("require")).get("php")
    if php:
        versions["php"] = str(php)

    lock = _obj(_load_json(root / "composer.lock"))
    installed: dict[str, str] = {}
    for key in ("packages", "packages-dev"):
        pkgs = lock.get(key)
        for pkg in pkgs if isinstance(pkgs, list) else []:
            if isinstance(pkg, dict) and pkg.get("name") and pkg.get("version"):
                installed[pkg["name"]] = _strip_v(pkg["version"])
    for name, _label in _COMPOSER_PACKAGES:
        if name in installed:
            versions[name] = installed[name]

    package = _obj(_load_json(root / "package.json"))
    declared = {**_obj(package.get("dependencies")),
                **_obj(package.get("devDependencies"))}
    npm_lock_json = _obj(_load_json(root / "package-lock.json"))
    npm_lock = _obj(npm_lock_json.get("packages"))
    npm_lock_v1 = _obj(npm_lock_json.get("dependencies"))
    for name, _label in _NPM_PACKAGES:
        entry = npm_lock.get(f"node_modules/{name}") or npm_lock_v1.get(name)
        if isinstance(entry, dict) and entry.get("version"):
            versions[name] = str(entry["version"])
        elif name in declared:
            versions[name] = str(declared[name])

    node = _first_line(root / ".nvmrc") or _obj(package.get("engines")).get("node")
    if node:
        versions["node"] = str(node)

    targets = _browserslist(root / ".browserslistrc") or package.get("browserslist")
    if isinstance(targets, list):
        targets = ", ".join(str(q) for q in targets)
    if isinstance(targets, str) and targets.strip():
        versions["browserslist"] = targets.strip()

    return versions


def _obj(value) -> dict:
    """`value` when it is a JSON object, else `{}` — a hand-edited manifest
    with an unexpected shape must not crash the detection."""
    return value if isinstance(value, dict) else {}


def _first_line(path: Path) -> str | None:
    """First non-empty line of a small text file, or None."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip()
    except (OSError, UnicodeDecodeError):
        pass
    return None


def _browserslist(path: Path) -> str | None:
    """Queries of a `.browserslistrc` joined by `, ` (comments and
    `[env]` section headers dropped)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    queries = [line.split("#", 1)[0].strip() for line in text.splitlines()]
    queries = [q for q in queries if q and not q.startswith("[")]
    return ", ".join(queries) or None


def manifest_root(start: Path, git_root: Path) -> Path:
    """The directory whose manifests describe the code at `start`: the nearest
    one from `start` up to `git_root` that holds a `composer.json` or a
    `package.json`, else `git_root`. The app often lives in a subdirectory of
    the repository (e.g. `<repo>/appbase/`), where the git root has no
    manifest at all."""
    start = Path(start).resolve()
    git_root = Path(git_root).resolve()
    for directory in (start, *start.parents):
        if (directory / "composer.json").is_file() or (directory / "package.json").is_file():
            return directory
        if directory == git_root:
            break
    return git_root


def versions_summary(versions: dict) -> str | None:
    """One readable line for the technical plan, e.g.
    `PHP ^8.3, Laravel 12.28.1, Vue 3.5.13`. None when nothing was detected —
    the plan then carries the generic framework line."""
    labels = {"php": "PHP", "node": "Node",
              **dict(_COMPOSER_PACKAGES), **dict(_NPM_PACKAGES)}
    order = ["php", *(n for n, _ in _COMPOSER_PACKAGES),
             *(n for n, _ in _NPM_PACKAGES), "node"]
    parts = [f"{labels[name]} {versions[name]}" for name in order if name in versions]
    if versions.get("browserslist"):
        parts.append(f"browserslist: {versions['browserslist']}")
    return ", ".join(parts) or None


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
        framework_versions — installed framework / language versions read
                        from the manifest and lock files of the nearest
                        directory between `cwd` and the git root that has a
                        composer.json / package.json (in every mode, as long
                        as there is a git root); {} else
        framework_summary  — the same as one readable line, or None
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
        "framework_versions": {},
        "framework_summary": None,
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

    # Versions matter in every mode — a plain Vue / Nuxt repo is "standalone"
    # for the contract flow but still has installed versions to respect.
    # Read them where the app actually lives — the nearest manifest between
    # the start directory and the git root.
    result["framework_versions"] = detect_versions(manifest_root(start_path, git_root))
    result["framework_summary"] = versions_summary(result["framework_versions"])

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps(detect_repo_mode(target), indent=2, ensure_ascii=False))
