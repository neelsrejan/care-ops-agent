"""Flatten Synthea FHIR R4 bundles into rows (Patient, Condition, Observation, Procedure).

Only the codes the three HEDIS-style measures need are kept. Blood pressure in
FHIR R4 is one Observation (LOINC 85354-9, or 55284-4 in older Synthea) with systolic (8480-6) and
diastolic (8462-4) components; we emit one row per component.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

DIABETES = "44054006"
HYPERTENSION = "59621000"
HBA1C = "4548-4"
BP_PANELS = {"85354-9", "55284-4"}  # newer Synthea uses 85354-9; the 2019 sample uses 55284-4
SYSTOLIC, DIASTOLIC = "8480-6", "8462-4"
MAMMOGRAPHY = {"71651007", "24623002", "241055006"}


def _code(resource: dict[str, Any]) -> str:
    codings = (resource.get("code") or {}).get("coding") or [{}]
    return str(codings[0].get("code", ""))


def _ref_id(ref: str | None) -> str:
    return (ref or "").split(":")[-1].split("/")[-1]


def flatten_bundle(bundle: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {"patient": [], "condition": [], "observation": [], "procedure": []}
    for entry in bundle.get("entry", []):
        r = entry.get("resource", {})
        kind = r.get("resourceType")
        if kind == "Patient":
            addr = (r.get("address") or [{}])[0]
            out["patient"].append({
                "patient_id": r["id"], "birth_date": r.get("birthDate"), "death_date": (r.get("deceasedDateTime") or "")[:10] or None,
                "sex": r.get("gender"), "city": addr.get("city"), "state": addr.get("state"),
            })
        elif kind == "Condition" and _code(r) in {DIABETES, HYPERTENSION}:
            out["condition"].append({
                "patient_id": _ref_id(r["subject"]["reference"]), "code": _code(r),
                "onset": (r.get("onsetDateTime") or "")[:10] or None, "abatement": (r.get("abatementDateTime") or "")[:10] or None,
            })
        elif kind == "Observation":
            code, pid, ts = _code(r), _ref_id(r["subject"]["reference"]), r.get("effectiveDateTime")
            if code == HBA1C and "valueQuantity" in r:
                out["observation"].append({"patient_id": pid, "obs_ts": ts, "code": code, "value": r["valueQuantity"]["value"]})
            elif code in BP_PANELS:
                for comp in r.get("component", []):
                    c = _code(comp)
                    if c in {SYSTOLIC, DIASTOLIC} and "valueQuantity" in comp:
                        out["observation"].append({"patient_id": pid, "obs_ts": ts, "code": c, "value": comp["valueQuantity"]["value"]})
        elif kind == "Procedure" and _code(r) in MAMMOGRAPHY:
            period = r.get("performedPeriod") or {}
            out["procedure"].append({"patient_id": _ref_id(r["subject"]["reference"]), "code": _code(r),
                                     "proc_ts": r.get("performedDateTime") or period.get("start")})
    return out


def iter_bundles(folder: Path) -> Iterator[dict[str, Any]]:
    for path in sorted(folder.glob("*.json")):
        bundle = json.loads(path.read_text())
        if bundle.get("resourceType") == "Bundle" and any(e.get("resource", {}).get("resourceType") == "Patient" for e in bundle.get("entry", [])):
            yield bundle


def flatten_all(bundles: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    acc: dict[str, list[dict[str, Any]]] = {"patient": [], "condition": [], "observation": [], "procedure": []}
    for b in bundles:
        for k, rows in flatten_bundle(b).items():
            acc[k].extend(rows)
    return acc
