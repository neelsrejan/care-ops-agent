"""HAPI FHIR R4 public test server adapter (Synthea synthetic data only).

Default is read-only: ``capability()`` checks the server; ``fetch_patients``
pages Patient resources. ``upload_bundle`` POSTs a Synthea transaction bundle
and is OFF unless ``allow_write=True`` (the public server is shared and
world-readable; uploads are a deliberate, approved step).
"""

from __future__ import annotations

from typing import Any

import httpx

BASE = "https://hapi.fhir.org/baseR4"


def capability(base: str = BASE) -> dict[str, Any]:
    r = httpx.get(f"{base}/metadata", params={"_summary": "true"}, timeout=30)
    r.raise_for_status()
    body = r.json()
    return {"fhirVersion": body.get("fhirVersion"), "software": (body.get("software") or {}).get("name")}


def upload_bundle(bundle: dict[str, Any], *, allow_write: bool = False, base: str = BASE) -> dict[str, Any]:
    if not allow_write:
        return {"mode": "dry-run", "entries": len(bundle.get("entry", []))}
    r = httpx.post(base, json=bundle, headers={"Content-Type": "application/fhir+json"}, timeout=120)
    r.raise_for_status()
    return {"mode": "live", "status": r.status_code}
