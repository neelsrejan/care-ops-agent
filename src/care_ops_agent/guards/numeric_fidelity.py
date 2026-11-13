"""Reject narrative numbers that are not in the computed facts.

Identifiers such as ``L-4419`` and ``2.4.0`` are removed before the scan
when that exact string appears in the facts, so a lot id is not mistaken
for a rate and is also not a free pass for some other number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_NUMBER = re.compile(r"(?<![A-Za-z0-9._-])(\d+(?:\.\d+)?)")
_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


@dataclass
class FidelityResult:
    ok: bool
    unknown: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "unknown": self.unknown}


def _walk_numbers(obj: Any, found: set[float]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        value = float(obj)
        found.add(value)
        found.add(round(value, 2))
        found.add(round(value, 4))
        if 0.0 < abs(value) <= 1.0:
            found.add(round(value * 100.0, 2))
            found.add(round(value * 100.0, 1))
        return
    if isinstance(obj, dict):
        for item in obj.values():
            _walk_numbers(item, found)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _walk_numbers(item, found)


def _identifiers(obj: Any, found: set[str]) -> None:
    if isinstance(obj, str):
        if len(obj) >= 2:
            found.add(obj)
        return
    if isinstance(obj, dict):
        for item in obj.values():
            _identifiers(item, found)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _identifiers(item, found)


def allowed_numbers(facts: Any) -> set[float]:
    found: set[float] = set()
    _walk_numbers(facts, found)
    return found


def _atol(value: float) -> float:
    # Counts (14400 vs 14400.4) get half a unit. Rates printed to two
    # decimals get 0.03, so 3.67 matches 3.67 and 3.70, and 3.72 does not.
    if abs(value) >= 50:
        return 0.51
    return 0.03


def check_narrative(text: str, facts: Any) -> FidelityResult:
    """Return ok=False when any remaining number is not near a fact."""
    identifiers: set[str] = set()
    _identifiers(facts, identifiers)
    masked = _DATE.sub(" ", text)
    for identifier in sorted(identifiers, key=len, reverse=True):
        masked = masked.replace(identifier, " ")
    allowed = allowed_numbers(facts)
    unknown: list[float] = []
    for match in _NUMBER.finditer(masked):
        value = float(match.group(1))
        if any(abs(value - candidate) <= _atol(value) for candidate in allowed):
            continue
        unknown.append(value)
    return FidelityResult(ok=not unknown, unknown=unknown)
