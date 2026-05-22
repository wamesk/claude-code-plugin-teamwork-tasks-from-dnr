"""Shared pytest fixtures and path setup."""
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "teamwork-tasks-from-dnr" / "scripts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "teamwork-tasks-from-dnr" / "prompts"

sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def expected_plan(fixtures_dir) -> dict:
    import json
    return json.loads((fixtures_dir / "expected_tasks.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def schema() -> dict:
    import json
    return json.loads((PROMPTS_DIR / "json_schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def sample_dnr_docx(fixtures_dir) -> Path:
    return fixtures_dir / "DNR_Strecnianska_v1.2.docx"
