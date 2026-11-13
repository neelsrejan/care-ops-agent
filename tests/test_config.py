from care_ops_agent.config import MEASURE_TARGETS, load_settings


def test_defaults_rules_only(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    s = load_settings()
    assert s.rules_only


def test_aliases(monkeypatch):
    for alias in ("offline", "rules", "mock"):
        monkeypatch.setenv("LLM_BACKEND", alias)
        assert load_settings().rules_only


def test_repr_has_no_paths_or_secrets(monkeypatch):
    s = load_settings()
    assert "repo_root" not in repr(s)


def test_measures():
    assert set(MEASURE_TARGETS) == {"hba1c_control", "bp_control", "breast_cancer_screening"}
