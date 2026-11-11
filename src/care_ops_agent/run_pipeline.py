"""CLI: python -m care_ops_agent.run_pipeline scenarios/clinic_bp_drop.yaml

Builds the SYNTHETIC CRM, computes pipeline metrics + open gaps, writes:
- out/crm_export/*.csv   (Salesforce Data Import Wizard shape)
- out/<id>_pipeline.xlsx (openpyxl workbook)
- out/tableau/<id>_pipeline.csv (flat extract for Tableau Public)
- out/account_plans/<partner>.md
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date

from care_ops_agent import db
from care_ops_agent.config import load_settings
from care_ops_agent.crm.mock import build_crm, export_salesforce_csv
from care_ops_agent.export.workbook import write_pipeline_workbook
from care_ops_agent.metrics.pipeline import conversion, open_gaps_by_partner, readiness_view, stage_counts
from care_ops_agent.sim.network import build_network, load_scenario, seeds_from_db, simulate_results

AS_OF = date(2026, 11, 3)  # simulated "today" for the pipeline


def account_plan(account: dict, contacts: list[dict], row: dict) -> str:
    lines = [f"# Partner account plan — {account['Name']}", "", "*SYNTHETIC SIMULATION. Template for practice; no real relationship.*", "",
             f"- Stage: {row['StageName']} ({row['days_in_stage']} days){' — STALLED' if row['stalled'] else ''}",
             f"- Open care gaps (simulated patients): {row['open_gaps']} {row['open_gaps_by_measure']}",
             f"- Outreach ready: {'yes' if row['outreach_ready'] else 'no — finish onboarding first'}", "",
             "## Stakeholder map", "| Contact | Role | Influence | Interest | Next touch |", "|---|---|---|---|---|"]
    lines += [f"| {c['FirstName']} {c['LastName']} | {c['Title']} | [__] | [__] | [__] |" for c in contacts]
    lines += ["", "## Goals (patient outcomes)", "- Close open HbA1c, BP and screening gaps for attributed patients.",
              "## Risks / asks", "- [__]"]
    return "\n".join(lines)


def run(path: str) -> dict:
    sc = load_scenario(path)
    with db.connect() as con:
        net = build_network(sc, seeds_from_db(con))
    results = simulate_results(sc, net)
    crm = build_crm(net["partners"], sc["seed"], AS_OF)
    gaps = open_gaps_by_partner(results)
    ready = readiness_view(crm["Opportunity"], AS_OF, gaps)
    conv = conversion(crm["StageHistory"])
    counts = stage_counts(crm["Opportunity"])
    s = load_settings()
    export_salesforce_csv(crm, s.out_dir / "crm_export")
    write_pipeline_workbook(s.out_dir / f"{sc['id']}_pipeline.xlsx",
                            {"Readiness x Gaps": ready, "Stage conversion": conv,
                             "Stage counts": [{"stage": k, "count": v} for k, v in counts.items()],
                             "Accounts": crm["Account"]})
    (s.out_dir / "tableau").mkdir(parents=True, exist_ok=True)
    with (s.out_dir / "tableau" / f"{sc['id']}_pipeline.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label", "account_id", "stage", "days_in_stage", "stalled", "outreach_ready", "measure", "open_gaps"])
        for r in ready:
            for m, n in (r["open_gaps_by_measure"] or {"none": 0}).items():
                w.writerow(["SYNTHETIC", r["AccountId"], r["StageName"], r["days_in_stage"], r["stalled"], r["outreach_ready"], m, n])
    plans = s.out_dir / "account_plans"
    plans.mkdir(parents=True, exist_ok=True)
    by_acc = {a["AccountId"]: a for a in crm["Account"]}
    for r in ready:
        cs = [c for c in crm["Contact"] if c["AccountId"] == r["AccountId"]]
        (plans / f"{r['AccountId']}.md").write_text(account_plan(by_acc[r["AccountId"]], cs, r))
    return {"scenario": sc["id"], "stage_counts": counts, "stalled": [r["AccountId"] for r in ready if r["stalled"]],
            "outreach_ready_top3": [(r["AccountId"], r["open_gaps"]) for r in ready if r["outreach_ready"]][:3]}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(run(p)))
