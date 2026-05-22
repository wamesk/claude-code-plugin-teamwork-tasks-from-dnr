#!/usr/bin/env python3
"""
dnr_to_text — convert a DNR document (.docx / .pdf / .md / .txt) to plain text.

Stdlib only (zipfile + xml.etree for DOCX). Falls back to external `pandoc`
for DOCX if available (better formatting). For PDF, requires `pdftotext`
(poppler-utils) — no Python-only fallback by design (PDF parsers are heavy).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# OOXML namespaces used in .docx files.
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {"w": W_NS}

# Common stop words for language detection. Small lists keep stdlib-only.
LANG_STOPWORDS = {
    "sk": {"a", "ako", "ale", "alebo", "aj", "by", "do", "je", "na", "od", "pre",
           "po", "pri", "s", "so", "v", "vo", "z", "za", "že", "ktorý", "ktorá",
           "ktoré", "podľa", "sa", "si", "to", "tento", "tieto", "už"},
    "en": {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
           "has", "have", "in", "is", "it", "of", "on", "or", "that", "the",
           "this", "to", "was", "were", "will", "with"},
    "cs": {"a", "ale", "aby", "ano", "asi", "až", "bez", "by", "co", "do", "i",
           "je", "jsme", "jsi", "jak", "ke", "kdo", "který", "která", "které",
           "na", "od", "po", "pro", "se", "si", "to", "u", "už", "v", "ve", "z",
           "že"},
}

# Heading patterns for "extension" section detection.
# We accept matches anywhere — DNR text is flat after extraction so a heading
# may appear after other inline text from the same paragraph.
SECTION_PATTERNS = [
    # Slovak/Czech: "Rozšírenie č. 1 — Foo" / "Rozšírenie 1: Foo".
    # Must be followed by a separator (em-dash, colon, hyphen) to avoid matching
    # "Rozšírenie rozsahu" or other false positives.
    re.compile(r"Rozš[íi]renie\s*(?:č\.?)?\s*\d+\s*[—–\-:]", re.IGNORECASE),
    # English: "Extension 1 -", "Module 1:", "Feature 1 —"
    re.compile(r"\b(?:Extension|Module|Feature)\s+\d+\s*[—–\-:]", re.IGNORECASE),
    # Markdown/section refs: "4.1 Foo" at line start.
    re.compile(r"(?:^|\n)\s*\d+\.\d+\s+[A-ZÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ]"),
]


def parse(path: Path) -> dict:
    """Read a DNR file and return text + metadata."""
    if not path.exists():
        return _error(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext in (".md", ".txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
    elif ext == ".docx":
        text = _docx_to_text(path)
    elif ext == ".pdf":
        text = _pdf_to_text(path)
    else:
        return _error(f"Unsupported file extension: {ext}")

    if text.startswith("__ERROR__:"):
        return _error(text[len("__ERROR__:"):])

    return {
        "plain_text": text,
        "detected_language": _detect_language(text),
        "section_count": _count_sections(text),
        "client_metadata": _extract_client_metadata(text),
        "source_path": str(path),
        "warning": None,
    }


def _docx_to_text(path: Path) -> str:
    """Extract text from a .docx file.

    Strategy 1: pandoc (best formatting — preserves tables, lists).
    Strategy 2: stdlib zipfile + xml.etree (always available).
    """
    if shutil.which("pandoc"):
        try:
            result = subprocess.run(
                ["pandoc", str(path), "-t", "plain", "--wrap=none"],
                capture_output=True, text=True, timeout=30, check=True,
            )
            if result.stdout.strip():
                return result.stdout
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass  # fall through to stdlib

    return _docx_stdlib(path)


def _docx_stdlib(path: Path) -> str:
    """Extract paragraph text from word/document.xml inside a .docx zip."""
    try:
        with zipfile.ZipFile(path) as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
    except (zipfile.BadZipFile, KeyError) as e:
        return f"__ERROR__:Could not read DOCX: {e}"

    root = tree.getroot()
    paragraphs = []

    for p in root.iter(f"{{{W_NS}}}p"):
        runs = []
        for t in p.iter(f"{{{W_NS}}}t"):
            if t.text:
                runs.append(t.text)
        line = "".join(runs).rstrip()
        # Detect bold paragraphs (often headings). We add `**` markers so
        # downstream regex can match them.
        if line and _paragraph_is_bold(p):
            line = f"**{line}**"
        paragraphs.append(line)

    # Also extract table cell text. DNR uses tables for "Zásadné rozhodnutia".
    for tbl in root.iter(f"{{{W_NS}}}tbl"):
        for row in tbl.iter(f"{{{W_NS}}}tr"):
            cells = []
            for cell in row.iter(f"{{{W_NS}}}tc"):
                cell_text = []
                for t in cell.iter(f"{{{W_NS}}}t"):
                    if t.text:
                        cell_text.append(t.text)
                cells.append("".join(cell_text).strip())
            if any(cells):
                paragraphs.append(" | ".join(cells))

    return "\n".join(paragraphs)


def _paragraph_is_bold(p_element) -> bool:
    """Heuristic: paragraph is "bold" if all its runs have <w:b/> or no runs."""
    runs = list(p_element.iter(f"{{{W_NS}}}r"))
    if not runs:
        return False
    bold_runs = 0
    for r in runs:
        rpr = r.find(f"{{{W_NS}}}rPr")
        if rpr is not None and rpr.find(f"{{{W_NS}}}b") is not None:
            bold_runs += 1
    return bold_runs >= len(runs) // 2 + 1


def _pdf_to_text(path: Path) -> str:
    """Extract text from a .pdf using pdftotext (poppler-utils)."""
    if not shutil.which("pdftotext"):
        return ("__ERROR__:PDF support requires pdftotext from poppler-utils. "
                "Install via 'brew install poppler' (macOS) or 'apt install "
                "poppler-utils' (linux), or convert the PDF to DOCX/MD first.")

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True, timeout=60, check=True,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        return f"__ERROR__:pdftotext failed: {e}"


def _detect_language(text: str) -> str:
    """Pick the language whose stop-word set best matches the document."""
    words = re.findall(r"[a-záäčďéíľĺňóôŕšťúýžěščřžýáíé]{2,}", text.lower())
    if not words:
        return "en"
    counts = {lang: sum(1 for w in words if w in sw)
              for lang, sw in LANG_STOPWORDS.items()}
    best_lang, best_score = max(counts.items(), key=lambda kv: kv[1])
    # Require minimum signal; otherwise default to English.
    return best_lang if best_score >= 5 else "en"


def _count_sections(text: str) -> int:
    """Count extension/module/feature sections in the document.

    Returns the count from the first pattern with at least 1 match. Patterns
    are ordered most-specific first (extension/module/feature names), with
    generic numbered headings only as a fallback.
    """
    for pattern in SECTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            return len(matches)
    return 0


def _extract_client_metadata(text: str) -> dict:
    """Best-effort grep of header rows for client/project metadata.

    DNR header is a table with rows like 'Klient: ...', 'Referencia CP: ...'.
    We look in the first ~2000 chars.
    """
    head = text[:2000]
    metadata = {"client": None, "project_ref": None, "version": None, "title": None}

    patterns = {
        "client": [r"Klient[\s|:]*([^\n|]+?)(?:\n|\|)", r"Client[\s|:]*([^\n|]+?)(?:\n|\|)"],
        "project_ref": [r"Referencia\s*CP[\s|:]*([A-Z0-9-]+)", r"Reference[\s|:]*([A-Z0-9-]+)",
                        r"PON\d+", r"Project[\s|:]*([A-Z0-9-]+)"],
        "version": [r"Verzia[\s|:]*v?([0-9.]+)", r"Version[\s|:]*v?([0-9.]+)"],
    }

    for key, regex_list in patterns.items():
        for regex in regex_list:
            m = re.search(regex, head, re.IGNORECASE)
            if m:
                # Capture group 1 if present, otherwise full match.
                metadata[key] = (m.group(1) if m.groups() else m.group(0)).strip()
                break

    # Title = first non-empty line that's bold or starts with a word like
    # "Detailný návrh", "DNR", or matches the document header.
    for line in head.splitlines()[:30]:
        stripped = line.strip().strip("*").strip()
        if not stripped:
            continue
        if re.search(r"(detailný\s*návrh|DNR|specification|technical)", stripped, re.IGNORECASE):
            metadata["title"] = stripped
            break

    return metadata


def _error(message: str) -> dict:
    return {
        "plain_text": "",
        "detected_language": "en",
        "section_count": 0,
        "client_metadata": {},
        "source_path": None,
        "warning": message,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: dnr_to_text.py <path>", file=sys.stderr)
        sys.exit(2)
    import json
    out = parse(Path(sys.argv[1]).resolve())
    print(json.dumps(out, indent=2, ensure_ascii=False))
