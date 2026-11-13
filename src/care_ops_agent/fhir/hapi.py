"""Optional read of a public FHIR metadata endpoint.

Patient data for this project stays in local Synthea files. ``upload_bundle``
does not POST. A public test server such as HAPI is world-readable and is not
a destination for these bundles. See ADR 0006.
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
    """Refuse every upload, including when ``allow_write`` is set.

    ``allow_write`` is accepted so older call sites still run, and it does not
    open a connection. ``base`` is ignored for the same reason.
    """
    del allow_write, base
    return {
        "mode": "blocked",
        "reason": "FHIR bundles stay in local files and are not uploaded to a public server",
        "entries": len(bundle.get("entry", [])),
    }
