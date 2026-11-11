"""Load Synthea FHIR R4 bundles + the CMS hospital file into PostgreSQL, build views, run SQL tests."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from care_ops_agent import db
from care_ops_agent.config import find_repo_root
from care_ops_agent.fhir.parse import flatten_all, iter_bundles

COLS = {
    "patient": ["patient_id", "birth_date", "death_date", "sex", "city", "state"],
    "condition": ["patient_id", "code", "onset", "abatement"],
    "observation": ["patient_id", "obs_ts", "code", "value"],
    "procedure": ["patient_id", "code", "proc_ts"],
}
CMS_COLS = {"Facility ID": "facility_id", "Facility Name": "facility_name", "City/Town": "city", "State": "state",
            "County/Parish": "county", "Hospital Type": "hospital_type", "Hospital Ownership": "ownership",
            "Hospital overall rating": "overall_rating"}


def load(fhir_dir: Path, cms_csv: Path) -> dict:
    root = find_repo_root()
    rows = flatten_all(iter_bundles(fhir_dir))
    with db.connect() as con:
        db.run_sql_dir(con, root / "sql" / "schema")
        for table, cols in COLS.items():
            with con.cursor().copy(f"COPY raw.{table} ({','.join(cols)}) FROM STDIN") as cp:
                for r in rows[table]:
                    cp.write_row([r.get(c) for c in cols])
        with open(cms_csv, newline="", encoding="utf-8-sig") as fh, con.cursor().copy(
            f"COPY raw.cms_hospital ({','.join(CMS_COLS.values())}) FROM STDIN") as cp:
            for r in csv.DictReader(fh):
                cp.write_row([r[k] for k in CMS_COLS])
        con.execute("CREATE SCHEMA IF NOT EXISTS mart")
        db.run_sql_dir(con, root / "sql" / "views")
        counts = {t: con.execute(f"SELECT count(*) FROM raw.{t}").fetchone()[0] for t in [*COLS, "cms_hospital"]}
        tests = db.run_sql_tests(con)
    return {"raw_counts": counts, "sql_tests": tests, "failed": [k for k, v in tests.items() if v]}


def main() -> None:
    ap = argparse.ArgumentParser()
    root = find_repo_root()
    ap.add_argument("--fhir-dir", default=str(root / "data/raw/synthea_fhir/fhir"))
    ap.add_argument("--cms", default=str(root / "data/raw/cms/Hospital_General_Information.csv"))
    a = ap.parse_args()
    out = load(Path(a.fhir_dir), Path(a.cms))
    print(json.dumps(out, indent=2))
    if out["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
