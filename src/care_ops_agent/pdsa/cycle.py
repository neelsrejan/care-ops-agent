"""One PDSA row per program week.

Plan names the cells triage flagged. Do is outreach, a feed check, or
monitoring. Study records the rates the code just computed. Act is adopt,
adapt, or abandon. Prose goes through the numeric-fidelity guard.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from care_ops_agent.llm import narrate
from care_ops_agent.nodes.triage import analyze

_KIND_RANK = {"data_issue": 0, "care_gap": 1}


def _keys(flagged: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    return {(c["partner_id"], c.get("clinic") or "", c["measure"]) for c in flagged if c["level"] == "clinic" or c["level"] == "partner"}


def _focus_line(cell: dict[str, Any]) -> str:
    where = cell["partner_id"]
    if cell["level"] == "clinic":
        where += f" clinic {cell['clinic']}"
    return f"{where} {cell['measure']} ({cell['kind']})"


def run_pdsa(scenario: dict[str, Any], results: pd.DataFrame) -> list[dict[str, Any]]:
    start = int(scenario["program_start_week"])
    open_focus: set[tuple[str, str, str]] = set()
    cycles = []
    for week in range(start, int(scenario["weeks"]) + 1):
        window = results[results["week"] <= week]
        res = analyze(window, start)
        flagged = res["flagged"]
        current = _keys(flagged)
        cleared = open_focus - current
        kinds = {c["kind"] for c in flagged}
        if "data_issue" in kinds:
            act = "adapt"
            action = "Hold outreach on data-issue cells and open a feed check."
        elif flagged:
            act = "adopt"
            action = "Keep outreach on the flagged care-gap cells."
        elif cleared:
            act = "abandon"
            action = "The earlier special cause has left the flag list. Stop the extra outreach and return to monitoring."
        else:
            act = "adopt"
            action = "No cell is over the flag rule. Keep the weekly monitor."
        focus = ", ".join(_focus_line(c) for c in flagged[:4]) or "none"
        facts: dict[str, Any] = {
            "week": week,
            "flag_count": len(flagged),
            "cleared_count": len(cleared),
            "threshold_pts": 10,
            "scenario": scenario["id"],
        }
        for index, cell in enumerate(flagged[:4]):
            facts[f"p{index}"] = cell["partner_id"]
            facts[f"drop_pts_{index}"] = round(100 * cell["drop"], 1)
        text = "\n".join([
            f"# PDSA week {week} ({scenario['id']}) — SYNTHETIC SIMULATION",
            f"Plan: review {facts['flag_count']} flagged cells against the {facts['threshold_pts']} point rule. Focus: {focus}.",
            f"Do: {action}",
            f"Study: flag count {facts['flag_count']}; cells cleared since last week {facts['cleared_count']}.",
            f"Act: {act}.",
        ])
        written = narrate(text, facts)
        cycles.append({
            "week": week,
            "plan": f"Review flagged cells. Focus: {focus}.",
            "do": action,
            "study": f"Flags {len(flagged)}. Cleared since last week {len(cleared)}.",
            "act": act,
            "flag_count": len(flagged),
            "kinds": sorted(kinds, key=lambda kind: _KIND_RANK.get(kind, 9)),
            "focus": focus,
            "memo": written["text"],
            "fidelity_ok": written["fidelity"]["ok"],
            "label": "SYNTHETIC",
        })
        open_focus = current
    if any(not row["fidelity_ok"] for row in cycles):
        raise RuntimeError("PDSA memo failed the numeric-fidelity guard")
    return cycles
