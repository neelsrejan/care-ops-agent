"""Care-gap arithmetic. SQL stores the published inputs. This module owns the rates."""

from __future__ import annotations

from typing import Any

from care_ops_agent.metrics.rates import wilson_interval
from care_ops_agent.public.catalog import GAP_THRESHOLD_PP


def _whole(value: float) -> int | None:
    rounded = round(value)
    if abs(value - rounded) > 1e-6:
        return None
    return int(rounded)


def rate_from_counts(numerator: float, denominator: float) -> float | None:
    if denominator <= 0 or numerator < 0 or numerator > denominator + 1e-6:
        return None
    return numerator / denominator


def _wilson(numerator: float, denominator: float) -> tuple[float, float] | None:
    k = _whole(numerator)
    n = _whole(denominator)
    if k is None or n is None or n <= 0 or k > n:
        return None
    return wilson_interval(k, n)


def _gap_pp(rate: float, comparator: float, direction: str) -> float:
    if direction == "higher_better":
        return (comparator - rate) * 100.0
    if direction == "lower_better":
        return (rate - comparator) * 100.0
    raise ValueError(direction)


def care_gaps(rows: list[dict[str, Any]], *, direction: str, mode: str) -> dict[str, Any]:
    """Return per-entity gaps and the comparator those gaps use.

    mode ``counts`` divides numerator by denominator and pools by summing.
    mode ``percent`` treats ``percent`` as a published 0–100 value and uses
    the unweighted mean of entities that have one.
    mode ``weighted_percent`` uses the same percent, weighted by ``weight``.
    A positive gap_pp means worse than the comparator by that many points.
    """
    prepared: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        rate = _rate(item, mode)
        item["rate"] = rate
        interval = None
        if mode == "counts" and rate is not None:
            interval = _wilson(float(item["numerator"]), float(item["denominator"]))
        item["ci_low"] = None if interval is None else interval[0]
        item["ci_high"] = None if interval is None else interval[1]
        prepared.append(item)

    usable = [item for item in prepared if item["rate"] is not None]
    comparator = _comparator(usable, mode)
    pooled_n, pooled_d = _pooled_counts(usable, mode)
    for item in prepared:
        if item["rate"] is None or comparator is None:
            item["gap_pp"] = None
            item["worse"] = False
            continue
        gap = _gap_pp(item["rate"], comparator, direction)
        item["gap_pp"] = gap
        item["worse"] = gap >= GAP_THRESHOLD_PP

    prepared.sort(key=lambda item: (item["gap_pp"] is None, -(item["gap_pp"] or 0.0), item.get("entity_name") or ""))
    summary = {
        "n_entities": len(prepared),
        "n_with_rate": len(usable),
        "pooled_numerator": pooled_n,
        "pooled_denominator": pooled_d,
        "pooled_rate": None if comparator is None else (
            pooled_n / pooled_d if mode == "counts" and pooled_d else comparator
        ),
        "comparator": comparator,
        "n_worse": sum(1 for item in prepared if item["worse"]),
        "threshold_pp": GAP_THRESHOLD_PP,
        "mode": mode,
        "direction": direction,
    }
    if mode == "counts" and pooled_n is not None and pooled_d:
        interval = _wilson(pooled_n, pooled_d)
        summary["ci_low"] = None if interval is None else interval[0]
        summary["ci_high"] = None if interval is None else interval[1]
    else:
        summary["ci_low"] = None
        summary["ci_high"] = None
    return {"rows": prepared, "summary": summary}


def _rate(row: dict[str, Any], mode: str) -> float | None:
    if mode == "counts":
        numerator = row.get("numerator")
        denominator = row.get("denominator")
        if numerator is None or denominator is None:
            return None
        return rate_from_counts(float(numerator), float(denominator))
    percent = row.get("percent")
    if percent is None:
        return None
    value = float(percent)
    if value < 0 or value > 100:
        return None
    return value / 100.0


def _pooled_counts(rows: list[dict[str, Any]], mode: str) -> tuple[float | None, float | None]:
    if mode != "counts" or not rows:
        return None, None
    numerator = sum(float(row["numerator"]) for row in rows)
    denominator = sum(float(row["denominator"]) for row in rows)
    return numerator, denominator


def _comparator(rows: list[dict[str, Any]], mode: str) -> float | None:
    if not rows:
        return None
    if mode == "counts":
        numerator, denominator = _pooled_counts(rows, mode)
        if not denominator:
            return None
        return numerator / denominator
    if mode == "percent":
        return sum(row["rate"] for row in rows) / len(rows)
    weights = []
    for row in rows:
        weight = row.get("weight")
        if weight is None or float(weight) <= 0:
            continue
        weights.append((row["rate"], float(weight)))
    total = sum(weight for _, weight in weights)
    if total <= 0:
        return None
    return sum(rate * weight for rate, weight in weights) / total
