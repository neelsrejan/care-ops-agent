"""Pareto of invalid codes, largest count first."""

from __future__ import annotations

from typing import Any

import pandas as pd


def pareto(df: pd.DataFrame, column: str = "invalid_code") -> list[dict[str, Any]]:
    invalid = df.loc[df["invalid"].astype(bool)].copy()
    total = int(len(invalid))
    if total == 0:
        return []
    counts = (
        invalid[column]
        .replace("", "UNSPECIFIED")
        .fillna("UNSPECIFIED")
        .astype(str)
        .value_counts()
    )
    rows: list[dict[str, Any]] = []
    cumulative = 0
    for code, count in counts.items():
        cumulative += int(count)
        rows.append(
            {
                "code": str(code),
                "count": int(count),
                "share": int(count) / total,
                "cumulative_share": cumulative / total,
            }
        )
    return rows
