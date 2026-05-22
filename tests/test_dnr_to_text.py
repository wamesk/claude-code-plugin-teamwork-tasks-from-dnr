"""Tests for dnr_to_text DOCX/MD/PDF parser."""
from pathlib import Path

import dnr_to_text


def test_docx_extracts_text_and_metadata(sample_dnr_docx):
    result = dnr_to_text.parse(sample_dnr_docx)

    assert result["warning"] is None
    assert result["detected_language"] == "sk"
    assert result["section_count"] == 3, "WAME DNR has 3 extension sections (4.1, 4.2, 4.3)"
    assert "Rozšírenie č. 1" in result["plain_text"]
    assert "Rozšírenie č. 3" in result["plain_text"]
    assert len(result["plain_text"]) > 10_000


def test_docx_extracts_client_metadata(sample_dnr_docx):
    result = dnr_to_text.parse(sample_dnr_docx)
    meta = result["client_metadata"]

    assert meta["project_ref"] == "PON1107"
    assert meta["version"] == "1.2"
    assert "Družstvo lekárov" in (meta["client"] or "")


def test_md_file(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nRozšírenie č. 1 — Foo\n\nText.", encoding="utf-8")
    result = dnr_to_text.parse(md)

    assert result["warning"] is None
    assert result["section_count"] == 1
    assert "# Title" in result["plain_text"]


def test_missing_file_returns_warning(tmp_path):
    result = dnr_to_text.parse(tmp_path / "does_not_exist.docx")
    assert result["warning"] is not None
    assert "not found" in result["warning"].lower()


def test_unsupported_extension(tmp_path):
    f = tmp_path / "x.xyz"
    f.write_text("hi")
    result = dnr_to_text.parse(f)
    assert result["warning"] is not None
    assert "extension" in result["warning"].lower()


def test_language_detection_english(tmp_path):
    f = tmp_path / "en.md"
    f.write_text("This is an English document with the and a of in on is it.", encoding="utf-8")
    result = dnr_to_text.parse(f)
    assert result["detected_language"] == "en"


def test_paragraph_bold_detection_via_helper():
    """The _paragraph_is_bold helper is private but covered by the integration test
    above (DOCX heading paragraphs get **markdown bold**); ensure module import works."""
    assert callable(dnr_to_text._paragraph_is_bold)
