"""The guided flow is data, not a Streamlit session."""

import pytest

from care_ops_agent.public import catalog
from care_ops_agent.public.gaps import care_gaps
from care_ops_agent.public.walkthrough import (
    CHART_LIMIT,
    DEFAULT_FOCUS,
    DEFAULT_SOURCE,
    FOCUSES,
    SOURCE_ORDER,
    STEPS,
    direction_sentence,
    filter_rows,
    guide_copy,
    measure_for,
    prompts_for,
    recommendation_note,
    state_options,
    step_index,
    table_records,
    widest_rows,
    worse_states,
)

DEFINITION = {
    "source_label": "HRSA UDS health centers",
    "measure_label": "Diabetes poor glycemic status (>9% or missing)",
    "caveat": "Diabetes counts poor glycemic status or a missing test, so a higher rate is a wider gap.",
    "year": 2025,
}


def _diabetes_rows():
    result = care_gaps(
        [
            {"entity_id": "a", "entity_name": "Alpha Clinic", "state": "MA", "numerator": 20, "denominator": 100},
            {"entity_id": "b", "entity_name": "Bravo Clinic", "state": "TX", "numerator": 50, "denominator": 100},
            {"entity_id": "c", "entity_name": "Cedar Clinic", "state": "TX", "numerator": 55, "denominator": 100},
            {"entity_id": "d", "entity_name": "Delta Clinic", "state": "IL", "numerator": 25, "denominator": 80},
        ],
        direction="lower_better",
        mode="counts",
    )
    return result


def test_walkthrough_is_seven_steps_from_brief_to_recommendation():
    assert [step.id for step in STEPS] == [
        "brief",
        "file",
        "national",
        "gaps",
        "slice",
        "check",
        "outcome",
    ]
    assert step_index("brief") == 0
    assert step_index("outcome") == len(STEPS) - 1
    assert len(STEPS) == 7


def test_every_focus_maps_onto_a_real_measure():
    assert DEFAULT_FOCUS in FOCUSES
    assert DEFAULT_SOURCE == "hrsa_uds"
    for focus_id, focus in FOCUSES.items():
        assert set(focus["measures"]) == set(SOURCE_ORDER)
        for source_id, measure_id in focus["measures"].items():
            assert measure_id in catalog.MEASURES[source_id]
            assert measure_for(focus_id, source_id) == measure_id
            copy = guide_copy("national", focus_id, source_id)
            assert copy["doing"] and copy["why"] and copy["look"]


def test_every_step_says_what_the_agent_is_doing():
    for step in STEPS:
        copy = guide_copy(step.id, "screening", "cms_stars")
        assert "agent" in copy["doing"].lower()
        assert copy["why"]
        assert copy["look"]
        assert prompts_for(step.id, focus_id="screening", source_id="cms_stars", rows=[])


def test_guide_copy_follows_the_measure_on_screen():
    national = guide_copy("national", "diabetes", "cdc_places", "mammography")
    assert "Mammography among women 50–74" in national["doing"]
    assert "higher rate is better" in national["look"]


def test_diabetes_hrsa_tells_the_visitor_a_higher_rate_is_worse():
    sentence = direction_sentence("hrsa_uds", "diabetes_poor_control")
    assert "higher rate is worse" in sentence
    cms = direction_sentence("cms_stars", "diabetes_blood_sugar_controlled")
    assert "higher rate is better" in cms
    national = guide_copy("national", "diabetes", "hrsa_uds")
    assert "higher rate is worse" in national["look"]


def test_brief_and_file_prompts_cover_every_choice():
    brief = prompts_for("brief", focus_id="diabetes", source_id="hrsa_uds")
    assert [item.focus_id for item in brief] == list(FOCUSES)
    assert {item.goto for item in brief} == {"file"}
    files = prompts_for("file", focus_id="diabetes", source_id="hrsa_uds")
    assert [item.source_id for item in files] == list(SOURCE_ORDER)
    assert {item.goto for item in files} == {"national"}


def test_gap_prompts_open_the_widest_entity_and_the_worst_states():
    result = _diabetes_rows()
    prompts = prompts_for("gaps", focus_id="diabetes", source_id="hrsa_uds", rows=result["rows"])
    widest = prompts[0]
    assert widest.search == "Cedar Clinic"
    assert widest.state == "All"
    assert widest.goto == "slice"
    states = {item.state: item for item in prompts if item.id.startswith("state-")}
    assert states["TX"].search == ""
    assert "2 worse" in states["TX"].label
    assert "MA" not in states


def test_filter_keeps_gap_order_and_the_chart_is_the_top_slice():
    result = _diabetes_rows()
    rows = result["rows"]
    assert rows[0]["entity_name"] == "Cedar Clinic"
    texas = filter_rows(rows, state="TX", search="")
    assert [row["entity_name"] for row in texas] == ["Cedar Clinic", "Bravo Clinic"]
    named = filter_rows(rows, state="All", search="bravo")
    assert [row["entity_name"] for row in named] == ["Bravo Clinic"]
    assert state_options(rows) == ["All", "IL", "MA", "TX"]
    assert len(widest_rows(rows, limit=2)) == 2
    assert widest_rows(rows)[0]["entity_id"] == "c"
    assert CHART_LIMIT == 15


def test_table_records_match_the_hosted_columns():
    result = _diabetes_rows()
    record = table_records(result["rows"])[0]
    assert list(record) == [
        "name",
        "id",
        "state",
        "rate_percent",
        "gap_pp",
        "numerator",
        "denominator",
        "status",
    ]
    assert record["name"] == "Cedar Clinic"
    assert record["numerator"] == 55
    assert record["rate_percent"] == 55.0


def test_recommendation_uses_only_computed_numbers_and_names_the_worst():
    result = _diabetes_rows()
    note = recommendation_note(result["summary"], result["rows"], DEFINITION)
    assert note["fidelity"]["ok"]
    assert note["backend"] == "deterministic"
    assert "Cedar Clinic" in note["text"]
    assert "TX" in note["text"]
    assert "synthetic" not in note["text"].lower()
    assert "Recommendation: review the" in note["text"]


def test_recommendation_holds_when_nobody_clears_the_threshold():
    result = care_gaps(
        [
            {"entity_id": "a", "entity_name": "Alpha", "state": "MA", "numerator": 50, "denominator": 100},
            {"entity_id": "b", "entity_name": "Bravo", "state": "TX", "numerator": 52, "denominator": 100},
        ],
        direction="higher_better",
        mode="counts",
    )
    assert result["summary"]["n_worse"] == 0
    note = recommendation_note(result["summary"], result["rows"], DEFINITION)
    assert note["fidelity"]["ok"]
    assert "keep watching" in note["text"]
    assert "Bravo" not in note["text"]


def test_blank_cms_state_does_not_become_a_state_button():
    result = care_gaps(
        [
            {"entity_id": "H1", "entity_name": "Wide", "state": "", "percent": 50},
            {"entity_id": "H2", "entity_name": "Narrow", "state": "", "percent": 80},
        ],
        direction="higher_better",
        mode="percent",
    )
    prompts = prompts_for("gaps", focus_id="diabetes", source_id="cms_stars", rows=result["rows"])
    assert prompts[0].search == "Wide"
    assert prompts[0].state == "All"
    assert not any(item.id.startswith("state-") for item in prompts)
    assert worse_states(result["rows"]) == []


def test_unknown_focus_is_rejected():
    with pytest.raises(KeyError):
        measure_for("nope", "hrsa_uds")
