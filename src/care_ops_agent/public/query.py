"""Read published inputs and compute gaps in Python."""

from __future__ import annotations

from typing import Any

import psycopg

from care_ops_agent.public import catalog
from care_ops_agent.public.gaps import care_gaps
from care_ops_agent.public.narrate import public_note

_CAVEAT = {
    "hrsa_uds": (
        "Counts come from the health-center total columns. The rate is computed in this project. "
        "A fractional numerator is HRSA's weighted chart-sample estimate, and this sentence rounds it. "
        "Diabetes counts poor glycemic status or a missing test, so a higher rate is a wider gap. "
        "This is not certified HEDIS and it is not a chart this project reviewed."
    ),
    "cms_stars": (
        "Each contract value is the percent CMS published. The comparator is the unweighted mean "
        "of contracts that reported a number. This project did not recompute the measure from claims."
    ),
    "cdc_places": (
        "County values are CDC model-based prevalence estimates. The comparator is the "
        "adult-population-weighted mean. This project did not recompute the small-area model."
    ),
}
_YEAR = {"hrsa_uds": 2025, "cms_stars": 2027, "cdc_places": 2025}
_LABEL = {
    "hrsa_uds": "HRSA UDS health centers",
    "cms_stars": "CMS Medicare Advantage contracts",
    "cdc_places": "CDC PLACES counties",
}


def build_view(con: psycopg.Connection, source_id: str, measure_id: str) -> dict[str, Any]:
    if source_id not in catalog.MEASURES or measure_id not in catalog.MEASURES[source_id]:
        raise KeyError(f"Unknown measure {source_id}.{measure_id}")
    spec = catalog.MEASURES[source_id][measure_id]
    rows = _rows(con, source_id, measure_id)
    result = care_gaps(rows, direction=spec["direction"], mode=spec["mode"])
    definition = {
        "source_label": _LABEL[source_id],
        "measure_label": spec["label"],
        "caveat": _CAVEAT[source_id],
        "year": _YEAR[source_id],
    }
    note = public_note(result, definition)
    return {
        "source_id": source_id,
        "measure_id": measure_id,
        "definition": definition,
        "direction": spec["direction"],
        "mode": spec["mode"],
        "rows": result["rows"],
        "summary": result["summary"],
        "note": note,
        "source": _source_row(con, source_id),
    }


def _rows(con: psycopg.Connection, source_id: str, measure_id: str) -> list[dict[str, Any]]:
    if source_id == "hrsa_uds":
        fetched = con.execute(
            """
            SELECT bhcmis_id, health_center_name, state, city, numerator, denominator
            FROM published.hrsa_measure WHERE measure_id = %s
            """,
            (measure_id,),
        ).fetchall()
        return [
            {
                "entity_id": row[0],
                "entity_name": row[1],
                "state": row[2],
                "city": row[3],
                "numerator": row[4],
                "denominator": row[5],
            }
            for row in fetched
        ]
    if source_id == "cdc_places":
        fetched = con.execute(
            """
            SELECT county_fips, county_name, state_abbr, state_name, crude_percent, pop_18plus
            FROM published.places_county WHERE measure_id = %s
            """,
            (measure_id,),
        ).fetchall()
        return [
            {
                "entity_id": row[0],
                "entity_name": f"{row[1]} County, {row[2]}",
                "state": row[2],
                "state_name": row[3],
                "percent": row[4],
                "weight": row[5],
            }
            for row in fetched
        ]
    fetched = con.execute(
        """
        SELECT contract_id, contract_name, organization_type, parent_organization,
               published_percent, status
        FROM published.cms_contract_measure WHERE measure_id = %s
        """,
        (measure_id,),
    ).fetchall()
    return [
        {
            "entity_id": row[0],
            "entity_name": row[1] or row[0],
            "state": "",
            "organization_type": row[2],
            "parent_organization": row[3],
            "percent": row[4],
            "status": row[5],
        }
        for row in fetched
    ]


def _source_row(con: psycopg.Connection, source_id: str) -> dict[str, Any]:
    row = con.execute(
        """
        SELECT title, publisher, vintage, retrieved_on, source_url, license, grain, row_count, notes
        FROM published.source WHERE source_id = %s
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        return {}
    keys = ["title", "publisher", "vintage", "retrieved_on", "source_url", "license", "grain", "row_count", "notes"]
    return dict(zip(keys, row))
