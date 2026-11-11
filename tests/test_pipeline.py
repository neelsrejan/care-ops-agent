from datetime import date

import pandas as pd

from care_ops_agent.crm.mock import STAGES, build_crm, export_salesforce_csv
from care_ops_agent.export.workbook import write_pipeline_workbook
from care_ops_agent.metrics.pipeline import aging, conversion, open_gaps_by_partner, readiness_view, stage_counts

PARTNERS = [{"partner_id": f"P{i}", "name": f"Partner {i} (SYNTHETIC)", "city": "X"} for i in range(1, 9)]
AS_OF = date(2026, 11, 3)


def test_hand_checked_conversion():
    hist = [{"OpportunityId": o, "StageName": s} for o, stages in {"a": STAGES[:3], "b": STAGES[:1], "c": STAGES[:2]}.items() for s in stages]
    conv = conversion(hist)
    assert conv[0]["reached_from"] == 3 and conv[0]["advanced"] == 2
    assert conv[1]["reached_from"] == 2 and conv[1]["advanced"] == 1


def test_aging_and_stall():
    opps = [{"AccountId": "P1", "StageName": "Qualified", "StageEnteredDate": "2026-10-01"},
            {"AccountId": "P2", "StageName": "Live", "StageEnteredDate": "2026-09-01"}]
    rows = {r["AccountId"]: r for r in aging(opps, AS_OF)}
    assert rows["P1"]["days_in_stage"] == 33 and rows["P1"]["stalled"]
    assert not rows["P2"]["stalled"]  # Live never stalls


def test_open_gaps_uses_latest_result():
    df = pd.DataFrame([
        {"week": 1, "patient_key": "k1", "partner_id": "P1", "measure": "bp_control", "met": False},
        {"week": 2, "patient_key": "k1", "partner_id": "P1", "measure": "bp_control", "met": True},
        {"week": 2, "patient_key": "k2", "partner_id": "P1", "measure": "bp_control", "met": None},
    ])
    assert open_gaps_by_partner(df) == {"P1": {"bp_control": 1}}


def test_crm_export_and_workbook(tmp_path):
    crm = build_crm(PARTNERS, 7, AS_OF)
    assert sum(stage_counts(crm["Opportunity"]).values()) == 14
    assert all("SYNTHETIC" in a["Name"] or "SYNTHETIC" in a["Description"] for a in crm["Account"])
    paths = export_salesforce_csv(crm, tmp_path / "sf")
    assert {p.name for p in paths} == {"Account.csv", "Contact.csv", "Opportunity.csv", "StageHistory.csv"}
    ready = readiness_view(crm["Opportunity"], AS_OF, {"P1": {"bp_control": 5}})
    wb = write_pipeline_workbook(tmp_path / "x.xlsx", {"Readiness": ready})
    from openpyxl import load_workbook
    ws = load_workbook(wb)["Readiness"]
    assert "SYNTHETIC" in ws["A1"].value
