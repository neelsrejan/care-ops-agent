"""Care-gap triage: where are patients falling behind, and is it care or data?

All numbers come from Python (Wilson CIs, p-chart, two-period comparison). The memo
template is filled from those facts and passes the numeric-fidelity guard before any
LLM rewrite.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from care_ops_agent.llm import narrate
from care_ops_agent.metrics.rates import wilson_interval
from care_ops_agent.metrics.spc import western_electric, control_limits

MIN_DROP = 0.10           # flag a cell when recent met rate falls >= 10 points below baseline
MISSING_FLAG = 0.20
ALPHA = 0.05              # family-wise false-alarm rate across all cells       # recent share of visits with no recorded result that marks a data issue


def _rate(sub: pd.DataFrame) -> dict[str, Any]:
    recorded = sub[sub["result_recorded"]]
    n_visits, n = len(sub), len(recorded)
    k = int(recorded["met"].sum()) if n else 0
    # HEDIS-style: a visit with no recorded result leaves the gap open (counts as not met)
    n_all = n_visits
    lo, hi = wilson_interval(k, n_all) if n_all else (0.0, 0.0)
    return {"visits": n_visits, "recorded": n, "met": k, "met_rate": (k / n_all) if n_all else 0.0,
            "met_rate_recorded": (k / n) if n else None, "missing_share": (1 - n / n_visits) if n_visits else 0.0,
            "ci_low": lo, "ci_high": hi}


def two_prop_p(b: dict[str, Any], r: dict[str, Any]) -> float:
    """One-sided p-value that the recent met rate is lower than baseline."""
    from math import sqrt

    from scipy.stats import norm

    n1, n2 = b["visits"], r["visits"]
    if not n1 or not n2:
        return 1.0
    p1, p2 = b["met"] / n1, r["met"] / n2
    pool = (b["met"] + r["met"]) / (n1 + n2)
    se = sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    return 1.0 if se == 0 else float(norm.sf((p1 - p2) / se))


def weekly_pchart(df: pd.DataFrame) -> dict[str, Any]:
    """p-chart on weekly GAP share (not met); rule hits mean a real shift."""
    pts = []
    for week, sub in df.groupby("week"):
        n = len(sub)
        gaps = int((sub["met"] != True).sum())  # noqa: E712  None (no result) = gap open
        pts.append({"week": int(week), "n": n, "gaps": gaps, "p": gaps / n})
    p_bar = sum(p["gaps"] for p in pts) / sum(p["n"] for p in pts)
    for p in pts:
        lcl, ucl, se = control_limits(p_bar, p["n"])
        p.update(lcl=lcl, ucl=ucl, z=(p["p"] - p_bar) / se if se else 0.0)
    return {"p_bar": p_bar, "points": pts, "violations": western_electric([p["z"] for p in pts])}


def analyze(df: pd.DataFrame, program_start_week: int) -> dict[str, Any]:
    base, recent = df[df["week"] < program_start_week], df[df["week"] >= program_start_week]
    cells = []
    for keys, level in ((["partner_id", "measure"], "partner"), (["partner_id", "clinic", "measure"], "clinic")):
        for key, sub_recent in recent.groupby(keys):
            key = key if isinstance(key, tuple) else (key,)
            mask = (base[keys] == pd.Series(key, index=keys)).all(axis=1)
            b, r = _rate(base[mask]), _rate(sub_recent)
            cell = dict(zip(keys, key)) | {"level": level, "baseline": b, "recent": r,
                                           "drop": b["met_rate"] - r["met_rate"],
                                           "missing_jump": r["missing_share"] - b["missing_share"]}
            whole = df[(df[keys] == pd.Series(key, index=keys)).all(axis=1)]
            cell["pchart_rule_hits"] = len(weekly_pchart(whole)["violations"])
            cells.append(cell)
    # Many partner/clinic/measure cells are tested at once, so use a Bonferroni-adjusted
    # one-sided two-proportion z-test to keep false alarms down (no_signal scenario).
    per_level = {lvl: sum(1 for c in cells if c["level"] == lvl) for lvl in ("partner", "clinic")}
    for c in cells:
        c["p_value"] = two_prop_p(c["baseline"], c["recent"])
        c["alpha"] = ALPHA / max(1, per_level[c["level"]])
    flagged = [c for c in cells if c["drop"] >= MIN_DROP and c["p_value"] < c["alpha"]]
    for c in flagged:
        c["kind"] = "data_issue" if c["recent"]["missing_share"] >= MISSING_FLAG and c["missing_jump"] >= MISSING_FLAG else "care_gap"
    # Prefer the most specific cell: a clinic flag explains its partner flag only if the other clinics are fine.
    ranked = sorted(flagged, key=lambda c: (-c["drop"], c["level"] != "clinic"))
    top = ranked[0] if ranked else None
    if top and top["level"] == "clinic":
        siblings = [c for c in flagged if c["level"] == "clinic" and c["partner_id"] == top["partner_id"]
                    and c["measure"] == top["measure"] and c["clinic"] != top["clinic"]]
        if len(siblings) >= 1:  # two+ clinics down = partner-wide
            partner_cell = next(c for c in res_cells(cells) if c["level"] == "partner" and c["partner_id"] == top["partner_id"] and c["measure"] == top["measure"])
            partner_cell["kind"] = top["kind"]
            top = partner_cell
    return {"cells": cells, "flagged": ranked, "top": top}


def res_cells(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return cells


def _pct(x: float) -> float:
    return round(100 * x, 1)


def memo(df: pd.DataFrame, scenario: dict[str, Any], partners: list[dict[str, Any]]) -> dict[str, Any]:
    res = analyze(df, scenario["program_start_week"])
    names = {p["partner_id"]: p["name"] for p in partners}
    top = res["top"]
    facts: dict[str, Any] = {"scenario": scenario["id"], "flag_count": len(res["flagged"]),
                             "confidence_pct": 95, "threshold_pts": round(MIN_DROP * 100)}
    lines = [f"# Care-gap triage memo — {scenario['id']} (SYNTHETIC SIMULATION)", ""]
    if top is None:
        lines.append(f"No partner or clinic shows a care-gap drop of 10+ points beyond its interval. Flags: {len(res['flagged'])}. Recommendation: stay the course; keep weekly monitoring.")
        verdict = {"kind": "none"}
    else:
        b, r = top["baseline"], top["recent"]
        where = f"{top['partner_id']} ({names[top['partner_id']]})" + (f", clinic {top['clinic']}" if top["level"] == "clinic" else "")
        facts |= {"where": where, "measure": top["measure"], "base_pct": _pct(b["met_rate"]), "recent_pct": _pct(r["met_rate"]),
                  "ci_lo_pct": _pct(r["ci_low"]), "ci_hi_pct": _pct(r["ci_high"]), "visits": r["visits"],
                  "missing_pct": _pct(r["missing_share"]), "rule_hits": top["pchart_rule_hits"]}
        lines += [f"**Top signal:** {where}, {top['measure']}.",
                  f"Met rate fell from {facts['base_pct']}% to {facts['recent_pct']}% (95% CI {facts['ci_lo_pct']}–{facts['ci_hi_pct']}%, {r['visits']} visits). Control-chart rule hits: {facts['rule_hits']}.",
                  f"Visits with no recorded result: {facts['missing_pct']}%."]
        if top["kind"] == "data_issue":
            lines.append("**Read:** likely a DATA issue (results not arriving), not missed care. Action: check the partner's lab/result feed before any patient outreach.")
        else:
            lines.append("**Read:** likely a real CARE gap. Action: target outreach and partner support here first; review in the next weekly PDSA cycle.")
        verdict = {"kind": top["kind"], "partner_id": top["partner_id"], "clinic": top.get("clinic"), "measure": top["measure"]}
    text = "\n".join(lines)
    out = narrate(text, facts)
    return {"memo": out["text"], "facts": facts, "verdict": verdict, "fidelity": out["fidelity"], "analysis": res}
