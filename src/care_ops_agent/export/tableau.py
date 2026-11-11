"""Flat CSV extracts for Tableau Public.

A .hyper file is created inside Tableau Desktop (Extract, Create) from these
CSVs. This repo does not ship a Tableau binary, and it does not call Tableau
Public. Every column is a scalar so the extract does not need a JSON parse.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from care_ops_agent.nodes.triage import _rate


def _write(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return path
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def care_gap_weekly(results: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    grouped = results.groupby(["week", "partner_id", "clinic", "measure"], sort=True)
    for (week, partner_id, clinic, measure), sub in grouped:
        rate = _rate(sub)
        rows.append({
            "label": "SYNTHETIC",
            "week": int(week),
            "partner_id": partner_id,
            "clinic": clinic,
            "measure": measure,
            "visits": rate["visits"],
            "recorded": rate["recorded"],
            "met": rate["met"],
            "met_rate": round(rate["met_rate"], 4),
            "missing_share": round(rate["missing_share"], 4),
        })
    return rows


def pipeline_extract(ready: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in ready:
        gaps = row.get("open_gaps_by_measure") or {}
        if not gaps:
            gaps = {"": 0}
        for measure, count in gaps.items():
            rows.append({
                "label": "SYNTHETIC",
                "account_id": row["AccountId"],
                "stage": row["StageName"],
                "days_in_stage": row["days_in_stage"],
                "stalled": bool(row["stalled"]),
                "outreach_ready": bool(row["outreach_ready"]),
                "measure": measure,
                "open_gaps": int(count),
            })
    return rows


def pdsa_extract(cycles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cycle in cycles:
        rows.append({
            "label": "SYNTHETIC",
            "week": cycle["week"],
            "act": cycle["act"],
            "flag_count": cycle["flag_count"],
            "focus": cycle["focus"],
            "plan": cycle["plan"],
            "do": cycle["do"],
            "study": cycle["study"],
        })
    return rows


def budget_extract(burn: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "label": "SYNTHETIC",
            "week": row["week"],
            "role": row["role"],
            "hours": row["hours"],
            "cost": row["cost"],
            "cumulative_cost": row["cumulative_cost"],
        }
        for row in burn
    ]


def write_extracts(folder: Path, frames: dict[str, list[dict[str, Any]]]) -> list[Path]:
    paths = []
    for name, rows in frames.items():
        paths.append(_write(folder / f"{name}.csv", rows))
    return paths
