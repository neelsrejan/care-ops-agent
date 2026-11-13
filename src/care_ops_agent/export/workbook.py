"""Excel workbook via openpyxl (stand-in for the deck; opens in Excel/Google Sheets). Values only from Python metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HDR = Font(bold=True)
BANNER = "SYNTHETIC SIMULATION — not real partners, patients or contracts"


def _sheet(wb, title: str, rows: list[dict[str, Any]]):
    ws = wb.create_sheet(title)
    ws.append([BANNER])
    ws["A1"].font = Font(bold=True, color="C00000")
    if not rows:
        return ws
    cols = list(rows[0])
    ws.append(cols)
    for c in ws[2]:
        c.font = HDR
        c.fill = PatternFill("solid", fgColor="DDEBF7")
    for r in rows:
        ws.append([str(v) if isinstance(v, (dict, list)) else v for v in r.values()])
    for col in ws.columns:
        ws.column_dimensions[col[1].column_letter].width = max(12, min(48, max(len(str(c.value or "")) for c in col[1:]) + 2))
    return ws


def write_pipeline_workbook(path: Path, sheets: dict[str, list[dict[str, Any]]]) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    for title, rows in sheets.items():
        _sheet(wb, title[:31], rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
