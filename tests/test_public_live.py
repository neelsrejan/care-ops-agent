"""Checks against the real downloaded files. Skipped unless CARE_OPS_PUBLIC_DIR is set."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from care_ops_agent.public.gaps import care_gaps
from care_ops_agent.public.parse import parse_cms_zip, parse_hrsa_xlsx, parse_places_csv

pytestmark = pytest.mark.skipif(
    not os.environ.get("CARE_OPS_PUBLIC_DIR"),
    reason="set CARE_OPS_PUBLIC_DIR to a folder with the three downloaded files",
)


def _folder() -> Path:
    return Path(os.environ["CARE_OPS_PUBLIC_DIR"])


def test_places_file_matches_the_published_county_count():
    rows = parse_places_csv(_folder() / "places_county_2025.csv")
    autauga = next(row for row in rows if row["county_fips"] == "01001" and row["measure_id"] == "diabetes_prevalence")
    assert autauga["crude_percent"] == 13.3
    assert sum(1 for row in rows if row["measure_id"] == "diabetes_prevalence") >= 3000


def test_cms_file_keeps_the_published_h0028_rate():
    rows = parse_cms_zip(_folder() / "cms_star_ratings.zip")
    humana = next(row for row in rows if row["contract_id"] == "H0028" and row["measure_code"] == "C01")
    assert humana["published_percent"] == 77
    reporting = [row for row in rows if row["measure_code"] == "C12" and row["published_percent"] is not None]
    assert len(reporting) > 100


def test_hrsa_holyoke_mammogram_matches_the_published_percent():
    rows = parse_hrsa_xlsx(_folder() / "H80-2025.xlsx")
    holyoke = next(
        row for row in rows
        if row["bhcmis_id"] == "010030" and row["measure_id"] == "breast_cancer_screening"
    )
    assert holyoke["numerator"] == 1565
    assert holyoke["denominator"] == 2187
    assert holyoke["published_percent"] == 71.56
    assert abs(holyoke["numerator"] / holyoke["denominator"] * 100 - 71.56) < 0.02
    bp = next(row for row in rows if row["bhcmis_id"] == "010030" and row["measure_id"] == "bp_control")
    assert bp["numerator"] == 2817
    assert bp["denominator"] == 4741
    assert bp["published_percent"] is None
    assert bp["percent_status"] == "unavailable"
    assert "no center-total percent" in bp["percent_note"]
    poor = next(row for row in rows if row["bhcmis_id"] == "010030" and row["measure_id"] == "diabetes_poor_control")
    assert poor["numerator"] == 433
    assert poor["denominator"] == 2282
    assert poor["percent_status"] == "unavailable"
    assert holyoke["percent_status"] == "published"


def test_hrsa_national_rates_are_in_a_plausible_band():
    rows = parse_hrsa_xlsx(_folder() / "H80-2025.xlsx")
    for measure_id, low, high in (
        ("bp_control", 0.45, 0.85),
        ("breast_cancer_screening", 0.30, 0.85),
        ("diabetes_poor_control", 0.05, 0.50),
    ):
        subset = [
            {"entity_id": row["bhcmis_id"], "entity_name": row["health_center_name"],
             "numerator": row["numerator"], "denominator": row["denominator"]}
            for row in rows if row["measure_id"] == measure_id
        ]
        summary = care_gaps(subset, direction="higher_better", mode="counts")["summary"]
        assert low < summary["comparator"] < high, measure_id
