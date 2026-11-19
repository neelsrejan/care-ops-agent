"""Selections survive steps that do not draw the widget that owns them.

Streamlit deletes a widget key at the end of a run that did not render that
widget. source, measure, state, and name are those keys on this page.
"""

import os
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

ROOT = Path(__file__).resolve().parents[1]
_FORBIDDEN = ("/home/", "/opt/", "/usr/", "/tmp/", "/var/", "/agent/", "/workspace/", "site-packages")


def _dsn() -> str:
    return os.environ.get("CARE_OPS_PG_DSN", "postgresql://postgres@localhost:5433/care_ops")


def _load_fixture(dsn: str) -> None:
    from care_ops_agent.public.load import load_rows

    note = "Unavailable. Table 7 has counts only."
    hrsa = []
    for measure_id, numerator in (
        ("diabetes_poor_control", 40),
        ("bp_control", 70),
        ("breast_cancer_screening", 60),
    ):
        hrsa.append({
            "reporting_year": 2025,
            "bhcmis_id": "030050",
            "health_center_name": "Cedar Clinic",
            "city": "Dallas",
            "state": "TX",
            "measure_id": measure_id,
            "numerator": numerator,
            "denominator": 100,
            "published_percent": None if measure_id != "breast_cancer_screening" else 60.0,
            "percent_status": "unavailable" if measure_id != "breast_cancer_screening" else "published",
            "percent_note": note if measure_id != "breast_cancer_screening" else "Table 6B published percent.",
        })
    places = []
    for fips, abbr, state, county, measures in (
        ("48453", "TX", "Texas", "Travis", {"diabetes_prevalence": 9.5, "bp_medication": 80.0, "mammography": 74.0}),
        ("01001", "AL", "Alabama", "Autauga", {"diabetes_prevalence": 13.3, "bp_medication": 76.0, "mammography": 68.0}),
    ):
        for measure_id, percent in measures.items():
            places.append({
                "county_fips": fips,
                "state_abbr": abbr,
                "state_name": state,
                "county_name": county,
                "total_population": 1000,
                "pop_18plus": 800,
                "measure_id": measure_id,
                "crude_percent": percent,
                "published_ci_low": None,
                "published_ci_high": None,
            })
    cms = [{
        "contract_id": "H0028",
        "organization_type": "Local CCP",
        "contract_name": "Humana",
        "parent_organization": "Humana Inc.",
        "measure_code": code,
        "measure_id": measure_id,
        "measure_name": measure_id,
        "measurement_period": "01/01/2025 - 12/31/2025",
        "published_percent": 70,
        "status": None,
    } for code, measure_id in (
        ("C01", "breast_cancer_screening"),
        ("C12", "diabetes_blood_sugar_controlled"),
        ("C14", "bp_control"),
    )]
    result = load_rows(
        dsn,
        hrsa=hrsa,
        places=places,
        cms=cms,
        hashes={"hrsa_uds": "apptest", "cdc_places": "apptest", "cms_stars": "apptest"},
    )
    assert result["failed"] == []


def _visible(app) -> str:
    chunks = []
    for name in ("markdown", "text", "caption", "error", "warning", "info", "subheader", "header", "title"):
        for item in getattr(app, name, []):
            chunks.append(str(getattr(item, "value", "")))
    return "\n".join(chunks)


def _run(app):
    app.run()
    assert not app.exception, app.exception
    return app


def _click(app, label: str):
    next(item for item in app.button if item.label == label).click()
    return _run(app)


def _box(app, label: str):
    return next(item for item in app.selectbox if item.label == label)


def test_choices_persist_across_steps_and_free_explore(monkeypatch):
    """A non-default source, measure, state, and name survive two steps and Free explore."""
    from streamlit.testing.v1 import AppTest

    dsn = _dsn()
    monkeypatch.setenv("CARE_OPS_ALLOW_LOCAL", "1")
    monkeypatch.setenv("CARE_OPS_PG_DSN", dsn)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    try:
        psycopg.connect(dsn, connect_timeout=3).close()
    except Exception:
        pytest.skip("no local PostgreSQL")
    _load_fixture(dsn)

    app = _run(AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=90))
    toggle = next(item for item in app.toggle if item.label == "Free explore")
    toggle.set_value(True)
    app = _run(app)

    _box(app, "Source").select("cdc_places")
    app = _run(app)
    _box(app, "Measure").select("mammography")
    app = _run(app)
    _box(app, "State").select("TX")
    app = _run(app)
    next(item for item in app.text_input if item.label == "Name contains").set_value("Travis")
    app = _run(app)

    assert app.session_state["source_id"] == "cdc_places"
    assert app.session_state["measure_id"] == "mammography"
    assert app.session_state["slice_state"] == "TX"
    assert app.session_state["slice_search"] == "Travis"

    toggle = next(item for item in app.toggle if item.label == "Free explore")
    toggle.set_value(False)
    app = _run(app)
    app = _click(app, "Next")
    app = _click(app, "Next")

    assert "Step 3 of 7" in _visible(app)
    assert app.session_state["source_id"] == "cdc_places"
    assert app.session_state["measure_id"] == "mammography"
    assert app.session_state["slice_state"] == "TX"
    assert app.session_state["slice_search"] == "Travis"
    assert "Mammography among women 50–74" in _visible(app)

    toggle = next(item for item in app.toggle if item.label == "Free explore")
    toggle.set_value(True)
    app = _run(app)
    assert _box(app, "Source").value == "cdc_places"
    assert _box(app, "Measure").value == "mammography"
    assert _box(app, "State").value == "TX"
    assert next(item for item in app.text_input if item.label == "Name contains").value == "Travis"

    toggle = next(item for item in app.toggle if item.label == "Free explore")
    toggle.set_value(False)
    app = _run(app)
    assert app.session_state["source_id"] == "cdc_places"
    assert app.session_state["measure_id"] == "mammography"
    assert app.session_state["slice_state"] == "TX"
    assert app.session_state["slice_search"] == "Travis"
    shown = _visible(app)
    for needle in _FORBIDDEN:
        assert needle not in shown
