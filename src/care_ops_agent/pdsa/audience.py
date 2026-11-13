"""Three views of the same week: partner, internal, steering.

The matrix is the permissions spec. The renderer includes a section only when
the audience is allowed to see it, and a leak check scans partner text for
every other partner id.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from care_ops_agent.llm import narrate
from care_ops_agent.nodes.triage import _rate

# What each audience may see. Partner text is one partner at a time.
AUDIENCES = {
    "partner": {"other_partners": False, "own_patients": True, "patient_keys_all": False, "budget": False, "pipeline_all": False},
    "internal": {"other_partners": True, "own_patients": True, "patient_keys_all": True, "budget": True, "pipeline_all": True},
    "steering": {"other_partners": True, "own_patients": False, "patient_keys_all": False, "budget": True, "pipeline_all": False},
}


def permissions_markdown() -> str:
    lines = [
        "# Permissions spec (SIMULATION)",
        "",
        "The same weekly packet is rendered three ways. The filter runs before the text is written. A partner packet that names another partner is a failed run, not a disclaimer.",
        "",
        "| Field | Partner (own group only) | Internal | Steering |",
        "|---|---|---|---|",
        "| Own care-gap rates | yes | yes | yes, as part of the network story |",
        "| Other partners' names, ids, or rates | no | yes | yes, flagged partners only |",
        "| Patient keys | own panel only | yes | no |",
        "| Pipeline stage | own stage | every account | stalled count only |",
        "| Budget dollars | no | yes | yes, the rollup |",
        "",
        "Live Salesforce sharing rules are not configured. This table is the stand-in until an org exists.",
        "",
    ]
    return "\n".join(lines)


def _pct(value: float) -> float:
    return round(100 * value, 1)


def network_rates(results: pd.DataFrame, start_week: int) -> dict[str, dict[str, Any]]:
    recent = results[results["week"] >= start_week]
    out = {}
    for measure, sub in recent.groupby("measure"):
        rate = _rate(sub)
        out[str(measure)] = {"met_pct": _pct(rate["met_rate"]), "visits": rate["visits"], "missing_pct": _pct(rate["missing_share"])}
    return out


def leak_findings(text: str, partner_id: str, partners: list[dict[str, Any]]) -> list[str]:
    found = []
    for partner in partners:
        other = partner["partner_id"]
        if other == partner_id:
            continue
        if other in text or partner["name"] in text:
            found.append(other)
    return found


def _stall_count(ready: list[dict[str, Any]]) -> int:
    return sum(1 for row in ready if row["stalled"])


def render_updates(
    scenario: dict[str, Any],
    partners: list[dict[str, Any]],
    analysis: dict[str, Any],
    results: pd.DataFrame,
    ready: list[dict[str, Any]],
    budget: dict[str, int],
) -> dict[str, Any]:
    names = {p["partner_id"]: p["name"] for p in partners}
    rates = network_rates(results, scenario["program_start_week"])
    flagged = analysis["flagged"]
    facts_base: dict[str, Any] = {
        "scenario": scenario["id"],
        "flag_count": len(flagged),
        "stalled_accounts": _stall_count(ready),
        "baseline_budget": budget["baseline_cost"],
        "forecast_budget": budget["forecast_cost"],
        "threshold_pts": 10,
    }
    for measure, rate in rates.items():
        facts_base[f"{measure}_pct"] = rate["met_pct"]
        facts_base[f"{measure}_visits"] = rate["visits"]
    for cell in flagged:
        facts_base[cell["partner_id"]] = cell["partner_id"]
        facts_base[names[cell["partner_id"]]] = names[cell["partner_id"]]

    steering_lines = [
        "# Steering update (SYNTHETIC SIMULATION)",
        f"Flagged cells: {facts_base['flag_count']}. Stalled onboarding accounts: {facts_base['stalled_accounts']}.",
        f"Forecast budget USD {facts_base['forecast_budget']} against a baseline of USD {facts_base['baseline_budget']}.",
    ]
    for measure, rate in rates.items():
        steering_lines.append(f"{measure} met rate {rate['met_pct']}% on {rate['visits']} recent visits.")
    if flagged:
        steering_lines.append("Flagged: " + ", ".join(
            f"{c['partner_id']} {c['measure']} {c['kind']}" for c in flagged[:6]
        ) + ".")
    else:
        steering_lines.append("No cell cleared the flag rule this window.")
    steering = narrate("\n".join(steering_lines), facts_base)

    internal_lines = steering_lines + [
        "Internal view includes every flagged partner and the budget rollup above.",
        "Patient keys stay in the working files and are not repeated in this short note.",
    ]
    internal = narrate("\n".join(internal_lines).replace("Steering update", "Internal update"), facts_base)

    partner_packets = {}
    leaks: dict[str, list[str]] = {}
    for partner in partners:
        pid = partner["partner_id"]
        own = [c for c in flagged if c["partner_id"] == pid]
        own_ready = next((row for row in ready if row["AccountId"] == pid), None)
        pfacts: dict[str, Any] = {
            "scenario": scenario["id"],
            "partner_id": pid,
            "partner_name": partner["name"],
            "own_flags": len(own),
            "threshold_pts": 10,
        }
        if own_ready:
            pfacts["days_in_stage"] = own_ready["days_in_stage"]
            pfacts["stage"] = own_ready["StageName"]
        lines = [
            f"# Partner update — {pid} (SYNTHETIC SIMULATION)",
            f"{partner['name']} has {len(own)} flagged cells under the {pfacts['threshold_pts']} point rule.",
        ]
        if own_ready:
            lines.append(f"Your onboarding stage is {own_ready['StageName']}, {own_ready['days_in_stage']} days in stage.")
        if any(c["kind"] == "data_issue" for c in own):
            lines.append("At least one flag is a data issue. Outreach for that measure stays on hold until the feed check closes.")
        elif own:
            lines.append("Flags read as care gaps. Outreach for your panel is the current action.")
        else:
            lines.append("Nothing on your panel cleared the flag rule this window.")
        text = "\n".join(lines)
        written = narrate(text, pfacts)
        partner_packets[pid] = written
        leaks[pid] = leak_findings(written["text"], pid, partners)

    return {
        "steering": steering,
        "internal": internal,
        "partners": partner_packets,
        "leaks": leaks,
        "network_rates": rates,
        "audiences": AUDIENCES,
    }
