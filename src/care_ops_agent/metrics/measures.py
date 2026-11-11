"""Care-gap rates computed in Python from patient-level rows (never in SQL aggregates or the LLM)."""

from __future__ import annotations

from typing import Any, Iterable

from care_ops_agent.metrics.rates import wilson_interval

MEASURE_VIEWS = {
    "hba1c_control": "mart.v_hba1c_control",
    "bp_control": "mart.v_bp_control",
    "breast_cancer_screening": "mart.v_breast_cancer_screening",
}


def met_rate(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Patients with no qualifying result count as NOT met (gap open), as in HEDIS-style logic."""
    rows = list(rows)
    n = len(rows)
    k = sum(1 for r in rows if r.get("met") is True)
    if n == 0:
        return {"denominator": 0, "numerator": 0, "met_rate": None, "gap_rate": None, "ci_low": None, "ci_high": None}
    lo, hi = wilson_interval(k, n)
    return {"denominator": n, "numerator": k, "met_rate": k / n, "gap_rate": 1 - k / n, "ci_low": lo, "ci_high": hi,
            "no_result": sum(1 for r in rows if r.get("met") is None)}
