from datetime import date
from xml.etree import ElementTree as ET

from openpyxl import load_workbook

from care_ops_agent.controls.plan import PROGRAM_START, build_plan, dated_rows
from care_ops_agent.export.mspdi import project_xml
from care_ops_agent.export.workbook import write_pipeline_workbook


def test_budget_capacity_and_dependencies():
    plan = build_plan()
    leaves = plan["leaves"]
    assert plan["forecast_cost"] == sum(task["cost"] for task in leaves)
    assert plan["baseline_cost"] + plan["change_cost"] == plan["forecast_cost"]
    assert plan["change_cost"] > 0
    assert all(row["slack_hours"] >= 0 for row in plan["capacity"])
    by_id = {task["id"]: task for task in leaves}
    for task in leaves:
        for pred in task["preds"]:
            assert task["start"] > by_id[pred]["finish"]
            assert task["start"].weekday() < 5
            assert task["finish"].weekday() < 5
    assert by_id["1.1"]["start"] == PROGRAM_START
    assert any(row["id"] == "CR-001" and row["cost"] == by_id["3.3"]["cost"] for row in plan["changes"])
    burn_cost = sum(row["cost"] for row in plan["burn"])
    assert burn_cost == plan["forecast_cost"]
    assert plan["burn"][-1]["cumulative_cost"] == plan["forecast_cost"]
    assert all(row["score"] == row["likelihood"] * row["impact"] for row in plan["raid"])


def test_controls_workbook_and_project_xml(tmp_path):
    plan = build_plan()
    path = write_pipeline_workbook(tmp_path / "controls.xlsx", {
        "Charter": plan["charter"],
        "WBS": dated_rows(plan["wbs"]),
        "RAID": plan["raid"],
    })
    book = load_workbook(path)
    assert "SYNTHETIC" in book["Charter"]["A1"].value
    assert book["WBS"]["A3"].value  # header is row 2, first data row is 3
    xml = project_xml(plan)
    root = ET.fromstring(xml)
    ns = {"p": "http://schemas.microsoft.com/project"}
    names = [node.text for node in root.findall("p:Tasks/p:Task/p:Name", ns)]
    assert "Confirm the three HEDIS-style measure definitions" in names
    links = root.findall("p:Tasks/p:Task/p:PredecessorLink/p:Type", ns)
    assert links and all(link.text == "1" for link in links)
    assert date.fromisoformat(plan["wbs"][-1]["finish"].isoformat())
