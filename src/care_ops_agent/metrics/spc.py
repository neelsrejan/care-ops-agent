"""p-chart control limits and the four Western Electric zone rules.

Limits use the pooled invalid rate ``p_bar`` and the subgroup size of each
period:

    SE_i = sqrt( p_bar * (1 - p_bar) / n_i )
    UCL_i = p_bar + 3 * SE_i
    LCL_i = max(0, p_bar - 3 * SE_i)

Rules (applied to z_i = (p_i - p_bar) / SE_i):

1. One point beyond 3 sigma.
2. Two of three consecutive points beyond 2 sigma, same side.
3. Four of five consecutive points beyond 1 sigma, same side.
4. Eight consecutive points on the same side of the center line.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def control_limits(p_bar: float, n: int) -> tuple[float, float, float]:
    """Return (lcl, ucl, standard_error) for one subgroup."""
    if n <= 0:
        raise ValueError("n must be positive")
    p_bar = min(1.0, max(0.0, float(p_bar)))
    se = math.sqrt(p_bar * (1.0 - p_bar) / n)
    return (max(0.0, p_bar - 3.0 * se), min(1.0, p_bar + 3.0 * se), se)


def western_electric(z_values: list[float]) -> list[dict[str, Any]]:
    """Flag Western Electric rules. ``z_values`` are in time order."""
    z = [float(value) for value in z_values]
    found: list[dict[str, Any]] = []
    n = len(z)

    def add(index: int, rule: int, side: str) -> None:
        found.append({"index": index, "rule": rule, "side": side, "z": z[index]})

    for i, value in enumerate(z):
        if value > 3.0:
            add(i, 1, "high")
        elif value < -3.0:
            add(i, 1, "low")

    for i in range(n):
        window = z[max(0, i - 2) : i + 1]
        if len(window) < 3:
            continue
        if sum(value > 2.0 for value in window) >= 2:
            add(i, 2, "high")
        if sum(value < -2.0 for value in window) >= 2:
            add(i, 2, "low")

    for i in range(n):
        window = z[max(0, i - 4) : i + 1]
        if len(window) < 5:
            continue
        if sum(value > 1.0 for value in window) >= 4:
            add(i, 3, "high")
        if sum(value < -1.0 for value in window) >= 4:
            add(i, 3, "low")

    for i in range(n):
        window = z[max(0, i - 7) : i + 1]
        if len(window) < 8:
            continue
        if all(value > 0.0 for value in window):
            add(i, 4, "high")
        if all(value < 0.0 for value in window):
            add(i, 4, "low")

    return found


def p_chart(df: pd.DataFrame, freq: str = "W-SUN") -> dict[str, Any]:
    """Weekly p-chart. Periods with no runs are dropped."""
    frame = df.loc[:, ["date", "invalid"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["invalid"] = frame["invalid"].astype(int)
    grouped = frame.groupby(pd.Grouper(key="date", freq=freq), sort=True)
    points: list[dict[str, Any]] = []
    for period, sub in grouped:
        n = int(len(sub))
        if n == 0:
            continue
        k = int(sub["invalid"].sum())
        points.append(
            {
                "period": pd.Timestamp(period).date().isoformat(),
                "n": n,
                "k": k,
                "p": k / n,
            }
        )
    total_n = sum(point["n"] for point in points)
    total_k = sum(point["k"] for point in points)
    p_bar = (total_k / total_n) if total_n else 0.0
    for point in points:
        lcl, ucl, se = control_limits(p_bar, point["n"])
        point["p_bar"] = p_bar
        point["lcl"] = lcl
        point["ucl"] = ucl
        point["se"] = se
        point["z"] = ((point["p"] - p_bar) / se) if se > 0 else 0.0
    violations = western_electric([point["z"] for point in points])
    for violation in violations:
        violation["period"] = points[violation["index"]]["period"]
    return {"p_bar": p_bar, "points": points, "violations": violations}
