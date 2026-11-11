"""MS Project XML (MSPDI) export of the synthetic WBS.

The file is the schedule a desktop Project client can open. Asana's free plan
has no dependencies, so the Gantt lives here and in the Excel workbook.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = "http://schemas.microsoft.com/project"
HOURS_PER_DAY = 8


def _stamp(day: date, hour: int) -> str:
    return datetime(day.year, day.month, day.day, hour, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")


def _task(parent: ET.Element, uid: int, task: dict[str, Any], uid_of: dict[str, int]) -> None:
    node = ET.SubElement(parent, "Task")
    ET.SubElement(node, "UID").text = str(uid)
    ET.SubElement(node, "ID").text = str(uid)
    ET.SubElement(node, "Name").text = task["name"]
    ET.SubElement(node, "OutlineLevel").text = str(task["outline"])
    ET.SubElement(node, "OutlineNumber").text = task["id"]
    ET.SubElement(node, "Start").text = _stamp(task["start"], 8)
    ET.SubElement(node, "Finish").text = _stamp(task["finish"], 17)
    hours = int(task["days"]) * HOURS_PER_DAY
    ET.SubElement(node, "Duration").text = f"PT{hours}H0M0S"
    ET.SubElement(node, "Summary").text = "1" if task["summary"] else "0"
    notes = "SYNTHETIC SIMULATION."
    if task.get("role"):
        notes += f" Role: {task['role']}."
    if task.get("change_id"):
        notes += f" Change: {task['change_id']}."
    ET.SubElement(node, "Notes").text = notes
    for pred in task.get("preds") or []:
        link = ET.SubElement(node, "PredecessorLink")
        ET.SubElement(link, "PredecessorUID").text = str(uid_of[pred])
        ET.SubElement(link, "Type").text = "1"  # finish-to-start


def project_xml(plan: dict[str, Any]) -> str:
    root = ET.Element("Project", xmlns=NS)
    ET.SubElement(root, "Name").text = "Harbor Health Plan care-gap program (SYNTHETIC)"
    ET.SubElement(root, "Title").text = "SYNTHETIC SIMULATION — not a live project schedule"
    ET.SubElement(root, "ScheduleFromStart").text = "1"
    ET.SubElement(root, "StartDate").text = _stamp(plan["start"], 8)
    finish = max(task["finish"] for task in plan["wbs"])
    ET.SubElement(root, "FinishDate").text = _stamp(finish, 17)
    ET.SubElement(root, "MinutesPerDay").text = "480"
    ET.SubElement(root, "MinutesPerWeek").text = "2400"
    tasks = ET.SubElement(root, "Tasks")
    summary = {
        "id": "0",
        "name": "Harbor Health Plan care-gap program (SYNTHETIC)",
        "outline": 0,
        "start": plan["start"],
        "finish": finish,
        "days": max(task["days"] for task in plan["wbs"]),
        "summary": True,
        "preds": [],
        "role": "",
        "change_id": "",
    }
    ordered = [summary, *plan["wbs"]]
    uid_of = {task["id"]: uid for uid, task in enumerate(ordered)}
    for task in ordered:
        _task(tasks, uid_of[task["id"]], task, uid_of)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def write_project_xml(plan: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(project_xml(plan))
    return path
