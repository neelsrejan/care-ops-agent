from care_ops_agent.experiment.ab import (
    EFFECT_P_A,
    EFFECT_P_B,
    NULL_P,
    effect_recovered,
    null_quiet,
    run_trial,
    sample_size_per_arm,
)
from care_ops_agent.pdsa.audience import AUDIENCES, render_updates
from care_ops_agent.pdsa.cycle import run_pdsa
from care_ops_agent.rfp.library import answer_all, questions
from care_ops_agent.sim.fixtures import demo_seeds
from care_ops_agent.sim.network import build_network, load_scenario, simulate_results

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pdsa_and_partner_filter_on_the_program_story():
    scenario = load_scenario(ROOT / "scenarios" / "program_story.yaml")
    network = build_network(scenario, demo_seeds())
    results = simulate_results(scenario, network)
    cycles = run_pdsa(scenario, results)
    assert len(cycles) == scenario["weeks"] - scenario["program_start_week"] + 1
    assert all(row["fidelity_ok"] for row in cycles)
    assert any(row["act"] == "adapt" for row in cycles)
    from datetime import date

    from care_ops_agent.crm.mock import apply_pipeline_stall, build_crm
    from care_ops_agent.metrics.pipeline import open_gaps_by_partner, readiness_view
    from care_ops_agent.nodes.triage import analyze

    as_of = date(2026, 11, 3)
    crm = apply_pipeline_stall(build_crm(network["partners"], scenario["seed"], as_of), scenario, as_of)
    ready = readiness_view(crm["Opportunity"], as_of, open_gaps_by_partner(results))
    stalled = [row["AccountId"] for row in ready if row["stalled"]]
    assert "P3" in stalled
    updates = render_updates(
        scenario, network["partners"], analyze(results, scenario["program_start_week"]), results, ready,
        {"baseline_cost": 1000, "forecast_cost": 1400},
    )
    assert updates["steering"]["fidelity"]["ok"]
    assert all(not leaks for leaks in updates["leaks"].values())
    assert AUDIENCES["partner"]["other_partners"] is False
    assert AUDIENCES["steering"]["budget"] is True
    assert "1000" in updates["internal"]["text"]
    assert "1000" not in updates["partners"]["P1"]["text"]


def test_two_injections_are_both_visible():
    scenario = load_scenario(ROOT / "scenarios" / "program_story.yaml")
    network = build_network(scenario, demo_seeds())
    from care_ops_agent.nodes.triage import analyze

    flagged = analyze(simulate_results(scenario, network), scenario["program_start_week"])["flagged"]
    keys = {(cell["partner_id"], cell["measure"], cell["kind"]) for cell in flagged}
    assert ("P4", "bp_control", "care_gap") in keys
    assert ("P6", "hba1c_control", "data_issue") in keys
    assert ("P2", "breast_cancer_screening", "care_gap") in keys


def test_ab_power_recovers_effect_and_reports_null():
    n = sample_size_per_arm(EFFECT_P_A, EFFECT_P_B)
    assert n > 20
    effect = [run_trial(seed, EFFECT_P_A, EFFECT_P_B, n_per_arm=n) for seed in range(20)]
    nulls = [run_trial(seed, NULL_P, NULL_P, n_per_arm=n) for seed in range(100, 130)]
    assert sum(effect_recovered(trial) for trial in effect) / len(effect) >= 0.8
    assert sum(null_quiet(trial) for trial in nulls) / len(nulls) >= 0.8
    primary = run_trial(17, EFFECT_P_A, EFFECT_P_B, n_per_arm=n)
    assert primary["decision"] == "scale_b"
    assert primary["assigned_a"] == primary["assigned_b"] == n


def test_rfp_library_cites_or_flags():
    rows = answer_all()
    assert len(rows) == 40
    assert len(questions()) == 40
    missed = [row["id"] for row in rows if not row["correct"]]
    assert not missed
    cited = [row for row in rows if row["status"] == "cited"]
    assert cited and all(row["cites"] for row in cited)
