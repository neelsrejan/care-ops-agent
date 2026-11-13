"""Partner pipeline metrics (Python only): stage counts, stage-to-stage conversion, aging, stalled partners."""

from __future__ import annotations

from datetime import date
from typing import Any

from care_ops_agent.crm.mock import STAGES

STALL_DAYS = 14


def stage_counts(opps: list[dict[str, Any]]) -> dict[str, int]:
    return {s: sum(1 for o in opps if o["StageName"] == s) for s in STAGES}


def conversion(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reached = {s: {h["OpportunityId"] for h in history if h["StageName"] == s} for s in STAGES}
    out = []
    for a, b in zip(STAGES, STAGES[1:]):
        n_a, n_b = len(reached[a]), len(reached[a] & reached[b])
        out.append({"from": a, "to": b, "reached_from": n_a, "advanced": n_b, "rate": (n_b / n_a) if n_a else None})
    return out


def aging(opps: list[dict[str, Any]], as_of: date) -> list[dict[str, Any]]:
    rows = []
    for o in opps:
        days = (as_of - date.fromisoformat(o["StageEnteredDate"])).days
        rows.append({"AccountId": o["AccountId"], "StageName": o["StageName"], "days_in_stage": days,
                     "stalled": o["StageName"] != "Live" and days > STALL_DAYS})
    return sorted(rows, key=lambda r: -r["days_in_stage"])


def open_gaps_by_partner(results) -> dict[str, dict[str, int]]:
    """Patients whose latest simulated result leaves the gap open, per partner and measure."""
    latest = results.sort_values("week").groupby("patient_key").tail(1)
    open_ = latest[latest["met"] != True]  # noqa: E712  (None = no result = open)
    out: dict[str, dict[str, int]] = {}
    for (pid, m), n in open_.groupby(["partner_id", "measure"]).size().items():
        out.setdefault(pid, {})[m] = int(n)
    return out


def readiness_view(opps, as_of: date, gaps: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    """Join pipeline stage with open care gaps: which partners can start outreach now?"""
    rows = []
    for a in aging(opps, as_of):
        g = gaps.get(a["AccountId"], {})
        total = sum(g.values())
        ready = a["StageName"] in ("Data Onboarding", "Live")
        rows.append(a | {"open_gaps": total, "open_gaps_by_measure": g, "outreach_ready": ready})
    return sorted(rows, key=lambda r: (not r["outreach_ready"], -r["open_gaps"]))
