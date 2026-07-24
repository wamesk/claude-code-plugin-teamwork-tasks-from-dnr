"""Tests for repository mode detection (repo_detect.py)."""
import json

import repo_detect


def _write(path, name, obj):
    (path / name).write_text(json.dumps(obj), encoding="utf-8")


def _git(path):
    (path / ".git").mkdir()


def test_backend_detected(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12.0"}})
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["mode"] == "backend"
    assert result["is_backend"] and not result["is_frontend"]
    assert result["warning"] is None


def test_backend_require_dev(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require-dev": {"laravel/framework": "^12.0"}})
    assert repo_detect.detect_repo_mode(tmp_path)["mode"] == "backend"


def test_frontend_vue(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "package.json", {"dependencies": {"@ionic/vue": "^8"}})
    assert repo_detect.detect_repo_mode(tmp_path)["mode"] == "frontend"


def test_frontend_core_in_dev_deps(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "package.json", {"devDependencies": {"@ionic/core": "^8"}})
    assert repo_detect.detect_repo_mode(tmp_path)["mode"] == "frontend"


def test_monorepo_prefers_backend_with_warning(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12"}})
    _write(tmp_path, "package.json", {"dependencies": {"@ionic/vue": "^8"}})
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["mode"] == "backend"
    assert result["warning"] and "monorepo" in result["warning"].lower()


def test_standalone_without_git(tmp_path):
    # composer.json present but no .git → standalone (contract needs a repo).
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12"}})
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["mode"] == "standalone"
    assert result["is_backend"] is False


def test_git_repo_but_neither_is_standalone(tmp_path):
    _git(tmp_path)
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["mode"] == "standalone"
    assert result["git_root"] is not None


def test_find_git_root_walks_up(tmp_path):
    _git(tmp_path)
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert repo_detect.find_git_root(nested) == tmp_path.resolve()


def test_repo_name_from_https_remote(tmp_path):
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    (gitdir / "config").write_text(
        '[remote "origin"]\n\turl = https://github.com/wamesk/foo-bar.git\n',
        encoding="utf-8")
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12"}})
    assert repo_detect.detect_repo_mode(tmp_path)["repo_name"] == "foo-bar"


def test_repo_name_from_scp_remote(tmp_path):
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    (gitdir / "config").write_text(
        '[remote "origin"]\n\turl = git@github.com:wamesk/baz-svc.git\n',
        encoding="utf-8")
    _write(tmp_path, "package.json", {"dependencies": {"@ionic/vue": "^8"}})
    assert repo_detect.detect_repo_mode(tmp_path)["repo_name"] == "baz-svc"


def test_wamesk_modules_detected(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12"}})
    module = tmp_path / "wamesk" / "orders"
    (module / "src").mkdir(parents=True)
    (module / "composer.json").write_text("{}", encoding="utf-8")
    result = repo_detect.detect_repo_mode(tmp_path)
    assert any(m["name"] == "orders" for m in result["modules"])
