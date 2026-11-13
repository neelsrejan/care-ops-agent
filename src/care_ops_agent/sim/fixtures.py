"""Small committed roster so tests and the offline demo never download raw files.

The full CMS file and the Synthea FHIR sample stay out of git. ``data.download``
and ``data.load`` still build the real tables when those files and PostgreSQL
are present. Names here are placeholders, not facilities from the CMS file.
"""

from __future__ import annotations

from typing import Any

MEASURES = ("hba1c_control", "bp_control", "breast_cancer_screening")


def demo_seeds(n_facilities: int = 12, roster_n: int = 50) -> dict[str, Any]:
    partners = [
        {"facility_id": f"F{i}", "facility_name": f"SEED FACILITY {i}", "city": "CITY"}
        for i in range(n_facilities)
    ]
    roster = {
        "hba1c_control": [f"a{i}" for i in range(roster_n)],
        "bp_control": [f"b{i}" for i in range(roster_n)],
        "breast_cancer_screening": [f"c{i}" for i in range(roster_n)],
    }
    return {"partners": partners, "roster": roster}
