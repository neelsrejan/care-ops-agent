"""Build the S5–S10 artifacts without PostgreSQL or a live account.

    python -m care_ops_agent.run_program
    python -m care_ops_agent.run_program --eval

The demo roster is the committed fixture, not the 1.5 GB download. Outcome
rates still come from the scenario parameters. ``--eval`` reruns the held-out
set and writes the resume bullets from that run.
"""

from __future__ import annotations

import argparse
import json
from datetime import date

from care_ops_agent.config import load_settings
from care_ops_agent.controls.plan import build_plan, dated_rows
from care_ops_agent.crm.client import salesforce_client_from_env
from care_ops_agent.crm.mock import apply_pipeline_stall, build_crm
from care_ops_agent.eval.catalog import materialize_yaml
from care_ops_agent.eval.harness import decision, resume_bullets, run_eval
from care_ops_agent.experiment.ab import (
    EFFECT_P_A,
    EFFECT_P_B,
    pdsa_from_trial,
    run_trial,
    sample_size_per_arm,
)
from care_ops_agent.export.mspdi import write_project_xml
from care_ops_agent.export.preview import write_preview
from care_ops_agent.export.tableau import (
    budget_extract,
    care_gap_weekly,
    pdsa_extract,
    pipeline_extract,
    write_extracts,
)
from care_ops_agent.export.workbook import write_pipeline_workbook
from care_ops_agent.metrics.pipeline import open_gaps_by_partner, readiness_view
from care_ops_agent.nodes.triage import analyze
from care_ops_agent.pdsa.audience import permissions_markdown, render_updates
from care_ops_agent.pdsa.cycle import run_pdsa
from care_ops_agent.pm.asana import asana_client_from_env
from care_ops_agent.rfp.library import answer_all, load_bank, tracker
from care_ops_agent.sim.fixtures import demo_seeds
from care_ops_agent.sim.network import build_network, load_scenario, simulate_results

AS_OF = date(2026, 11, 3)


def _controls_sheets(plan: dict) -> dict[str, list]:
    return {
        "Charter": plan["charter"],
        "WBS": dated_rows(plan["wbs"]),
        "RAID": plan["raid"],
        "Change log": plan["changes"],
        "Budget burn": plan["burn"],
        "Capacity": plan["capacity"],
        "Swimlane": plan["swimlane"],
    }


def run(eval_report: bool = False) -> dict:
    settings = load_settings()
    out = settings.out_dir
    root = settings.repo_root
    plan = build_plan()
    write_pipeline_workbook(out / "program_controls.xlsx", _controls_sheets(plan))
    write_project_xml(plan, out / "harbor_care_gap.xml")
    client = asana_client_from_env(out / "asana")
    if not hasattr(client, "create_tasks"):
        raise RuntimeError("ASANA_BACKEND=live is not used by the offline demo")
    client.create_tasks(plan["asana_tasks"])

    scenario_path = root / "scenarios" / "program_story.yaml"
    scenario = load_scenario(scenario_path)
    network = build_network(scenario, demo_seeds())
    results = simulate_results(scenario, network)
    cycles = run_pdsa(scenario, results)
    crm = apply_pipeline_stall(build_crm(network["partners"], scenario["seed"], AS_OF), scenario, AS_OF)
    salesforce_client_from_env(crm).export_csv(out / "crm_export")
    ready = readiness_view(crm["Opportunity"], AS_OF, open_gaps_by_partner(results))
    analysis = analyze(results, scenario["program_start_week"])
    updates = render_updates(
        scenario, network["partners"], analysis, results, ready,
        {"baseline_cost": plan["baseline_cost"], "forecast_cost": plan["forecast_cost"]},
    )
    packet = out / "updates"
    packet.mkdir(parents=True, exist_ok=True)
    (packet / "steering.md").write_text(updates["steering"]["text"] + "\n")
    (packet / "internal.md").write_text(updates["internal"]["text"] + "\n")
    for pid, written in updates["partners"].items():
        (packet / f"{pid}.md").write_text(written["text"] + "\n")
    (packet / "PERMISSIONS.md").write_text(permissions_markdown())
    (out / "pdsa_log.json").write_text(json.dumps(cycles, indent=2) + "\n")

    n_per_arm = sample_size_per_arm(EFFECT_P_A, EFFECT_P_B)
    trial = run_trial(17, EFFECT_P_A, EFFECT_P_B, n_per_arm=n_per_arm)
    ab_cycle = pdsa_from_trial(trial)
    (out / "ab_trial.json").write_text(json.dumps({"trial": trial, "pdsa": ab_cycle}, indent=2, default=str) + "\n")

    bank = load_bank()
    answers = answer_all()
    write_pipeline_workbook(out / "rfp_tracker.xlsx", {
        "Questions": tracker(),
        "Retrieval": answers,
        "Library": [{"id": entry["id"], "title": entry["title"], "body": entry["body"], "label": "SYNTHETIC"} for entry in bank["entries"]],
    })

    extracts = {
        "care_gap_weekly": care_gap_weekly(results),
        "pipeline": pipeline_extract(ready),
        "pdsa": pdsa_extract(cycles),
        "budget_burn": budget_extract(plan["burn"]),
    }
    write_extracts(out / "tableau", extracts)
    write_preview(out / "tableau" / "preview.html", [
        ("Care-gap week (sample)", extracts["care_gap_weekly"]),
        ("PDSA log", extracts["pdsa"]),
        ("Budget burn", extracts["budget_burn"]),
    ])
    materialize_yaml(root / "evals" / "heldout")

    summary = {
        "label": "SYNTHETIC SIMULATION",
        "controls_forecast_usd": plan["forecast_cost"],
        "controls_baseline_usd": plan["baseline_cost"],
        "asana_tasks": len(plan["asana_tasks"]),
        "pdsa_weeks": len(cycles),
        "partner_leaks": sum(len(v) for v in updates["leaks"].values()),
        "ab_decision": trial["decision"],
        "ab_n_per_arm": n_per_arm,
        "rfp_flagged": sum(1 for row in answers if row["status"] == "flagged"),
        "rfp_correct": sum(1 for row in answers if row["correct"]),
        "rfp_questions": len(answers),
    }
    if eval_report:
        report = run_eval()
        call = decision(report)
        (out / "eval_report.json").write_text(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2) + "\n")
        (out / "eval_rows.json").write_text(json.dumps(report["rows"], indent=2) + "\n")
        bullets = resume_bullets(report)
        (out / "RESUME_BULLETS.md").write_text(bullets)
        write_pipeline_workbook(out / "scaling_gonogo.xlsx", {
            "Decision": [{"decision": call["decision"], "label": call["label"]}],
            "Gates": call["gates"],
        })
        summary["decision"] = call["decision"]
        summary["top1"] = [report["top1_correct"], report["top1_total"]]
    (out / "program_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the synthetic care-gap program artifacts.")
    parser.add_argument("--eval", action="store_true", help="also run the held-out eval and the go/no-go workbook")
    args = parser.parse_args()
    print(json.dumps(run(eval_report=args.eval), indent=2))


if __name__ == "__main__":
    main()
