"""Local CRM stand-in shaped like Salesforce objects (Account, Contact, Opportunity + stage history).

SYNTHETIC. Built so the same records can be imported into a Salesforce Developer
Edition org later (Data Import Wizard CSVs in ``export_salesforce_csv``). No
network calls; no real people. "Agreement" stages are simulated; the author has
not owned real partner contracts.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

STAGES = ["Prospect", "Qualified", "Agreement (simulated)", "Data Onboarding", "Live"]
ROLES = ["Practice Manager", "Medical Director", "Quality Lead", "IT / Data Contact"]


def build_crm(partners: list[dict[str, Any]], seed: int, as_of: date, n_prospects: int = 6) -> dict[str, list[dict[str, Any]]]:
    rng = np.random.default_rng(seed + 100)
    accounts, contacts, opps, history = [], [], [], []
    rows = [(p["partner_id"], p["name"], p.get("city", "")) for p in partners]
    rows += [(f"X{i + 1}", f"Prospect Group {i + 1} (SYNTHETIC)", "") for i in range(n_prospects)]
    for i, (aid, name, city) in enumerate(rows):
        accounts.append({"AccountId": aid, "Name": name, "BillingCity": city, "Type": "Partner" if aid.startswith("P") else "Prospect",
                         "Description": "SYNTHETIC SIMULATION record"})
        for j, role in enumerate(ROLES):
            contacts.append({"ContactId": f"{aid}-C{j + 1}", "AccountId": aid, "FirstName": f"Contact{j + 1}",
                             "LastName": f"{aid} (SYNTHETIC)", "Title": role})
        # current stage: partners mostly late-stage, prospects early
        final = int(rng.integers(2, 5)) if aid.startswith("P") else int(rng.integers(0, 3))
        start = as_of - timedelta(days=int(rng.integers(60, 120)))
        d = start
        for s in range(final + 1):
            history.append({"OpportunityId": f"O-{aid}", "StageName": STAGES[s], "EnteredDate": d.isoformat()})
            if s < final:
                d = d + timedelta(days=int(rng.integers(5, 25)))
        # time in the current stage: 1-30 days (synthetic), never before the previous stage
        prev = date.fromisoformat(history[-2]["EnteredDate"]) if final > 0 else start
        d = max(prev, as_of - timedelta(days=int(rng.integers(1, 31))))
        history[-1]["EnteredDate"] = d.isoformat()
        opps.append({"OpportunityId": f"O-{aid}", "AccountId": aid, "Name": f"{name} network onboarding",
                     "StageName": STAGES[final], "CreatedDate": start.isoformat(), "StageEnteredDate": d.isoformat(),
                     "CloseDate": (as_of + timedelta(days=28)).isoformat()})
    return {"Account": accounts, "Contact": contacts, "Opportunity": opps, "StageHistory": history}


def apply_pipeline_stall(crm: dict[str, list[dict[str, Any]]], scenario: dict[str, Any], as_of: date) -> dict[str, list[dict[str, Any]]]:
    """Force one synthetic opportunity into a stalled onboarding stage.

    Used by held-out scenarios and the program story. Dev scenarios omit
    ``pipeline_stall``, so their CRM draws stay as ``build_crm`` left them.
    """
    spec = scenario.get("pipeline_stall")
    if not spec:
        return crm
    stage = spec.get("stage", "Data Onboarding")
    if stage not in STAGES or stage == "Live":
        raise ValueError(f"stall stage must be an onboarding stage, got {stage!r}")
    pid = f"P{int(spec['partner_index']) + 1}"
    days = int(spec.get("days_in_stage", 21))
    entered = (as_of - timedelta(days=days)).isoformat()
    opp_id = f"O-{pid}"
    created = None
    for opp in crm["Opportunity"]:
        if opp["AccountId"] != pid:
            continue
        created = opp["CreatedDate"]
        opp["StageName"] = stage
        opp["StageEnteredDate"] = entered
    if created is None:
        raise KeyError(pid)
    crm["StageHistory"] = [row for row in crm["StageHistory"] if row["OpportunityId"] != opp_id]
    for name in STAGES[: STAGES.index(stage) + 1]:
        crm["StageHistory"].append({
            "OpportunityId": opp_id,
            "StageName": name,
            "EnteredDate": entered if name == stage else created,
        })
    return crm


def export_salesforce_csv(crm: dict[str, list[dict[str, Any]]], folder: Path) -> list[Path]:
    """Write one CSV per object for Salesforce Data Import Wizard / Data Loader (external ids kept as columns)."""
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for obj, rows in crm.items():
        if not rows:
            continue
        p = folder / f"{obj}.csv"
        with p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        paths.append(p)
    return paths
