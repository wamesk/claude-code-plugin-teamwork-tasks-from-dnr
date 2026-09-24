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


# --- installed framework versions (technical-plan `framework` line) -----------

def test_versions_from_lock_files(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {
        "require": {"php": "^8.2", "laravel/framework": "^12.0"},
        "config": {"platform": {"php": "8.3.12"}},
    })
    _write(tmp_path, "composer.lock", {
        "packages": [{"name": "laravel/framework", "version": "v12.28.1"},
                     {"name": "laravel/nova", "version": "5.7.4"},
                     {"name": "guzzlehttp/guzzle", "version": "7.9.2"}],
        "packages-dev": [{"name": "pestphp/pest", "version": "v3.8.2"}],
    })
    result = repo_detect.detect_repo_mode(tmp_path)
    versions = result["framework_versions"]
    # The platform pin wins over the require constraint; the `v` prefix goes.
    assert versions["php"] == "8.3.12"
    assert versions["laravel/framework"] == "12.28.1"
    assert versions["laravel/nova"] == "5.7.4"
    assert versions["pestphp/pest"] == "3.8.2"
    # Only the packages that shape idioms are reported.
    assert "guzzlehttp/guzzle" not in versions
    assert result["framework_summary"] == "PHP 8.3.12, Laravel 12.28.1, Nova 5.7.4, Pest 3.8.2"


def test_npm_lock_wins_over_declared_range(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "package.json", {
        "dependencies": {"vue": "^3.4.0", "@ionic/vue": "^8"},
        "devDependencies": {"tailwindcss": "^4.0.0"},
        "engines": {"node": ">=20"},
        "browserslist": ["> 0.5%", "not dead"],
    })
    _write(tmp_path, "package-lock.json", {
        "packages": {"node_modules/vue": {"version": "3.5.13"}},
    })
    (tmp_path / ".nvmrc").write_text("22.11.0\n", encoding="utf-8")
    versions = repo_detect.detect_repo_mode(tmp_path)["framework_versions"]
    assert versions["vue"] == "3.5.13"            # installed
    assert versions["tailwindcss"] == "^4.0.0"    # declared (no lock entry)
    assert versions["node"] == "22.11.0"          # .nvmrc wins over engines
    assert versions["browserslist"] == "> 0.5%, not dead"


def test_browserslistrc_wins_over_package_key(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "package.json", {"browserslist": ["defaults"]})
    (tmp_path / ".browserslistrc").write_text(
        "# targets\n[production]\nlast 2 versions\nnot dead # keep\n", encoding="utf-8")
    versions = repo_detect.detect_repo_mode(tmp_path)["framework_versions"]
    assert versions["browserslist"] == "last 2 versions, not dead"


def test_versions_empty_without_manifests_or_git(tmp_path):
    _git(tmp_path)
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["framework_versions"] == {}
    assert result["framework_summary"] is None
    # No git root → no versions either (the plan gets the generic line).
    bare = tmp_path / "bare"
    bare.mkdir()
    _write(bare, "composer.lock", {"packages": [{"name": "laravel/framework", "version": "v12.0.0"}]})
    (tmp_path / ".git").rmdir()
    result = repo_detect.detect_repo_mode(bare)
    assert result["framework_versions"] == {}
    assert result["framework_summary"] is None


def test_malformed_lock_file_is_skipped(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require": {"laravel/framework": "^12"}})
    (tmp_path / "composer.lock").write_text("{not json", encoding="utf-8")
    _write(tmp_path, "package-lock.json", ["unexpected", "shape"])
    result = repo_detect.detect_repo_mode(tmp_path)
    assert result["mode"] == "backend"
    assert result["framework_versions"] == {}


def test_versions_read_from_app_subdirectory(tmp_path):
    # The app lives in `<repo>/appbase/`; the git root has no manifest.
    _git(tmp_path)
    app = tmp_path / "appbase"
    (app / "app" / "Models").mkdir(parents=True)
    _write(app, "composer.json", {"require": {"php": "^8.4"}})
    _write(app, "composer.lock", {"packages": [{"name": "laravel/framework", "version": "v12.64.0"}]})
    for start in (app, app / "app" / "Models"):
        versions = repo_detect.detect_repo_mode(start)["framework_versions"]
        assert versions == {"php": "^8.4", "laravel/framework": "12.64.0"}
    # From the git root itself there is no manifest to read.
    assert repo_detect.detect_repo_mode(tmp_path)["framework_versions"] == {}


def test_npm_lockfile_v1_dependencies(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "package.json", {"dependencies": {"vue": "^2.7"}})
    _write(tmp_path, "package-lock.json", {
        "lockfileVersion": 1,
        "dependencies": {"vue": {"version": "2.7.16"}, "lodash": {"version": "4.17.21"}},
    })
    versions = repo_detect.detect_repo_mode(tmp_path)["framework_versions"]
    assert versions == {"vue": "2.7.16"}


def test_lock_file_with_invalid_bytes_is_skipped(tmp_path):
    _git(tmp_path)
    _write(tmp_path, "composer.json", {"require": {"php": "^8.3"}})
    (tmp_path / "composer.lock").write_bytes(b'{"packages": [\xff\xfe]}')
    versions = repo_detect.detect_repo_mode(tmp_path)["framework_versions"]
    assert versions == {"php": "^8.3"}
