"""Turn a computed gap summary into prose. The model may not add numbers."""

from __future__ import annotations

from typing import Any

from care_ops_agent.llm import narrate

PUBLIC_SYSTEM_PROMPT = (
    "You rewrite a care-gap note for clarity. Use ONLY numbers that already appear "
    "in the draft or the facts. Never compute a new rate, gap, count, or year. "
    "These figures are public reported rates. Do not call them synthetic, simulated, "
    "or estimated by you."
)


def _count(value: float) -> int:
    """Sentence form of a count. Weighted UDS numerators are not always whole."""
    return int(round(value))


def _pct(rate: float | None) -> float | None:
    if rate is None:
        return None
    return round(rate * 100.0, 1)


def public_note(result: dict[str, Any], definition: dict[str, str]) -> dict[str, Any]:
    summary = result["summary"]
    worst = next((row for row in result["rows"] if row.get("gap_pp") is not None), None)
    facts: dict[str, Any] = {
        "n_entities": summary["n_entities"],
        "n_with_rate": summary["n_with_rate"],
        "n_worse": summary["n_worse"],
        "threshold_pp": summary["threshold_pp"],
        "pooled_percent": _pct(summary["comparator"]),
        "reporting_year": definition.get("year", ""),
        "source_label": definition["source_label"],
        "measure_label": definition["measure_label"],
    }
    if summary.get("pooled_numerator") is not None:
        facts["pooled_numerator"] = _count(summary["pooled_numerator"])
        facts["pooled_denominator"] = _count(summary["pooled_denominator"])
    if worst is not None:
        facts["worst_name"] = worst.get("entity_name") or ""
        facts["worst_gap_pp"] = round(float(worst["gap_pp"]), 1)
        facts["worst_percent"] = _pct(worst.get("rate"))

    if facts["pooled_percent"] is None:
        draft = (
            f"{definition['source_label']} has no numeric rate for {definition['measure_label']}. "
            f"{facts['n_entities']} entities were read. {definition['caveat']}"
        )
        return narrate(draft, facts, system_prompt=PUBLIC_SYSTEM_PROMPT)

    pieces = [
        f"{definition['source_label']}, reporting year {facts['reporting_year']}.",
        f"Measure: {definition['measure_label']}.",
        f"{facts['n_with_rate']} of {facts['n_entities']} entities have a rate.",
        f"The comparator is {facts['pooled_percent']} percent.",
        (
            f"{facts['n_worse']} entities are at least {facts['threshold_pp']} "
            "percentage points worse than that comparator."
        ),
    ]
    if "pooled_numerator" in facts:
        pieces.append(
            f"The pooled count is {facts['pooled_numerator']} of {facts['pooled_denominator']}."
        )
    if worst is not None:
        pieces.append(
            f"The widest gap is {facts['worst_gap_pp']} percentage points "
            f"at {facts['worst_name']} ({facts['worst_percent']} percent)."
        )
    pieces.append(definition["caveat"])
    draft = " ".join(pieces)
    return narrate(draft, facts, system_prompt=PUBLIC_SYSTEM_PROMPT)
