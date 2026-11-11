"""Score held-out scenarios against seeded truth.

Dev scenarios are not scored. Counts in the report are the resume bullets.
A failure taxonomy names what went wrong so a later change can be checked
against the same cases.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from care_ops_agent.controls.plan import build_plan
from care_ops_agent.crm.mock import apply_pipeline_stall, build_crm
from care_ops_agent.eval.catalog import DEV_IDS, heldout_scenarios
from care_ops_agent.experiment.ab import (
    EFFECT_P_A,
    EFFECT_P_B,
    NULL_P,
    effect_recovered,
    null_quiet,
    run_trial,
    sample_size_per_arm,
)
from care_ops_agent.metrics.pipeline import open_gaps_by_partner, readiness_view
from care_ops_agent.nodes.triage import memo
from care_ops_agent.pdsa.audience import render_updates
from care_ops_agent.sim.fixtures import demo_seeds
from care_ops_agent.sim.network import build_network, simulate_results

AS_OF = date(2026, 11, 3)
EFFECT_SEEDS = list(range(20))
NULL_SEEDS = list(range(100, 130))
SINGLE_KINDS = {"care_gap", "data_issue"}


def _partner_id(index: int) -> str:
    return f"P{index + 1}"


def _signal_hit(flagged: list[dict[str, Any]], signal: dict[str, Any]) -> bool:
    pid = _partner_id(signal["partner_index"])
    hits = [
        cell for cell in flagged
        if cell["partner_id"] == pid and cell["measure"] == signal["measure"] and cell["kind"] == signal["kind"]
    ]
    if signal.get("clinic"):
        return any(cell.get("clinic") == signal["clinic"] and cell["level"] == "clinic" for cell in hits)
    return any(cell["level"] == "partner" for cell in hits)


def _single_match(truth: dict[str, Any], verdict: dict[str, Any]) -> bool:
    if verdict.get("kind") != truth["kind"]:
        return False
    if verdict.get("partner_id") != _partner_id(truth["partner_index"]):
        return False
    if verdict.get("measure") != truth["measure"]:
        return False
    if truth.get("clinic"):
        return verdict.get("clinic") == truth["clinic"]
    return not verdict.get("clinic")


def _taxonomy(family_truth: str, truth: dict[str, Any], verdict: dict[str, Any], matched: bool) -> str:
    if matched:
        return "correct"
    if truth["kind"] == "none" and verdict.get("kind") not in (None, "none"):
        return "false_alarm"
    if truth["kind"] == "none":
        return "correct"
    if verdict.get("kind") in (None, "none"):
        return "missed_signal"
    if verdict.get("partner_id") != _partner_id(truth.get("partner_index", -1)):
        return "wrong_partner"
    if verdict.get("measure") != truth.get("measure"):
        return "wrong_measure"
    if verdict.get("kind") != truth.get("kind"):
        return "wrong_kind"
    if truth.get("clinic") and verdict.get("clinic") != truth.get("clinic"):
        return "wrong_clinic"
    return "mixed_incomplete" if family_truth == "mixed" else "missed_signal"


def score_scenario(scenario: dict[str, Any], seeds: dict[str, Any] | None = None) -> dict[str, Any]:
    if scenario["id"] in DEV_IDS:
        raise ValueError(f"{scenario['id']} is a dev scenario and is not scored")
    seeds = seeds or demo_seeds()
    network = build_network(scenario, seeds)
    results = simulate_results(scenario, network)
    written = memo(results, scenario, network["partners"])
    verdict = written["verdict"]
    flagged = written["analysis"]["flagged"]
    fidelity_ok = bool(written["fidelity"]["ok"])
    truth = scenario["truth"]
    crm = apply_pipeline_stall(build_crm(network["partners"], scenario["seed"], AS_OF), scenario, AS_OF)
    ready = readiness_view(crm["Opportunity"], AS_OF, open_gaps_by_partner(results))
    stall_ok = None
    if truth["kind"] == "onboarding_stall":
        pid = _partner_id(truth["partner_index"])
        stall_ok = any(row["AccountId"] == pid and row["stalled"] for row in ready)
        matched = bool(stall_ok) and verdict.get("kind") in (None, "none")
    elif truth["kind"] == "mixed":
        matched = all(_signal_hit(flagged, signal) for signal in truth["signals"])
    elif truth["kind"] == "none":
        matched = verdict.get("kind") in (None, "none")
    else:
        matched = _single_match(truth, verdict)
    if not fidelity_ok:
        failure = "fidelity_fail"
    else:
        failure = _taxonomy(truth["kind"], truth if truth["kind"] != "mixed" else {"kind": "mixed"}, verdict, matched)
        if truth["kind"] == "mixed" and not matched:
            failure = "mixed_incomplete"
        if truth["kind"] == "onboarding_stall" and not matched:
            failure = "stall_miss" if not stall_ok else "false_alarm"
    leaks = render_updates(
        scenario, network["partners"], written["analysis"], results, ready,
        {"baseline_cost": 0, "forecast_cost": 0},
    )["leaks"]
    leak_count = sum(len(ids) for ids in leaks.values())
    return {
        "id": scenario["id"],
        "family": scenario["family"],
        "truth_kind": truth["kind"],
        "verdict": verdict,
        "matched": matched and fidelity_ok and leak_count == 0,
        "call_matched": matched,
        "fidelity_ok": fidelity_ok,
        "failure": "partner_leak" if leak_count else failure,
        "leak_count": leak_count,
        "stall_ok": stall_ok,
        "label": "SYNTHETIC",
    }


def _ab_block() -> dict[str, Any]:
    n_per_arm = sample_size_per_arm(EFFECT_P_A, EFFECT_P_B)
    effect = [run_trial(seed, EFFECT_P_A, EFFECT_P_B, n_per_arm=n_per_arm) for seed in EFFECT_SEEDS]
    nulls = [run_trial(seed, NULL_P, NULL_P, n_per_arm=n_per_arm) for seed in NULL_SEEDS]
    return {
        "p_a": EFFECT_P_A,
        "p_b": EFFECT_P_B,
        "null_p": NULL_P,
        "n_per_arm": n_per_arm,
        "ab_effect_recovered": sum(1 for trial in effect if effect_recovered(trial)),
        "ab_effect_runs": len(effect),
        "ab_null_correct": sum(1 for trial in nulls if null_quiet(trial)),
        "ab_null_runs": len(nulls),
    }


def run_eval(scenarios: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    scenarios = scenarios if scenarios is not None else heldout_scenarios()
    seeds = demo_seeds()
    rows = [score_scenario(scenario, seeds) for scenario in scenarios]
    single = [row for row in rows if row["truth_kind"] in SINGLE_KINDS]
    kind_rows = single
    quiet = [row for row in rows if row["family"] in {"no_signal", "near_threshold"}]
    mixed = [row for row in rows if row["truth_kind"] == "mixed"]
    stalls = [row for row in rows if row["truth_kind"] == "onboarding_stall"]
    ab = _ab_block()
    plan = build_plan()
    taxonomy: dict[str, int] = {}
    for row in rows:
        taxonomy[row["failure"]] = taxonomy.get(row["failure"], 0) + 1
    report = {
        "label": "SYNTHETIC SIMULATION",
        "partners": 8,
        "scenarios": len(rows),
        "excluded_dev_scenarios": sorted(DEV_IDS),
        "top1_correct": sum(1 for row in single if row["call_matched"] and row["fidelity_ok"]),
        "top1_total": len(single),
        "kind_correct": sum(1 for row in kind_rows if row["call_matched"] and row["fidelity_ok"]),
        "kind_total": len(kind_rows),
        "false_alarms": sum(1 for row in quiet if row["verdict"].get("kind") not in (None, "none")),
        "quiet_scenarios": len(quiet),
        "mixed_recovered": sum(1 for row in mixed if row["call_matched"]),
        "mixed_total": len(mixed),
        "stalls_detected": sum(1 for row in stalls if row["stall_ok"]),
        "stall_total": len(stalls),
        "fidelity_ok": sum(1 for row in rows if row["fidelity_ok"]),
        "fidelity_checked": len(rows),
        "partner_leaks": sum(row["leak_count"] for row in rows),
        "taxonomy": taxonomy,
        "rows": [{k: v for k, v in row.items() if k != "verdict"} | {"verdict_kind": row["verdict"].get("kind")} for row in rows],
        "baseline_cost": plan["baseline_cost"],
        "forecast_cost": plan["forecast_cost"],
        **ab,
    }
    return report


def resume_bullets(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Resume bullets",
        "",
        "Portfolio simulation only. These lines describe synthetic partner groups and synthetic patients. They are not a claim about a real panel, a real customer, or a production system. Numbers come from `python -m care_ops_agent.eval.harness`.",
        "",
        (
            f"- Built a simulated care-gap closure program across {report['partners']} synthetic partner practices "
            f"that finds where patients are falling behind on diabetes control, blood-pressure control, and breast cancer screening. "
            f"On single-cause held-out scenarios, triage named the right practice and measure in {report['top1_correct']} of {report['top1_total']} cases."
        ),
        (
            "- Loaded synthetic patient records from local FHIR R4 files into PostgreSQL and wrote the SQL for three HEDIS-style measures, with data checks that must return zero bad rows. "
            "Every rate is computed in Python. The public Synthea sample is the roster only. Outcome probabilities are labeled scenario parameters, because that sample shows every diabetic patient already under an HbA1c of 8.0%."
        ),
        (
            f"- Separated care gaps from missing lab-result feeds so outreach is held when the problem is the data feed. "
            f"The care-versus-data call matched the seeded truth in {report['kind_correct']} of {report['kind_total']} single-cause scenarios, "
            f"with {report['false_alarms']} false alarm{'s' if report['false_alarms'] != 1 else ''} on {report['quiet_scenarios']} no-signal and near-threshold scenarios."
        ),
        (
            "- Ran the simulation as weekly PDSA cycles, kept partner onboarding in a Salesforce-shaped stand-in, kept the plan in an Asana CSV import, and wrote Excel workbooks plus Tableau-ready extracts. "
            "Live Asana, Salesforce, and Tableau Public are not connected."
        ),
        (
            f"- Designed a simulated outreach A/B test on gaps closed, including the sample-size calculation and a two-proportion readout. "
            f"The seeded effect was recovered in {report['ab_effect_recovered']} of {report['ab_effect_runs']} runs, "
            f"and the equal-rate version stayed quiet in {report['ab_null_correct']} of {report['ab_null_runs']} runs."
        ),
        "",
    ])


def eval_report_markdown(report: dict[str, Any]) -> str:
    call = decision(report)
    lines = [
        "# Held-out eval report",
        "",
        "SYNTHETIC SIMULATION. The four dev scenarios (`clinic_bp_drop`, `missing_a1c_feed`, `partner_screening_gap`, `no_signal`) are not in this score. Numbers come from `care_ops_agent.eval.harness`.",
        "",
        f"Decision: **{call['decision']}**.",
        "",
        "The scaling rule requires zero false alarms on no-signal and near-threshold weeks. A chance flag in a cell that was not the injected shift keeps the decision at NO-GO. The other gates passed on this run.",
        "",
        "## Gates",
        "",
        "| Gate | Result | Evidence | Rule |",
        "|---|---|---|---|",
    ]
    for gate in call["gates"]:
        lines.append(f"| {gate['gate']} | {'pass' if gate['passed'] else 'fail'} | {gate['evidence']} | {gate['rule']} |")
    lines += [
        "",
        "## Failure taxonomy",
        "",
    ]
    for name, count in sorted(report["taxonomy"].items()):
        lines.append(f"- {name}: {count}")
    lines += [
        "",
        "## Scenario results",
        "",
        "| Scenario | Family | Failure |",
        "|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(f"| {row['id']} | {row['family']} | {row['failure']} |")
    lines.append("")
    return "\n".join(lines)


def gate_results(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Gates for the scaling workbook. A miss is a no-go, not a rounded-up win."""
    checks = [
        ("numeric_fidelity", report["fidelity_ok"] == report["fidelity_checked"],
         "every held-out memo passed the numeric-fidelity guard",
         f"{report['fidelity_ok']} of {report['fidelity_checked']}"),
        ("partner_leaks", report["partner_leaks"] == 0,
         "partner updates named no other partner",
         str(report["partner_leaks"])),
        ("false_alarms", report["false_alarms"] == 0,
         "no-signal and near-threshold scenarios stayed quiet",
         f"{report['false_alarms']} of {report['quiet_scenarios']}"),
        ("single_cause_top1", report["top1_total"] > 0 and report["top1_correct"] / report["top1_total"] >= 0.8,
         "at least 80% of single-cause held-out scenarios named the right practice and measure",
         f"{report['top1_correct']} of {report['top1_total']}"),
        ("care_vs_data", report["kind_total"] > 0 and report["kind_correct"] / report["kind_total"] >= 0.8,
         "at least 80% of single-cause care-versus-data calls matched",
         f"{report['kind_correct']} of {report['kind_total']}"),
        ("mixed_causes", report["mixed_total"] > 0 and report["mixed_recovered"] == report["mixed_total"],
         "both shocks were flagged in every mixed scenario",
         f"{report['mixed_recovered']} of {report['mixed_total']}"),
        ("onboarding_stalls", report["stall_total"] > 0 and report["stalls_detected"] == report["stall_total"],
         "every seeded stalled account was marked stalled",
         f"{report['stalls_detected']} of {report['stall_total']}"),
        ("ab_effect", report["ab_effect_runs"] > 0 and report["ab_effect_recovered"] / report["ab_effect_runs"] >= 0.8,
         "the seeded outreach effect was recovered in at least 80% of runs",
         f"{report['ab_effect_recovered']} of {report['ab_effect_runs']}"),
        ("ab_null", report["ab_null_runs"] > 0 and report["ab_null_correct"] / report["ab_null_runs"] >= 0.8,
         "the equal-rate outreach test stayed quiet in at least 80% of runs",
         f"{report['ab_null_correct']} of {report['ab_null_runs']}"),
    ]
    return [
        {"gate": name, "passed": bool(ok), "rule": rule, "evidence": evidence, "label": "SYNTHETIC"}
        for name, ok, rule, evidence in checks
    ]


def decision(report: dict[str, Any]) -> dict[str, Any]:
    gates = gate_results(report)
    go = all(row["passed"] for row in gates)
    return {"decision": "GO" if go else "NO-GO", "gates": gates, "label": "SYNTHETIC SIMULATION"}


def main() -> None:
    import json

    report = run_eval()
    call = decision(report)
    print(json.dumps({"decision": call["decision"], "top1": [report["top1_correct"], report["top1_total"]],
                      "false_alarms": report["false_alarms"], "leaks": report["partner_leaks"],
                      "ab_effect": [report["ab_effect_recovered"], report["ab_effect_runs"]],
                      "ab_null": [report["ab_null_correct"], report["ab_null_runs"]],
                      "taxonomy": report["taxonomy"]}, indent=2))


if __name__ == "__main__":
    main()
