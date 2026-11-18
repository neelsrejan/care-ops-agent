"""Load the public files into hosted Postgres.

Requires CARE_OPS_PG_DSN or DATABASE_URL. Refuses localhost unless
CARE_OPS_ALLOW_LOCAL=1. Does not print the URL.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import psycopg

from care_ops_agent import db
from care_ops_agent.config import find_repo_root
from care_ops_agent.public import catalog
from care_ops_agent.public.download import download_all, file_sha256
from care_ops_agent.public.dsn import redact, require_hosted_dsn
from care_ops_agent.public.parse import parse_cms_zip, parse_hrsa_xlsx, parse_places_csv

HRSA_COLS = [
    "reporting_year", "bhcmis_id", "health_center_name", "city", "state",
    "measure_id", "numerator", "denominator", "published_percent",
]
PLACES_COLS = [
    "release", "county_fips", "state_abbr", "state_name", "county_name",
    "total_population", "pop_18plus", "measure_id", "crude_percent",
    "published_ci_low", "published_ci_high",
]
CMS_COLS = [
    "ratings_year", "contract_id", "organization_type", "contract_name",
    "parent_organization", "measure_code", "measure_id", "measure_name",
    "measurement_period", "published_percent", "status",
]


def load_files(folder: Path, dsn: str) -> dict[str, Any]:
    places = parse_places_csv(folder / "places_county_2025.csv")
    cms = parse_cms_zip(folder / "cms_star_ratings.zip")
    hrsa = parse_hrsa_xlsx(folder / "H80-2025.xlsx")
    hashes = {name: file_sha256(folder / filename) for name, filename in (
        ("cdc_places", "places_county_2025.csv"),
        ("cms_stars", "cms_star_ratings.zip"),
        ("hrsa_uds", "H80-2025.xlsx"),
    )}
    return load_rows(dsn, hrsa=hrsa, places=places, cms=cms, hashes=hashes)


def load_rows(
    dsn: str,
    *,
    hrsa: list[dict[str, Any]],
    places: list[dict[str, Any]],
    cms: list[dict[str, Any]],
    hashes: dict[str, str],
) -> dict[str, Any]:
    try:
        with psycopg.connect(dsn, autocommit=False) as con:
            execute_script(con, find_repo_root() / "sql" / "published" / "01_schema.sql")
            _copy(con, "published.hrsa_measure", HRSA_COLS, [_hrsa(row) for row in hrsa])
            _copy(con, "published.places_county", PLACES_COLS, [_places(row) for row in places])
            _copy(con, "published.cms_contract_measure", CMS_COLS, [_cms(row) for row in cms])
            _sources(con, {"hrsa_uds": len(hrsa), "cdc_places": len(places), "cms_stars": len(cms)}, hashes)
            tests = db.run_sql_tests(con, find_repo_root() / "sql" / "published" / "tests")
            if any(tests.values()):
                con.rollback()
            else:
                con.commit()
    except Exception as exc:
        raise RuntimeError(redact(str(exc))) from exc
    failed = [name for name, count in tests.items() if count]
    return {
        "hrsa_rows": len(hrsa),
        "places_rows": len(places),
        "cms_rows": len(cms),
        "sql_tests": tests,
        "failed": failed,
    }


def execute_script(con: psycopg.Connection, path: Path) -> None:
    """Run a SQL file one statement at a time. psycopg rejects multi-statement strings."""
    stripped = "\n".join(
        line for line in path.read_text().splitlines() if not line.strip().startswith("--")
    )
    for piece in stripped.split(";"):
        statement = piece.strip()
        if statement:
            con.execute(statement)


def _copy(con: psycopg.Connection, table: str, columns: list[str], rows: list[list[Any]]) -> None:
    sql = f"COPY {table} ({', '.join(columns)}) FROM STDIN"
    with con.cursor().copy(sql) as writer:
        for row in rows:
            writer.write_row(row)


def _sources(con: psycopg.Connection, counts: dict[str, int], hashes: dict[str, str]) -> None:
    today = date.today()
    with con.cursor() as cur:
        for source_id, meta in catalog.SOURCES.items():
            cur.execute(
                """
                INSERT INTO published.source (
                  source_id, title, publisher, vintage, retrieved_on, source_url,
                  license, grain, row_count, file_sha256, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    source_id, meta["title"], meta["publisher"], meta["vintage"], today,
                    meta["source_url"], meta["license"], meta["grain"], counts[source_id],
                    hashes[source_id], meta["notes"],
                ),
            )


def _hrsa(row: dict[str, Any]) -> list[Any]:
    return [row[name] for name in HRSA_COLS]


def _places(row: dict[str, Any]) -> list[Any]:
    return ["2025", *[row[name] for name in PLACES_COLS[1:]]]


def _cms(row: dict[str, Any]) -> list[Any]:
    values = {
        "ratings_year": 2027,
        **row,
    }
    return [values[name] for name in CMS_COLS]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public care-gap files and load hosted Postgres.")
    parser.add_argument("--raw-dir", default="", help="Folder with the three files. Defaults to data/raw/public after download.")
    parser.add_argument("--skip-download", action="store_true", help="Use files already in --raw-dir.")
    args = parser.parse_args()
    dsn = require_hosted_dsn()
    folder = Path(args.raw_dir) if args.raw_dir else find_repo_root() / "data" / "raw" / "public"
    if not args.skip_download:
        download_all(folder)
    result = load_files(folder, dsn)
    print(json.dumps(result, indent=2))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
