"""Program controls for the simulated Harbor Health Plan care-gap program.

Every hour and dollar is a project-controls figure for the simulation. It is
not a bid, a rate card from an employer, or a P&L. Dates are business days
starting Monday 2026-11-02, the week of the S1–S4 build.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

PROGRAM_START = date(2026, 11, 2)
FUNDED_WEEKS = 10
HOURS_PER_DAY = 8
LABEL = "SYNTHETIC SIMULATION — project-controls figures only, not a bid or a P&L"

# Synthetic blended rates, USD per hour, labeled as such everywhere they appear.
RATES = {
    "Program lead": 110,
    "Quality analyst": 95,
    "Partner success": 85,
    "Data engineer": 120,
}
CAPACITY_FTE = {
    "Program lead": 0.4,
    "Quality analyst": 0.5,
    "Partner success": 0.4,
    "Data engineer": 0.3,
}

# Leaves carry the work. Summaries roll up after the leaves are dated.
# preds are finish-to-start. in_baseline False is an approved change (CR-001).
_TASKS: list[dict[str, Any]] = [
    {"id": "1", "name": "Charter and controls", "summary": True, "section": "Charter"},
    {"id": "1.1", "name": "Confirm the three HEDIS-style measure definitions", "role": "Quality analyst",
     "days": 5, "preds": [], "section": "Charter"},
    {"id": "1.2", "name": "Write the program charter", "role": "Program lead",
     "days": 3, "preds": ["1.1"], "section": "Charter"},
    {"id": "1.3", "name": "Build the WBS, RAID log, and change log", "role": "Program lead",
     "days": 4, "preds": ["1.2"], "section": "Charter"},
    {"id": "2", "name": "Baseline measures and triage", "summary": True, "section": "Data"},
    {"id": "2.1", "name": "Load the synthetic roster and measure views", "role": "Data engineer",
     "days": 5, "preds": ["1.1"], "section": "Data"},
    {"id": "2.2", "name": "Compute baseline care-gap rates with intervals", "role": "Quality analyst",
     "days": 3, "preds": ["2.1"], "section": "Data"},
    {"id": "2.3", "name": "Triage the first care-gap and data-feed signals", "role": "Quality analyst",
     "days": 2, "preds": ["2.2"], "section": "Data"},
    {"id": "3", "name": "Partner onboarding", "summary": True, "section": "Onboarding"},
    {"id": "3.1", "name": "Stage the Salesforce-shaped partner pipeline", "role": "Partner success",
     "days": 4, "preds": ["1.2"], "section": "Onboarding"},
    {"id": "3.2", "name": "Work the stalled data-onboarding accounts", "role": "Partner success",
     "days": 5, "preds": ["3.1"], "section": "Onboarding"},
    {"id": "3.3", "name": "CR-001 Lab-feed remediation", "role": "Data engineer",
     "days": 5, "preds": ["2.3"], "section": "Onboarding", "in_baseline": False,
     "change_id": "CR-001"},
    {"id": "4", "name": "Outreach PDSA and scale decision", "summary": True, "section": "Outreach"},
    {"id": "4.1", "name": "Plan the weekly outreach list from the triage", "role": "Program lead",
     "days": 2, "preds": ["2.3"], "section": "Outreach"},
    {"id": "4.2", "name": "Run the simulated outreach A/B test", "role": "Quality analyst",
     "days": 8, "preds": ["4.1"], "section": "Outreach"},
    {"id": "4.3", "name": "Steering readout and scale go/no-go", "role": "Program lead",
     "days": 3, "preds": ["4.2"], "section": "Outreach"},
]

_RAID = [
    {"id": "R1", "type": "Risk",
     "item": "The public Synthea sample shows every diabetic patient already under 8.0% HbA1c, so it cannot supply outcome rates",
     "likelihood": 3, "impact": 4, "owner": "Quality analyst",
     "response": "Use Synthea for the roster and denominators only, and label outcome probabilities as scenario parameters"},
    {"id": "R2", "type": "Risk",
     "item": "A missing lab feed is mistaken for missed care, and outreach goes to patients whose results never arrived",
     "likelihood": 2, "impact": 5, "owner": "Quality analyst",
     "response": "Hold outreach when the share of visits with no recorded result jumps, and open a feed-check task"},
    {"id": "R3", "type": "Risk",
     "item": "A partner-facing update names another partner's panel",
     "likelihood": 2, "impact": 5, "owner": "Program lead",
     "response": "Render partner text through the role filter and fail the run if another partner id appears"},
    {"id": "A1", "type": "Assumption",
     "item": "Eight synthetic partner groups and three clinics are enough to practice the weekly operating rhythm",
     "likelihood": 1, "impact": 2, "owner": "Program lead",
     "response": "State the panel size next to every rate and do not treat it as a real network"},
    {"id": "I1", "type": "Issue",
     "item": "A public FHIR test server would make uploaded bundles world-readable",
     "likelihood": 3, "impact": 3, "owner": "Data engineer",
     "response": "Keep FHIR files on disk and block the upload function"},
    {"id": "D1", "type": "Dependency",
     "item": "Publishing the dashboard needs a Tableau Public account this repo does not have",
     "likelihood": 4, "impact": 2, "owner": "Program lead",
     "response": "Ship CSV extracts and a written dashboard spec, and leave publishing as a manual step"},
    {"id": "D2", "type": "Dependency",
     "item": "Asana and Salesforce live sync need tokens that are not in the repo",
     "likelihood": 4, "impact": 2, "owner": "Program lead",
     "response": "Default to the offline clients and the CSV import files"},
]


def _roll_to_weekday(day: date) -> date:
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def add_business_days(start: date, duration_days: int) -> tuple[date, date]:
    """Inclusive business-day span. Duration is the count of weekdays, not calendar days."""
    if duration_days < 1:
        raise ValueError("duration_days must be positive")
    start = _roll_to_weekday(start)
    finish = start
    left = duration_days - 1
    while left:
        finish += timedelta(days=1)
        if finish.weekday() < 5:
            left -= 1
    return start, finish


def next_business_day(day: date) -> date:
    return _roll_to_weekday(day + timedelta(days=1))


def _business_days_in(start: date, finish: date) -> list[date]:
    days = []
    cursor = start
    while cursor <= finish:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _program_week(day: date) -> int:
    return (day - PROGRAM_START).days // 7 + 1


def _schedule_leaves(leaves: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for raw in leaves:
        preds = [by_id[pid] for pid in raw["preds"]]
        start = PROGRAM_START if not preds else max(next_business_day(p["finish"]) for p in preds)
        start, finish = add_business_days(start, raw["days"])
        hours = raw["days"] * HOURS_PER_DAY
        rate = RATES[raw["role"]]
        by_id[raw["id"]] = {
            "id": raw["id"],
            "name": raw["name"],
            "summary": False,
            "outline": raw["id"].count(".") + 1,
            "section": raw["section"],
            "role": raw["role"],
            "days": raw["days"],
            "preds": list(raw["preds"]),
            "start": start,
            "finish": finish,
            "hours": hours,
            "rate": rate,
            "cost": hours * rate,
            "in_baseline": raw.get("in_baseline", True),
            "change_id": raw.get("change_id", ""),
        }
    return by_id


def _summaries(by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for raw in _TASKS:
        if not raw.get("summary"):
            continue
        children = [task for task in by_id.values() if task["id"].startswith(raw["id"] + ".")]
        start = min(child["start"] for child in children)
        finish = max(child["finish"] for child in children)
        rows.append({
            "id": raw["id"],
            "name": raw["name"],
            "summary": True,
            "outline": 1,
            "section": raw["section"],
            "role": "",
            "days": len(_business_days_in(start, finish)),
            "preds": [],
            "start": start,
            "finish": finish,
            "hours": sum(child["hours"] for child in children),
            "rate": None,
            "cost": sum(child["cost"] for child in children),
            "in_baseline": all(child["in_baseline"] for child in children),
            "change_id": "",
        })
    return rows


def _raid_rows() -> list[dict[str, Any]]:
    rows = []
    for item in _RAID:
        score = item["likelihood"] * item["impact"]
        rows.append(item | {"score": score, "label": "SYNTHETIC"})
    return rows


def _burn(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, str], dict[str, Any]] = {}
    for task in leaves:
        days = _business_days_in(task["start"], task["finish"])
        if len(days) != task["days"]:
            raise RuntimeError(f"{task['id']} spanned {len(days)} business days, expected {task['days']}")
        for day in days:
            key = (_program_week(day), task["role"])
            bucket = buckets.setdefault(key, {"week": key[0], "role": task["role"], "hours": 0, "cost": 0, "tasks": []})
            bucket["hours"] += HOURS_PER_DAY
            bucket["cost"] += HOURS_PER_DAY * task["rate"]
            if task["id"] not in bucket["tasks"]:
                bucket["tasks"].append(task["id"])
    rows = []
    cumulative = 0
    for key in sorted(buckets):
        row = buckets[key]
        cumulative += row["cost"]
        rows.append({
            "week": row["week"],
            "role": row["role"],
            "hours": row["hours"],
            "cost": row["cost"],
            "cumulative_cost": cumulative,
            "task_ids": ",".join(row["tasks"]),
            "label": "SYNTHETIC",
        })
    return rows


def _capacity(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assigned: dict[str, int] = {role: 0 for role in RATES}
    for task in leaves:
        assigned[task["role"]] += task["hours"]
    rows = []
    for role, fte in CAPACITY_FTE.items():
        available = int(fte * 40 * FUNDED_WEEKS)
        rows.append({
            "role": role,
            "fte": fte,
            "funded_weeks": FUNDED_WEEKS,
            "available_hours": available,
            "assigned_hours": assigned[role],
            "slack_hours": available - assigned[role],
            "label": "SYNTHETIC",
        })
    return rows


def _swimlane(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lanes: dict[tuple[str, int], list[str]] = {}
    for task in leaves:
        seen = set()
        for day in _business_days_in(task["start"], task["finish"]):
            week = _program_week(day)
            if (task["role"], week) in seen:
                continue
            seen.add((task["role"], week))
            lanes.setdefault((task["role"], week), []).append(task["id"])
    return [
        {"role": role, "week": week, "task_ids": ",".join(ids), "label": "SYNTHETIC"}
        for (role, week), ids in sorted(lanes.items())
    ]


def _changes(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task in leaves:
        if task["in_baseline"]:
            continue
        rows.append({
            "id": task["change_id"],
            "task_id": task["id"],
            "title": task["name"],
            "opened": task["start"].isoformat(),
            "hours": task["hours"],
            "cost": task["cost"],
            "status": "approved",
            "reason": "PDSA on the missing HbA1c feed showed a data problem, so feed remediation was added. SYNTHETIC.",
            "label": "SYNTHETIC",
        })
    return rows


def _charter(leaves: list[dict[str, Any]], forecast: int, baseline: int) -> list[dict[str, Any]]:
    finish = max(task["finish"] for task in leaves)
    pairs = [
        ("Program", "Harbor Health Plan care-gap closure (SYNTHETIC)"),
        ("Sponsor", "Steering lead (SYNTHETIC role, not a real person)"),
        ("Program lead", "Network care-gap program lead (simulated)"),
        ("Start", PROGRAM_START.isoformat()),
        ("Finish", finish.isoformat()),
        ("Problem", "Open HbA1c, blood-pressure, and breast cancer screening gaps are spread across 8 synthetic partner groups, and the weekly stack of lists hides the cells that moved."),
        ("Outcome", "Raise the share of attributed synthetic patients meeting each HEDIS-style measure, with effort pointed at the widest real gaps and held back when the feed is the problem."),
        ("In scope", "Measure views, triage, PDSA cycles, partner pipeline, outreach A/B, program controls, and the reporting extracts."),
        ("Out of scope", "Real patients, real partners, certified HEDIS, clinical advice, contracting, and live Asana, Salesforce, or Tableau connections."),
        ("Baseline budget USD", baseline),
        ("Forecast budget USD", forecast),
        ("Label", LABEL),
    ]
    return [{"field": field, "value": value} for field, value in pairs]


def _asana_tasks(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    for task in leaves:
        tasks.append({
            "name": f"[{task['id']}] {task['name']}",
            "notes": (
                f"SYNTHETIC program task for Harbor Health Plan. Role: {task['role']}. "
                f"Effort hours: {task['hours']}. Cost USD: {task['cost']}. "
                f"Baseline: {'yes' if task['in_baseline'] else 'no, approved change ' + task['change_id']}."
            ),
            "section": task["section"],
            "assignee": "",
            "due_on": task["finish"].isoformat(),
            "tags": "synthetic,program-controls",
        })
    return tasks


def build_plan() -> dict[str, Any]:
    leaves_in = [task for task in _TASKS if not task.get("summary")]
    by_id = _schedule_leaves(leaves_in)
    leaves = [by_id[task["id"]] for task in leaves_in]
    summaries = _summaries(by_id)
    order = {task["id"]: index for index, task in enumerate(_TASKS)}
    wbs = sorted([*summaries, *leaves], key=lambda row: order[row["id"]])
    baseline = sum(task["cost"] for task in leaves if task["in_baseline"])
    forecast = sum(task["cost"] for task in leaves)
    capacity = _capacity(leaves)
    if any(row["slack_hours"] < 0 for row in capacity):
        raise RuntimeError("assigned hours exceed funded capacity")
    plan = {
        "label": LABEL,
        "start": PROGRAM_START,
        "charter": _charter(leaves, forecast, baseline),
        "wbs": wbs,
        "leaves": leaves,
        "raid": _raid_rows(),
        "changes": _changes(leaves),
        "burn": _burn(leaves),
        "capacity": capacity,
        "swimlane": _swimlane(leaves),
        "baseline_cost": baseline,
        "forecast_cost": forecast,
        "change_cost": forecast - baseline,
        "asana_tasks": _asana_tasks(leaves),
    }
    return plan


def dated_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ISO strings so the workbook and the CSV do not depend on date formatting."""
    out = []
    for row in rows:
        flat = {}
        for key, value in row.items():
            if isinstance(value, date):
                flat[key] = value.isoformat()
            elif isinstance(value, list):
                flat[key] = ",".join(str(item) for item in value)
            else:
                flat[key] = value
        out.append(flat)
    return out
