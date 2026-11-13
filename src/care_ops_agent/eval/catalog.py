"""The 20 held-out scenarios. The four dev files in ``scenarios/`` are not in this list.

Families follow the build plan: clinic gaps, partner gaps, missing feeds,
a feed on a measure other than the dev HbA1c case, onboarding stalls, mixed
causes, quiet weeks, and near-threshold shifts that should stay quiet.
"""

from __future__ import annotations

from typing import Any

BASELINE = {"hba1c_control": 0.62, "bp_control": 0.66, "breast_cancer_screening": 0.58}
DEV_IDS = {"clinic_bp_drop", "missing_a1c_feed", "partner_screening_gap", "no_signal"}


def _base(scenario_id: str, seed: int, family: str) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "label": "SYNTHETIC SIMULATION",
        "family": family,
        "seed": seed,
        "weeks": 20,
        "program_start_week": 14,
        "baseline_met": dict(BASELINE),
        "held_out": True,
    }


def _clinic(scenario_id: str, seed: int, partner: int, clinic: str, measure: str, after: float) -> dict[str, Any]:
    row = _base(scenario_id, seed, "clinic_gap")
    row["injection"] = {
        "type": "clinic_drop", "partner_index": partner, "clinic": clinic,
        "measure": measure, "met_prob_after": after,
    }
    row["truth"] = {"kind": "care_gap", "partner_index": partner, "clinic": clinic, "measure": measure}
    return row


def _partner(scenario_id: str, seed: int, partner: int, measure: str, after: float) -> dict[str, Any]:
    row = _base(scenario_id, seed, "partner_gap")
    row["injection"] = {"type": "partner_drop", "partner_index": partner, "measure": measure, "met_prob_after": after}
    row["truth"] = {"kind": "care_gap", "partner_index": partner, "clinic": None, "measure": measure}
    return row


def _feed(scenario_id: str, seed: int, partner: int, measure: str, share: float, family: str) -> dict[str, Any]:
    row = _base(scenario_id, seed, family)
    row["injection"] = {"type": "missing_feed", "partner_index": partner, "measure": measure, "missing_share_after": share}
    row["truth"] = {"kind": "data_issue", "partner_index": partner, "clinic": None, "measure": measure}
    return row


def _quiet(scenario_id: str, seed: int, family: str, injection: dict[str, Any] | None = None) -> dict[str, Any]:
    row = _base(scenario_id, seed, family)
    row["injection"] = injection or {"type": "none"}
    row["truth"] = {"kind": "none"}
    return row


def heldout_scenarios() -> list[dict[str, Any]]:
    rows = [
        _clinic("hold_clinic_bp_p1_c1", 101, 0, "C1", "bp_control", 0.34),
        _clinic("hold_clinic_a1c_p5_c3", 118, 4, "C3", "hba1c_control", 0.30),
        _clinic("hold_clinic_bcs_p7_c2", 133, 6, "C2", "breast_cancer_screening", 0.28),
        _partner("hold_partner_a1c_p3", 207, 2, "hba1c_control", 0.30),
        _partner("hold_partner_bp_p6", 219, 5, "bp_control", 0.32),
        _partner("hold_partner_bcs_p8", 228, 7, "breast_cancer_screening", 0.26),
        _feed("hold_feed_a1c_p2", 301, 1, "hba1c_control", 0.75, "missing_feed"),
        _feed("hold_feed_a1c_p4", 314, 3, "hba1c_control", 0.80, "missing_feed"),
        _feed("hold_feed_a1c_p7", 327, 6, "hba1c_control", 0.70, "missing_feed"),
        _feed("hold_feed_bp_p3", 341, 2, "bp_control", 0.75, "other_measure_feed"),
        _feed("hold_feed_bcs_p5", 356, 4, "breast_cancer_screening", 0.72, "other_measure_feed"),
        _quiet("hold_stall_p3", 401, "stall"),
        _quiet("hold_stall_p6", 418, "stall"),
        _base("hold_mixed_bp_and_a1c", 501, "mixed"),
        _base("hold_mixed_bcs_and_bp", 522, "mixed"),
        _quiet("hold_quiet_a", 601, "no_signal"),
        _quiet("hold_quiet_b", 617, "no_signal"),
        _quiet("hold_quiet_c", 633, "no_signal"),
        _quiet("hold_near_bp_p2", 701, "near_threshold", {
            "type": "clinic_drop", "partner_index": 1, "clinic": "C2",
            "measure": "bp_control", "met_prob_after": 0.64,
        }),
        _quiet("hold_near_a1c_p4", 714, "near_threshold", {
            "type": "partner_drop", "partner_index": 3, "measure": "hba1c_control", "met_prob_after": 0.60,
        }),
    ]
    rows[11]["pipeline_stall"] = {"partner_index": 2, "stage": "Data Onboarding", "days_in_stage": 21}
    rows[11]["truth"] = {"kind": "onboarding_stall", "partner_index": 2}
    rows[12]["pipeline_stall"] = {"partner_index": 5, "stage": "Qualified", "days_in_stage": 27}
    rows[12]["truth"] = {"kind": "onboarding_stall", "partner_index": 5}
    rows[13]["injections"] = [
        {"type": "clinic_drop", "partner_index": 0, "clinic": "C1", "measure": "bp_control", "met_prob_after": 0.34},
        {"type": "missing_feed", "partner_index": 4, "measure": "hba1c_control", "missing_share_after": 0.75},
    ]
    rows[13]["truth"] = {"kind": "mixed", "signals": [
        {"kind": "care_gap", "partner_index": 0, "clinic": "C1", "measure": "bp_control"},
        {"kind": "data_issue", "partner_index": 4, "clinic": None, "measure": "hba1c_control"},
    ]}
    rows[14]["injections"] = [
        {"type": "partner_drop", "partner_index": 1, "measure": "breast_cancer_screening", "met_prob_after": 0.28},
        {"type": "missing_feed", "partner_index": 6, "measure": "bp_control", "missing_share_after": 0.70},
    ]
    rows[14]["truth"] = {"kind": "mixed", "signals": [
        {"kind": "care_gap", "partner_index": 1, "clinic": None, "measure": "breast_cancer_screening"},
        {"kind": "data_issue", "partner_index": 6, "clinic": None, "measure": "bp_control"},
    ]}
    ids = [row["id"] for row in rows]
    if len(rows) != 20 or len(set(ids)) != 20:
        raise RuntimeError("held-out catalog must contain 20 unique scenarios")
    if set(ids) & DEV_IDS:
        raise RuntimeError("dev scenarios leaked into the held-out catalog")
    return rows


def materialize_yaml(folder) -> list:
    """Write the catalog to YAML files so a reviewer can read the shocks."""
    from pathlib import Path

    import yaml

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for row in heldout_scenarios():
        path = folder / f"{row['id']}.yaml"
        path.write_text(yaml.safe_dump(row, sort_keys=False))
        paths.append(path)
    return paths
