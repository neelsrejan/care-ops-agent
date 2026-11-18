import pytest
from pathlib import Path

from care_ops_agent.public.gaps import care_gaps, rate_from_counts
from care_ops_agent.public.narrate import public_note
from care_ops_agent.public.parse import parse_cms_measure_file, parse_places_csv

FIXTURES = Path(__file__).parent / "fixtures" / "public"


def test_counts_pool_and_wilson():
    result = care_gaps(
        [
            {"entity_id": "a", "entity_name": "A", "numerator": 1565, "denominator": 2187},
            {"entity_id": "b", "entity_name": "B", "numerator": 18, "denominator": 66},
        ],
        direction="higher_better",
        mode="counts",
    )
    summary = result["summary"]
    assert summary["pooled_numerator"] == 1583
    assert summary["pooled_denominator"] == 2253
    assert summary["comparator"] == 1583 / 2253
    holyoke = next(row for row in result["rows"] if row["entity_id"] == "a")
    assert holyoke["rate"] == 1565 / 2187
    assert holyoke["ci_low"] is not None and holyoke["ci_low"] < holyoke["rate"] < holyoke["ci_high"]
    # 18/66 is well below the pool, so it is the worse gap.
    assert result["rows"][0]["entity_id"] == "b"
    assert result["rows"][0]["worse"] is True


def test_published_percent_is_not_treated_as_a_count():
    result = care_gaps(
        [
            {"entity_id": "H0028", "entity_name": "Humana", "percent": 77},
            {"entity_id": "H0104", "entity_name": "Alabama", "percent": 79},
            {"entity_id": "H0062", "entity_name": "Small", "percent": None, "status": "Plan too small to be measured"},
        ],
        direction="higher_better",
        mode="percent",
    )
    assert result["summary"]["n_with_rate"] == 2
    assert result["summary"]["comparator"] == 0.78
    assert result["summary"]["ci_low"] is None
    worse = next(row for row in result["rows"] if row["entity_id"] == "H0028")
    assert worse["gap_pp"] == (0.78 - 0.77) * 100


def test_places_weight_uses_adult_population():
    result = care_gaps(
        [
            {"entity_id": "01001", "entity_name": "Autauga", "percent": 13.3, "weight": 100},
            {"entity_id": "01011", "entity_name": "Bullock", "percent": 24.6, "weight": 300},
        ],
        direction="lower_better",
        mode="weighted_percent",
    )
    expected = (0.133 * 100 + 0.246 * 300) / 400
    assert result["summary"]["comparator"] == pytest.approx(expected)
    bullock = next(row for row in result["rows"] if row["entity_id"] == "01011")
    assert bullock["gap_pp"] > 0


def test_note_uses_only_computed_numbers():
    result = care_gaps(
        [{"entity_id": "010030", "entity_name": "Holyoke Health Center", "numerator": 1565, "denominator": 2187}],
        direction="higher_better",
        mode="counts",
    )
    note = public_note(result, {
        "source_label": "HRSA UDS health centers",
        "measure_label": "Breast cancer screening (mammogram, women 52–74)",
        "caveat": "Counts come from the health-center total columns.",
        "year": 2025,
    })
    assert note["fidelity"]["ok"]
    assert "1565" in note["text"]
    assert "synthetic" not in note["text"].lower()


def test_places_fixture_keeps_real_autauga_value():
    rows = parse_places_csv(FIXTURES / "places_sample.csv")
    autauga = next(row for row in rows if row["county_fips"] == "01001" and row["measure_id"] == "diabetes_prevalence")
    assert autauga["crude_percent"] == 13.3
    assert autauga["published_ci_low"] == 11.4
    assert autauga["pop_18plus"] == 46253
    assert len(rows) == 6


def test_cms_fixture_keeps_real_h0028_percents():
    rows = parse_cms_measure_file(FIXTURES / "cms_measure_sample.csv")
    humana = {(row["measure_code"]): row for row in rows if row["contract_id"] == "H0028"}
    assert humana["C01"]["published_percent"] == 77
    assert humana["C12"]["published_percent"] == 93
    assert humana["C14"]["published_percent"] == 87
    small = next(row for row in rows if row["contract_id"] == "H0099" and row["measure_code"] == "C01")
    assert small["published_percent"] is None
    assert "too small" in small["status"]


def test_fractional_numerator_is_rounded_in_the_note():
    result = care_gaps(
        [{"entity_id": "x", "entity_name": "Center", "numerator": 10.2, "denominator": 40}],
        direction="higher_better",
        mode="counts",
    )
    note = public_note(result, {
        "source_label": "HRSA UDS health centers",
        "measure_label": "Breast cancer screening",
        "caveat": "A fractional numerator is a weighted estimate.",
        "year": 2025,
    })
    assert note["fidelity"]["ok"]
    assert "10 of 40" in note["text"]
    assert "10.2" not in note["text"]


def test_rate_rejects_a_numerator_past_the_denominator():
    assert rate_from_counts(11, 10) is None
