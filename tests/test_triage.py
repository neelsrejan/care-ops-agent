from pathlib import Path

import pytest

from care_ops_agent.nodes.triage import memo
from care_ops_agent.sim.network import build_network, load_scenario, simulate_results

ROOT = Path(__file__).resolve().parents[1]
SEEDS = {  # tiny stand-in for the Postgres views so the test runs without a database
    "partners": [{"facility_id": f"F{i}", "facility_name": f"SEED FACILITY {i}", "city": "CITY"} for i in range(12)],
    "roster": {"hba1c_control": [f"a{i}" for i in range(50)], "bp_control": [f"b{i}" for i in range(50)],
               "breast_cancer_screening": [f"c{i}" for i in range(50)]},
}


@pytest.mark.parametrize("name", ["clinic_bp_drop", "missing_a1c_feed", "partner_screening_gap", "no_signal"])
def test_scenarios_recover_truth(name):
    sc = load_scenario(ROOT / "scenarios" / f"{name}.yaml")
    net = build_network(sc, SEEDS)
    out = memo(simulate_results(sc, net), sc, net["partners"])
    truth, v = sc["truth"], out["verdict"]
    assert out["fidelity"]["ok"]
    assert v["kind"] == truth["kind"]
    if truth["kind"] != "none":
        assert v["partner_id"] == f"P{truth['partner_index'] + 1}" and v["measure"] == truth["measure"]
        if truth.get("clinic"):
            assert v["clinic"] == truth["clinic"]


def test_results_labeled_synthetic():
    sc = load_scenario(ROOT / "scenarios" / "no_signal.yaml")
    df = simulate_results(sc, build_network(sc, SEEDS))
    assert df.attrs["label"] == "SYNTHETIC SIMULATION"
