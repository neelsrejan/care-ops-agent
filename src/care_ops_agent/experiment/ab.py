"""Two-proportion outreach test. Patients and scripts are synthetic.

Script A is the current outreach text. Script B is the variant. A trial draws
a fixed seed, assigns equal arms, and tests whether the closed-gap rates differ.
The sample size is the usual normal approximation for a two-sided test. The
language model does not pick the size or the p-value.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import stats

# Seeded truth for the portfolio run. Not estimated from Synthea.
EFFECT_P_A = 0.22
EFFECT_P_B = 0.48
NULL_P = 0.35
ALPHA = 0.05
POWER = 0.90


def sample_size_per_arm(p1: float, p2: float, alpha: float = ALPHA, power: float = POWER) -> int:
    """Equal-arm sample size for a two-sided test of two independent proportions."""
    if not 0 < p1 < 1 or not 0 < p2 < 1:
        raise ValueError("rates must sit strictly between 0 and 1")
    if p1 == p2:
        raise ValueError("the approximation needs two different rates")
    z_alpha = float(stats.norm.ppf(1 - alpha / 2))
    z_power = float(stats.norm.ppf(power))
    pooled = (p1 + p2) / 2
    se_null = math.sqrt(2 * pooled * (1 - pooled))
    se_alt = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    n = ((z_alpha * se_null + z_power * se_alt) / (p1 - p2)) ** 2
    return int(math.ceil(n))


def _two_proportion(k1: int, n1: int, k2: int, n2: int) -> dict[str, float]:
    p1 = k1 / n1
    p2 = k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = 0.0 if se == 0 else (p2 - p1) / se
    p_value = float(2 * stats.norm.sf(abs(z)))
    return {"p1": p1, "p2": p2, "z": z, "p_value": p_value}


def run_trial(seed: int, p_a: float, p_b: float, n_per_arm: int | None = None,
              alpha: float = ALPHA) -> dict[str, Any]:
    """Randomize 2n synthetic patients and read the closed-gap rates.

    When the two planned rates differ, ``n_per_arm`` defaults to the 90% power
    calculation. A null trial has to pass ``n_per_arm`` because the formula is
    undefined at a zero difference.
    """
    planned = None if p_a == p_b else sample_size_per_arm(p_a, p_b, alpha=alpha)
    n = int(n_per_arm if n_per_arm is not None else (planned if planned is not None else 0))
    if n < 1:
        raise ValueError("n_per_arm is required when the two rates match")
    rng = np.random.default_rng(seed)
    arms = np.array(["A"] * n + ["B"] * n)
    rng.shuffle(arms)
    thresholds = np.where(arms == "A", p_a, p_b)
    outcomes = rng.random(len(arms)) < thresholds
    closed_a = int(outcomes[arms == "A"].sum())
    closed_b = int(outcomes[arms == "B"].sum())
    stats_row = _two_proportion(closed_a, n, closed_b, n)
    if stats_row["p_value"] < alpha and stats_row["p2"] > stats_row["p1"]:
        decision = "scale_b"
    elif stats_row["p_value"] < alpha and stats_row["p1"] > stats_row["p2"]:
        decision = "scale_a"
    else:
        decision = "no_difference"
    return {
        "label": "SYNTHETIC SIMULATION",
        "seed": seed,
        "alpha": alpha,
        "planned_n_per_arm": planned,
        "n_per_arm": n,
        "assigned_a": int((arms == "A").sum()),
        "assigned_b": int((arms == "B").sum()),
        "closed_a": closed_a,
        "closed_b": closed_b,
        "rate_a": stats_row["p1"],
        "rate_b": stats_row["p2"],
        "z": stats_row["z"],
        "p_value": stats_row["p_value"],
        "decision": decision,
    }


def repeat_trials(seeds: list[int], p_a: float, p_b: float, n_per_arm: int) -> dict[str, Any]:
    rows = [run_trial(seed, p_a, p_b, n_per_arm=n_per_arm) for seed in seeds]
    return {"trials": rows, "n": len(rows)}


def effect_recovered(trial: dict[str, Any]) -> bool:
    return trial["decision"] == "scale_b"


def null_quiet(trial: dict[str, Any]) -> bool:
    return trial["decision"] == "no_difference"


def pdsa_from_trial(trial: dict[str, Any]) -> dict[str, Any]:
    """The A/B readout is PDSA 4 in the program story, not a separate method."""
    act = {"scale_b": "adopt", "scale_a": "adopt", "no_difference": "abandon"}[trial["decision"]]
    if trial["decision"] == "scale_b":
        action = "Scale script B. The closed-gap rate is higher and the test cleared alpha."
    elif trial["decision"] == "scale_a":
        action = "Keep script A. It beat script B."
    else:
        action = "Do not scale either script. The test did not clear alpha."
    return {
        "week": "AB",
        "plan": "Compare outreach script A with script B on gaps closed.",
        "do": f"Randomize {trial['n_per_arm']} synthetic patients per arm.",
        "study": f"Decision {trial['decision']}.",
        "act": act,
        "action": action,
        "decision": trial["decision"],
        "label": "SYNTHETIC",
    }
