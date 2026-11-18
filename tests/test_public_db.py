import os

import pytest

psycopg = pytest.importorskip("psycopg")

from care_ops_agent.public.load import load_rows
from care_ops_agent.public.query import build_view


def _dsn() -> str:
    return os.environ.get("CARE_OPS_PG_DSN", "postgresql://postgres@localhost:5433/care_ops")


def test_published_schema_roundtrip(monkeypatch):
    monkeypatch.setenv("CARE_OPS_ALLOW_LOCAL", "1")
    monkeypatch.setenv("CARE_OPS_PG_DSN", _dsn())
    try:
        psycopg.connect(_dsn(), connect_timeout=3).close()
    except Exception:
        pytest.skip("no local PostgreSQL")
    result = load_rows(
        _dsn(),
        hrsa=[{
            "reporting_year": 2025,
            "bhcmis_id": "010030",
            "health_center_name": "Holyoke Health Center",
            "city": "Holyoke",
            "state": "MA",
            "measure_id": "breast_cancer_screening",
            "numerator": 1565,
            "denominator": 2187,
            "published_percent": 71.56,
            "percent_status": "published",
            "percent_note": "Table 6B published percent.",
        }, {
            "reporting_year": 2025,
            "bhcmis_id": "010030",
            "health_center_name": "Holyoke Health Center",
            "city": "Holyoke",
            "state": "MA",
            "measure_id": "bp_control",
            "numerator": 2817,
            "denominator": 4741,
            "published_percent": None,
            "percent_status": "unavailable",
            "percent_note": "Unavailable. Table 7 has counts only.",
        }],
        places=[{
            "county_fips": "01001",
            "state_abbr": "AL",
            "state_name": "Alabama",
            "county_name": "Autauga",
            "total_population": 58805,
            "pop_18plus": 45143,
            "measure_id": "diabetes_prevalence",
            "crude_percent": 13.3,
            "published_ci_low": 11.4,
            "published_ci_high": 15.3,
        }],
        cms=[{
            "contract_id": "H0028",
            "organization_type": "Local CCP",
            "contract_name": "Humana",
            "parent_organization": "Humana Inc.",
            "measure_code": "C01",
            "measure_id": "breast_cancer_screening",
            "measure_name": "Breast Cancer Screening",
            "measurement_period": "01/01/2025 – 12/31/2025",
            "published_percent": 77,
            "status": None,
        }],
        hashes={"hrsa_uds": "fixture", "cdc_places": "fixture", "cms_stars": "fixture"},
    )
    assert result["failed"] == []
    with psycopg.connect(_dsn(), autocommit=True) as con:
        view = build_view(con, "hrsa_uds", "breast_cancer_screening")
    assert view["summary"]["pooled_numerator"] == 1565
    assert view["note"]["fidelity"]["ok"]
    assert abs(view["rows"][0]["rate"] * 100 - 71.56) < 0.02
