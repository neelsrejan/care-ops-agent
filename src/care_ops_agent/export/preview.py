"""A local HTML table preview of the extracts.

This is not the Tableau Public dashboard. It lets a reviewer see the same
rows without a Tableau account.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _table(title: str, rows: list[dict[str, Any]], limit: int = 12) -> str:
    if not rows:
        return f"<h2>{escape(title)}</h2><p>No rows.</p>"
    cols = list(rows[0])
    head = "".join(f"<th>{escape(str(col))}</th>" for col in cols)
    body = []
    for row in rows[:limit]:
        body.append("<tr>" + "".join(f"<td>{escape(str(row[col]))}</td>" for col in cols) + "</tr>")
    more = "" if len(rows) <= limit else f"<p>Showing {limit} of {len(rows)} rows.</p>"
    return f"<h2>{escape(title)}</h2>{more}<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def write_preview(path: Path, sections: list[tuple[str, list[dict[str, Any]]]]) -> Path:
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<title>Care-gap extracts (SYNTHETIC)</title>",
        "<style>body{font-family:Georgia,serif;margin:2rem;color:#14232b;background:#f3efe6}",
        "table{border-collapse:collapse;width:100%;background:#fffdf8;margin-bottom:1.5rem}",
        "th,td{border:1px solid #e3d9cc;padding:6px 8px;font-size:14px;text-align:left}",
        "th{background:#0b3a5b;color:#fff} .banner{color:#8c2f3b;font-weight:bold}</style></head><body>",
        "<p class='banner'>SYNTHETIC SIMULATION. Local preview only. Not a Tableau Public dashboard.</p>",
        "<h1>Harbor Health Plan care-gap extracts</h1>",
    ]
    for title, rows in sections:
        parts.append(_table(title, rows))
    parts.append("</body></html>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(parts))
    return path
