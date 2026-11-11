from care_ops_agent.guards.numeric_fidelity import check_narrative
from care_ops_agent.llm import narrate


def test_accepts_known_and_rejects_planted():
    facts = {"rate": 0.0412, "n": 1200}
    assert check_narrative("Rate 4.12% on 1200 rows.", facts).ok
    bad = check_narrative("Rate 9.9% on 1200 rows.", facts)
    assert not bad.ok and 9.9 in bad.unknown


def test_narrate_rules_only(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "deterministic")
    out = narrate("Gap 12.5%.", {"gap": 0.125})
    assert out["backend"] == "deterministic" and out["fidelity"]["ok"]
