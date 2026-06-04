#!/usr/bin/env python3
"""
json_to_xlsx — minimal stdlib-only XLSX writer for Teamwork.com task import.

Produces an OOXML SpreadsheetML 2007+ file with the 10-column Teamwork import
schema: TASKLIST, TASK, DESCRIPTION, ASSIGN TO, START DATE, DUE DATE, PRIORITY,
ESTIMATED TIME, TAGS, STATUS.

Uses only `zipfile`, `xml.etree.ElementTree`, and `xml.sax.saxutils.escape`.
No `openpyxl`, no `pandas`. Works in any Python 3.7+ environment.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from description_summary import append_summary_to_description

HEADER = ["TASKLIST", "TASK", "DESCRIPTION", "ASSIGN TO", "START DATE",
          "DUE DATE", "PRIORITY", "ESTIMATED TIME", "TAGS", "STATUS"]

DEFAULT_LAYOUT = {
    "header_fill": "1F4E79",
    "tasklist_fill": "D9E2F3",
    "column_widths": {
        "tasklist": 40, "task": 60, "description": 110, "assign_to": 20,
        "start_date": 14, "due_date": 14, "priority": 10,
        "estimated_time": 14, "tags": 14, "status": 14,
    },
}


def write(plan: dict, output_path: Path, layout: dict | None = None,
          include_tags: bool = False, default_status: str = "Active") -> Path:
    """Render a plan JSON to an XLSX file at output_path.

    The plan must follow `prompts/json_schema.json`. include_tags controls
    whether the TAGS column gets populated (default False per user pref).
    """
    layout = {**DEFAULT_LAYOUT, **(layout or {})}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = _build_rows(plan, include_tags=include_tags, default_status=default_status)
    strings = _collect_strings(rows)
    workbook = _Workbook(rows, strings, layout)
    workbook.save(output_path)
    return output_path


def _build_rows(plan: dict, include_tags: bool, default_status: str) -> list[dict]:
    """Build a list of row dicts in the order they appear in the sheet.

    Each row has:
        kind: 'header' | 'tasklist' | 'task'
        cells: list of 10 cell values (None for empty)
    """
    rows = [{"kind": "header", "cells": list(HEADER)}]

    language = (plan.get("metadata", {}).get("language") or "sk").lower()
    for tl in plan.get("tasklists", []):
        tl_cells = [None] * 10
        tl_cells[0] = tl.get("name", "")
        tl_cells[2] = append_summary_to_description(tl, language=language)
        tl_cells[9] = default_status
        rows.append({"kind": "tasklist", "cells": tl_cells})

        for task in tl.get("tasks", []):
            cells = [None] * 10
            cells[1] = task.get("name", "")
            cells[2] = _render_task_description(task)
            if task.get("assign_to"):
                cells[3] = str(task["assign_to"])
            cells[6] = task.get("priority", "")
            cells[7] = int(task.get("estimated_minutes", 0))
            if include_tags and task.get("tags"):
                cells[8] = ",".join(task["tags"])
            cells[9] = default_status
            rows.append({"kind": "task", "cells": cells})

    return rows


def _render_task_description(task: dict) -> str:
    """Compose the DESCRIPTION cell from acceptance + deps + goal + tech plan."""
    parts = ["## Akceptačné kritériá"]
    for crit in task.get("acceptance_criteria", []):
        parts.append(f"- [ ] {crit}")

    deps = task.get("dependencies") or []
    if deps:
        parts.append("")
        parts.append("### Závislosť")
        for d in deps:
            parts.append(f"- {d}")

    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Cieľ")
    parts.append(task.get("goal", "").strip())
    parts.append("")
    parts.append("## Technický popis")
    parts.append(task.get("technical_plan", "").rstrip())

    return "\n".join(parts)


def _collect_strings(rows: list[dict]) -> dict:
    """Build a shared-strings index from all string cell values."""
    index = {}
    for row in rows:
        for cell in row["cells"]:
            if isinstance(cell, str) and cell not in index:
                index[cell] = len(index)
    return index


# ---------------------------------------------------------------------------
# OOXML writer
# ---------------------------------------------------------------------------


class _Workbook:
    """Builds and writes a minimal OOXML workbook."""

    def __init__(self, rows: list[dict], strings: dict, layout: dict):
        self.rows = rows
        self.strings = strings
        self.layout = layout

    def save(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", self._content_types())
            z.writestr("_rels/.rels", self._root_rels())
            z.writestr("xl/_rels/workbook.xml.rels", self._workbook_rels())
            z.writestr("xl/workbook.xml", self._workbook())
            z.writestr("xl/styles.xml", self._styles())
            z.writestr("xl/sharedStrings.xml", self._shared_strings())
            z.writestr("xl/worksheets/sheet1.xml", self._sheet())

    # ------ part builders ------

    def _content_types(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '</Types>'
        )

    def _root_rels(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

    def _workbook_rels(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
            '</Relationships>'
        )

    def _workbook(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Tasks" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )

    def _styles(self) -> str:
        """Define 4 styles:
        0 — default (no fill, no font)
        1 — header (bold white text, dark-blue fill, centered)
        2 — tasklist row (bold, light-blue fill, wrap text)
        3 — task body (wrap text, vertical-top)
        """
        header_fill = self.layout["header_fill"]
        tasklist_fill = self.layout["tasklist_fill"]
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF{header_fill}"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF{tasklist_fill}"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FF999999"/></left>
      <right style="thin"><color rgb="FF999999"/></right>
      <top style="thin"><color rgb="FF999999"/></top>
      <bottom style="thin"><color rgb="FF999999"/></bottom>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="4">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

    def _shared_strings(self) -> str:
        count = len(self.strings)
        items = []
        # Preserve insertion order: build inverse map first.
        ordered = sorted(self.strings.items(), key=lambda kv: kv[1])
        for s, _idx in ordered:
            # Preserve whitespace and newlines.
            items.append(f'<si><t xml:space="preserve">{escape(s)}</t></si>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'count="{count}" uniqueCount="{count}">'
            + "".join(items) +
            '</sst>'
        )

    def _sheet(self) -> str:
        widths = self.layout["column_widths"]
        cols_xml = self._cols_xml([
            widths["tasklist"], widths["task"], widths["description"],
            widths["assign_to"], widths["start_date"], widths["due_date"],
            widths["priority"], widths["estimated_time"], widths["tags"],
            widths["status"],
        ])

        out = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
            cols_xml,
            '<sheetData>',
        ]

        for r_idx, row in enumerate(self.rows, start=1):
            kind = row["kind"]
            cells_xml = []
            for c_idx, value in enumerate(row["cells"], start=1):
                if value is None or value == "":
                    continue
                ref = f"{_col_letter(c_idx)}{r_idx}"
                style_id = self._cell_style_for(kind, c_idx)
                if isinstance(value, str):
                    s_idx = self.strings[value]
                    cells_xml.append(f'<c r="{ref}" s="{style_id}" t="s"><v>{s_idx}</v></c>')
                elif isinstance(value, (int, float)):
                    cells_xml.append(f'<c r="{ref}" s="{style_id}"><v>{value}</v></c>')

            # Auto-size row heights for description-heavy rows.
            ht_attr = ""
            if kind in ("tasklist", "task"):
                desc = row["cells"][2]
                if isinstance(desc, str):
                    lines = max(1, desc.count("\n") + 1)
                    if lines > 4:
                        ht = min(15 * lines, 409)
                        ht_attr = f' ht="{ht}" customHeight="1"'

            out.append(f'<row r="{r_idx}"{ht_attr}>' + "".join(cells_xml) + '</row>')

        out.append('</sheetData>')
        out.append('</worksheet>')
        return "".join(out)

    def _cols_xml(self, widths: list[float]) -> str:
        cols = ['<cols>']
        for i, w in enumerate(widths, start=1):
            cols.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
        cols.append('</cols>')
        return "".join(cols)

    def _cell_style_for(self, kind: str, col_idx: int) -> int:
        if kind == "header":
            return 1
        if kind == "tasklist":
            return 2
        return 3  # task body


def _col_letter(idx: int) -> str:
    """1 -> 'A', 26 -> 'Z', 27 -> 'AA'."""
    letters = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True, help="Path to plan JSON file")
    p.add_argument("--out", required=True, help="Output .xlsx path")
    p.add_argument("--include-tags", action="store_true")
    p.add_argument("--default-status", default="Active")
    args = p.parse_args()

    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    output = write(plan, Path(args.out), include_tags=args.include_tags,
                   default_status=args.default_status)
    print(f"Wrote: {output}")
