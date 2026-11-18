"""Baseline draw rates for the weekly program, pinned to the public load.

Computed in Python on 2026-11-18 from the downloaded HRSA UDS 2025 file
(2,878 health-center measure rows). These are pooled rates, not scenario
inventions. Two of them are the same construct as the weekly draw, and the
shift from the old round numbers is small enough that the 10-point triage
rule and the near-threshold shocks still mean what they meant.

HbA1c control is not seeded. HRSA's diabetes figure is poor glycemic status
(>9% or missing), pooled at 26.1%. That is not "HbA1c under 8%." CMS C12,
"Diabetes Care — Blood Sugar Controlled," was 87.6% across contracts that
reported a number. Using 87.6% as the weekly baseline would turn the
held-out near-threshold shock (a draw at 0.60, meant to stay under the
10-point rule) into a large drop, and the scored experiment would no longer
be the one the gate was built on.
"""

from __future__ import annotations

# Exact pooled rates from that load, before rounding into the draw.
EXACT = {
    "hrsa_bp_control": 0.6899,
    "hrsa_breast_cancer_screening": 0.5625,
    "hrsa_diabetes_poor_control": 0.2607,
    "cms_c01_breast_cancer_screening": 0.7442,
    "cms_c12_blood_sugar_controlled": 0.8759,
    "cms_c14_bp_control": 0.8096,
    "places_diabetes_prevalence": 0.1205,
    "places_bp_medication": 0.7555,
    "places_mammography": 0.7612,
}

# Weekly Bernoulli probabilities. hba1c_control stays the original parameter.
PROGRAM_BASELINE = {
    "hba1c_control": 0.62,
    "bp_control": 0.69,
    "breast_cancer_screening": 0.56,
}


def program_baseline() -> dict[str, float]:
    return dict(PROGRAM_BASELINE)
