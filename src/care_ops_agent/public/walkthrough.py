"""Guided hiring-manager flow over the public care-gap rates.

Python chooses the measure, filters the rows, and writes the recommendation
from numbers ``care_gaps`` already computed. ``narrate`` may only rephrase
that sentence. This module does not open a database and does not read secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from care_ops_agent.public import catalog
from care_ops_agent.public.narrate import PUBLIC_SYSTEM_PROMPT, narrate

CHART_LIMIT = 15
STATE_PROMPT_LIMIT = 3


@dataclass(frozen=True)
class Step:
    id: str
    title: str
    short: str


STEPS = (
    Step("brief", "The brief", "Brief"),
    Step("file", "Which file", "File"),
    Step("national", "The national picture", "National"),
    Step("gaps", "The widest gaps", "Gaps"),
    Step("slice", "One slice", "Slice"),
    Step("check", "Check the work", "Check"),
    Step("outcome", "The recommendation", "Outcome"),
)

DEFAULT_FOCUS = "diabetes"
DEFAULT_SOURCE = "hrsa_uds"

# One question, three public definitions. The ids are catalog.MEASURES keys.
FOCUSES: dict[str, dict[str, Any]] = {
    "diabetes": {
        "label": "Diabetes",
        "prompt": "Where does diabetes look worse than the national picture?",
        "blurb": (
            "The three files do not share a diabetes definition. HRSA counts poor control. "
            "CMS counts control. CDC counts how common a diagnosis is. This walkthrough keeps them apart."
        ),
        "measures": {
            "hrsa_uds": "diabetes_poor_control",
            "cms_stars": "diabetes_blood_sugar_controlled",
            "cdc_places": "diabetes_prevalence",
        },
    },
    "blood_pressure": {
        "label": "Blood pressure",
        "prompt": "Where does blood pressure lag the national picture?",
        "blurb": (
            "HRSA and CMS count control under 140/90. CDC counts adults with high blood pressure "
            "who take medication. Those are different questions."
        ),
        "measures": {
            "hrsa_uds": "bp_control",
            "cms_stars": "bp_control",
            "cdc_places": "bp_medication",
        },
    },
    "screening": {
        "label": "Breast cancer screening",
        "prompt": "Where is mammography behind the national picture?",
        "blurb": (
            "HRSA counts women 52–74. CMS publishes the Star Ratings screening percent. "
            "CDC estimates mammography among women 50–74. The age bands differ."
        ),
        "measures": {
            "hrsa_uds": "breast_cancer_screening",
            "cms_stars": "breast_cancer_screening",
            "cdc_places": "mammography",
        },
    },
}

SOURCE_ORDER = ("hrsa_uds", "cms_stars", "cdc_places")
SOURCE_SHORT = {
    "hrsa_uds": "Health centers (HRSA)",
    "cms_stars": "Medicare contracts (CMS)",
    "cdc_places": "Counties (CDC PLACES)",
}
SOURCE_JOB = {
    "hrsa_uds": (
        "Python divides each health center's numerator by its denominator and compares "
        "that rate with the pooled national rate."
    ),
    "cms_stars": (
        "Python averages the contracts that published a percent, with each contract weighted "
        "equally, then scores the gap from that mean."
    ),
    "cdc_places": (
        "Python averages the county estimates with weights equal to the adult population, "
        "then scores each county's gap from that mean."
    ),
}

BANNER = (
    "Public HRSA health-center counts, CMS Medicare Advantage percents, and CDC PLACES county estimates. "
    "Python computes every rate and gap. A model may only rewrite the wording. "
    "Not a patient chart and not certified HEDIS. "
    "The Harbor Health Plan weekly program is a separate labeled simulation and is not this walkthrough."
)


@dataclass(frozen=True)
class Prompt:
    """One-click action. The app applies the fields; this object does not touch session state."""

    id: str
    label: str
    focus_id: str | None = None
    source_id: str | None = None
    state: str | None = None
    search: str | None = None
    goto: str | None = None
    clear_slice: bool = False
    free_explore: bool = False
    reset: bool = False


def step_index(step_id: str) -> int:
    for index, step in enumerate(STEPS):
        if step.id == step_id:
            return index
    raise KeyError(step_id)


def measure_for(focus_id: str, source_id: str) -> str:
    try:
        return str(FOCUSES[focus_id]["measures"][source_id])
    except KeyError as exc:
        raise KeyError(f"Unknown focus or source: {focus_id}.{source_id}") from exc


def direction_sentence(source_id: str, measure_id: str) -> str:
    direction = catalog.MEASURES[source_id][measure_id]["direction"]
    if direction == "lower_better":
        return "On this measure a higher rate is worse. The gap is this rate minus the comparator."
    if direction == "higher_better":
        return "On this measure a higher rate is better. The gap is the comparator minus this rate."
    raise ValueError(direction)


def guide_copy(step_id: str, focus_id: str, source_id: str) -> dict[str, str]:
    """Plain-language doing / why / look for one step. No computed rates."""
    focus = FOCUSES[focus_id]
    source = catalog.SOURCES[source_id]
    measure_id = measure_for(focus_id, source_id)
    measure = catalog.MEASURES[source_id][measure_id]["label"]
    short = SOURCE_SHORT[source_id]
    threshold = f"{catalog.GAP_THRESHOLD_PP:g}"
    copies = {
        "brief": {
            "doing": "The agent is waiting for the question. It computes a rate after a file is chosen.",
            "why": (
                "A hiring manager should see the question before the spreadsheet. "
                f"The question in front of you is: {focus['prompt']}"
            ),
            "look": "The three buttons. Each one is a different care-gap question. Diabetes is the one this walkthrough opens on.",
        },
        "file": {
            "doing": (
                f"The agent is choosing the public file for “{focus['label']}”. "
                "It computes a rate on the next step."
            ),
            "why": f"{focus['blurb']} {SOURCE_JOB[source_id]}",
            "look": (
                f"Selected file: {short}. Grain: {source['grain']}. "
                f"Publisher: {source['publisher']}."
            ),
        },
        "national": {
            "doing": (
                f"The agent reads every {short} row for {measure}. "
                f"Python computes the comparator, how many entities have a rate, and how many "
                f"are at least {threshold} points worse."
            ),
            "why": "The national picture is the baseline. A later step only makes sense against it.",
            "look": (
                "The four numbers, then the sentence under them. "
                f"{direction_sentence(source_id, measure_id)} "
                "The comparator stays national even after you filter."
            ),
        },
        "gaps": {
            "doing": (
                f"The agent ranks the rows by the gap Python just computed and keeps the {CHART_LIMIT} widest. "
                "The chart is only that ranking."
            ),
            "why": "A national average hides the centers, contracts, or counties a program would review first.",
            "look": (
                "Bar length is percentage points worse than the comparator. "
                "The top bar is the widest gap. Names are the published names."
            ),
        },
        "slice": {
            "doing": "The agent applies the state or name you picked and shows only those rows.",
            "why": "The chart is a short list. The table is where you check the numerator, the denominator, and the rate.",
            "look": "The rate and the gap on each row. The comparator you already saw does not change when this table shrinks.",
        },
        "check": {
            "doing": (
                "The agent shows the file it read, the direction of this measure, and the numeric check on its sentence."
            ),
            "why": "The sentence is allowed to change wording. It is not allowed to introduce a number Python did not compute.",
            "look": (
                f"{direction_sentence(source_id, measure_id)} "
                "The caption under the sentence names the check and the backend. "
                "The block below names the publisher, the vintage, and the file."
            ),
        },
        "outcome": {
            "doing": (
                "The agent states a review recommendation from the gaps Python already computed. "
                "A model may only rephrase that sentence."
            ),
            "why": "The walkthrough should end on a decision: who to review first, and where the follow-up lives.",
            "look": (
                "The recommendation, then the read-only status of Asana, Salesforce, and Tableau Public. "
                "This page does not create tasks."
            ),
        },
    }
    if step_id not in copies:
        raise KeyError(step_id)
    return copies[step_id]


def prompts_for(
    step_id: str,
    *,
    focus_id: str,
    source_id: str,
    rows: list[dict[str, Any]] | None = None,
) -> list[Prompt]:
    """Suggested actions for one step. Labels are the button text."""
    if step_id == "brief":
        return [
            Prompt(
                id=f"focus-{key}",
                label=value["label"],
                focus_id=key,
                goto="file",
            )
            for key, value in FOCUSES.items()
        ]
    if step_id == "file":
        return [
            Prompt(
                id=f"source-{key}",
                label=SOURCE_SHORT[key],
                source_id=key,
                goto="national",
            )
            for key in SOURCE_ORDER
        ]
    if step_id == "national":
        return [Prompt(id="show-gaps", label="Show the widest gaps", goto="gaps")]
    if step_id == "gaps":
        return _gap_prompts(rows or [])
    if step_id == "slice":
        prompts = [Prompt(id="clear-slice", label="Show every state and name", clear_slice=True)]
        prompts.append(Prompt(id="check-source", label="Check the source and the sentence", goto="check"))
        return prompts
    if step_id == "check":
        return [Prompt(id="see-recommendation", label="Read the recommendation", goto="outcome")]
    if step_id == "outcome":
        return [
            Prompt(id="free-explore", label="Open free explore", free_explore=True),
            Prompt(id="start-over", label="Start over", reset=True, goto="brief", clear_slice=True),
        ]
    raise KeyError(step_id)


def _gap_prompts(rows: list[dict[str, Any]]) -> list[Prompt]:
    prompts: list[Prompt] = []
    worst = next((row for row in rows if row.get("gap_pp") is not None), None)
    if worst is not None:
        name = str(worst.get("entity_name") or "").strip()
        prompts.append(
            Prompt(
                id="widest",
                label=f"Start with {_clip(name)}",
                search=name,
                state="All",
                goto="slice",
            )
        )
    for state, count in worse_states(rows, limit=STATE_PROMPT_LIMIT):
        prompts.append(
            Prompt(
                id=f"state-{state}",
                label=f"Look at {state} ({count} worse)",
                state=state,
                search="",
                goto="slice",
            )
        )
    if not prompts:
        prompts.append(Prompt(id="no-gaps", label="Go to the recommendation", goto="outcome"))
    return prompts


def _clip(name: str, limit: int = 42) -> str:
    if len(name) <= limit:
        return name or "the widest gap"
    return name[: limit - 1].rstrip() + "…"


def filter_rows(rows: list[dict[str, Any]], *, state: str, search: str) -> list[dict[str, Any]]:
    shown = rows
    if state and state != "All":
        shown = [row for row in shown if row.get("state") == state]
    needle = (search or "").strip().lower()
    if needle:
        shown = [row for row in shown if needle in (row.get("entity_name") or "").lower()]
    return shown


def state_options(rows: list[dict[str, Any]]) -> list[str]:
    found = sorted({str(row.get("state")) for row in rows if row.get("state")})
    return ["All", *found]


def worse_states(rows: list[dict[str, Any]], *, limit: int = STATE_PROMPT_LIMIT) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        state = row.get("state") or ""
        if row.get("worse") and state:
            counts[state] = counts.get(state, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


def widest_rows(rows: list[dict[str, Any]], *, limit: int = CHART_LIMIT) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("gap_pp") is not None][:limit]


def _show_count(value: float | None) -> int | float | None:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-6:
        return int(round(value))
    return round(float(value), 1)


def _percent_number(rate: float | None) -> float | None:
    if rate is None:
        return None
    return round(float(rate) * 100.0, 1)


def table_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Columns the hosted table has always shown."""
    return [
        {
            "name": row.get("entity_name"),
            "id": row.get("entity_id"),
            "state": row.get("state") or "",
            "rate_percent": _percent_number(row.get("rate")),
            "gap_pp": None if row.get("gap_pp") is None else round(float(row["gap_pp"]), 1),
            "numerator": _show_count(row.get("numerator")),
            "denominator": _show_count(row.get("denominator")),
            "status": row.get("status") or "",
        }
        for row in rows
    ]


def recommendation_note(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    definition: dict[str, Any],
) -> dict[str, Any]:
    """Recommendation prose. Numbers come from ``summary`` and ``rows`` only."""
    worst = next((row for row in rows if row.get("gap_pp") is not None), None)
    facts: dict[str, Any] = {
        "n_entities": summary["n_entities"],
        "n_with_rate": summary["n_with_rate"],
        "n_worse": summary["n_worse"],
        "threshold_pp": summary["threshold_pp"],
        "comparator_percent": _percent_number(summary.get("comparator")),
        "source_label": definition["source_label"],
        "measure_label": definition["measure_label"],
        "reporting_year": definition.get("year", ""),
    }
    if worst is not None:
        facts["worst_name"] = worst.get("entity_name") or ""
        facts["worst_gap_pp"] = round(float(worst["gap_pp"]), 1)
        facts["worst_percent"] = _percent_number(worst.get("rate"))
        if worst.get("state"):
            facts["worst_state"] = worst["state"]

    caveat = str(definition.get("caveat") or "")
    if facts["comparator_percent"] is None:
        draft = (
            f"{facts['source_label']} has no numeric rate for {facts['measure_label']}. "
            f"{facts['n_entities']} entities were read. "
            "Recommendation: stop here and check the load before opening a review. "
            f"{caveat}"
        )
    elif not facts["n_worse"]:
        draft = (
            f"{facts['source_label']}, reporting year {facts['reporting_year']}. "
            f"Measure: {facts['measure_label']}. "
            f"Recommendation: keep watching. No entity is at least {facts['threshold_pp']} "
            f"percentage points worse than the comparator of {facts['comparator_percent']} percent. "
            f"{facts['n_with_rate']} of {facts['n_entities']} entities have a rate. "
            f"{caveat}"
        )
    else:
        where = f" ({facts['worst_state']})" if facts.get("worst_state") else ""
        draft = (
            f"{facts['source_label']}, reporting year {facts['reporting_year']}. "
            f"Measure: {facts['measure_label']}. "
            f"Recommendation: review the {facts['n_worse']} entities that are at least "
            f"{facts['threshold_pp']} percentage points worse than the comparator of "
            f"{facts['comparator_percent']} percent. "
            f"Start with {facts['worst_name']}{where}, at {facts['worst_percent']} percent, "
            f"{facts['worst_gap_pp']} percentage points worse. "
            "Python computed the rates and the gaps. This sentence only restates those figures. "
            f"{facts['n_with_rate']} of {facts['n_entities']} entities have a rate. "
            f"{caveat}"
        )
    return narrate(draft, facts, system_prompt=PUBLIC_SYSTEM_PROMPT)
