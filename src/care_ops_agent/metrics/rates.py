"""Invalid rates, Wilson intervals, strata, and chi-square tests.

The Wilson score interval is used because an invalid rate is a binomial
proportion and the usual Wald interval behaves badly when the count is
small. The formula below is the standard one (z from the normal quantile):

    center = (p + z^2 / (2n)) / (1 + z^2 / n)
    margin = z * sqrt( p(1-p)/n + z^2 / (4 n^2) ) / (1 + z^2 / n)
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from scipy import stats


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Return the Wilson score interval for ``k`` events in ``n`` trials."""
    if n <= 0:
        raise ValueError("n must be positive")
    if k < 0 or k > n:
        raise ValueError("k must be between 0 and n")
    z = float(stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    p_hat = k / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denominator
    margin = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n)) / denominator
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    # k = 0 makes the analytic lower bound 0; float noise leaves a ~1e-18 residue.
    if low < 1e-12:
        low = 0.0
    if high > 1.0 - 1e-12:
        high = 1.0
    return (low, high)


def overall_rate(df: pd.DataFrame, spec_invalid_rate: float, promised_validity: float = 0.98) -> dict[str, Any]:
    """Point estimate, Wilson 95% interval, and the spec comparison."""
    n = int(len(df))
    k = int(df["invalid"].astype(bool).sum())
    low, high = wilson_interval(k, n) if n else (0.0, 0.0)
    rate = (k / n) if n else 0.0
    return {
        "n": n,
        "k": k,
        "rate": rate,
        "ci_low": low,
        "ci_high": high,
        "confidence": 0.95,
        "spec_invalid_rate": float(spec_invalid_rate),
        "promised_validity": float(promised_validity),
        "exceeds_spec": bool(rate > spec_invalid_rate),
        "ci_entirely_above_spec": bool(low > spec_invalid_rate),
    }


def stratified_rates(df: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    """Invalid rate and Wilson interval for each level of ``column``, largest rate first."""
    rows: list[dict[str, Any]] = []
    invalid = df["invalid"].astype(bool)
    for key, sub in df.groupby(column, dropna=False):
        n = int(len(sub))
        k = int(invalid.loc[sub.index].sum())
        low, high = wilson_interval(k, n)
        rows.append(
            {
                "column": column,
                "level": str(key),
                "n": n,
                "k": k,
                "rate": k / n,
                "ci_low": low,
                "ci_high": high,
            }
        )
    rows.sort(key=lambda row: (-row["rate"], -row["k"], row["level"]))
    return rows


def chi_square_by(df: pd.DataFrame, column: str) -> dict[str, Any]:
    """Chi-square test of invalid vs valid across levels of ``column``.

    Returns p_value = 1 and chi2 = 0 when the table is degenerate (one
    level, or a column of all zeros), which is "no evidence of a difference"
    rather than an error.
    """
    frame = pd.DataFrame({"level": df[column].astype(str), "invalid": df["invalid"].astype(int)})
    table = pd.crosstab(frame["level"], frame["invalid"])
    for needed in (0, 1):
        if needed not in table.columns:
            table[needed] = 0
    table = table.loc[:, [0, 1]]
    if table.shape[0] < 2 or int(table.to_numpy().sum()) == 0 or (table.to_numpy() == 0).any():
        # A zero cell still has a defined chi-square; only bail out when a
        # whole outcome column is empty or there is a single stratum.
        if table.shape[0] < 2 or table.to_numpy().sum(axis=0).min() == 0:
            return {"column": column, "chi2": 0.0, "p_value": 1.0, "dof": 0, "levels": int(table.shape[0])}
    chi2, p_value, dof, _expected = stats.chi2_contingency(table.to_numpy())
    return {
        "column": column,
        "chi2": float(chi2),
        "p_value": float(p_value),
        "dof": int(dof),
        "levels": int(table.shape[0]),
    }
