"""Simulated provider network (SYNTHETIC) built on real public seeds.

- Partners: 8 CA acute-care facilities from the CMS file, used ONLY as name/location seeds.
- Patients: Synthea patients in each measure's denominator (from the Postgres views),
  resampled into partner panels with new synthetic ids.
- Weekly results: on each simulated visit a result is recorded; whether it meets the
  measure is drawn from the scenario's synthetic probabilities, plus the injected change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from care_ops_agent.metrics.measures import MEASURE_VIEWS

CLINICS = ("C1", "C2", "C3")
VISIT_PROB = 0.25  # weekly chance a denominator patient has a visit with a qualifying result (synthetic)
PANEL_PER_MEASURE = 300  # synthetic patients per partner per measure


def load_scenario(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text())


def seeds_from_db(con) -> dict[str, Any]:
    from care_ops_agent import db

    partners = db.fetch(con, "SELECT facility_id, facility_name, city FROM mart.v_partner_seed WHERE state = 'CA' ORDER BY facility_id")
    roster = {m: [r["patient_id"] for r in db.fetch(con, f"SELECT patient_id FROM {v}")] for m, v in MEASURE_VIEWS.items()}
    return {"partners": partners, "roster": roster}


def build_network(scenario: dict[str, Any], seeds: dict[str, Any], n_partners: int = 8) -> dict[str, Any]:
    rng = np.random.default_rng(scenario["seed"])
    pool = seeds["partners"]
    idx = sorted(rng.choice(len(pool), size=n_partners, replace=False).tolist())
    partners = [{"partner_id": f"P{i + 1}", "seed_facility_id": pool[j]["facility_id"],
                 "name": f"{pool[j]['facility_name'].title()} Partner Group (SYNTHETIC)", "city": pool[j]["city"].title()}
                for i, j in enumerate(idx)]
    panel = []
    for p in partners:
        for m, roster in seeds["roster"].items():
            picks = rng.choice(len(roster), size=PANEL_PER_MEASURE, replace=True)
            for k, pick in enumerate(picks):
                panel.append({"partner_id": p["partner_id"], "clinic": CLINICS[k % 3], "measure": m,
                              "patient_key": f"{p['partner_id']}-{m[:3]}-{k:04d}", "synthea_patient_id": roster[pick]})
    return {"partners": partners, "panel": pd.DataFrame(panel)}


def simulate_results(scenario: dict[str, Any], network: dict[str, Any]) -> pd.DataFrame:
    rng = np.random.default_rng(scenario["seed"] + 1)
    panel = network["panel"]
    inj = scenario.get("injection") or {"type": "none"}
    target_pid = f"P{inj['partner_index'] + 1}" if "partner_index" in inj else None
    rows = []
    for week in range(1, scenario["weeks"] + 1):
        visits = panel[rng.random(len(panel)) < VISIT_PROB]
        for r in visits.itertuples(index=False):
            p_met = scenario["baseline_met"][r.measure]
            missing = False
            after = week >= scenario["program_start_week"]
            if after and r.partner_id == target_pid and r.measure == inj.get("measure"):
                if inj["type"] == "clinic_drop" and r.clinic == inj["clinic"]:
                    p_met = inj["met_prob_after"]
                elif inj["type"] == "partner_drop":
                    p_met = inj["met_prob_after"]
                elif inj["type"] == "missing_feed":
                    missing = rng.random() < inj["missing_share_after"]
            met = None if missing else bool(rng.random() < p_met)
            rows.append({"week": week, "partner_id": r.partner_id, "clinic": r.clinic, "measure": r.measure,
                         "patient_key": r.patient_key, "result_recorded": not missing, "met": met})
    df = pd.DataFrame(rows)
    df.attrs["label"] = "SYNTHETIC SIMULATION"
    df.attrs["scenario_id"] = scenario["id"]
    return df
