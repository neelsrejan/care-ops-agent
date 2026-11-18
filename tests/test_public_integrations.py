import pytest

from care_ops_agent.config import find_repo_root
from care_ops_agent.public.baselines import PROGRAM_BASELINE
from care_ops_agent.public.integrations import (
    PortfolioNotConfigured,
    asana_status,
    credential_gaps,
    credential_message,
    tableau_url,
)
from care_ops_agent.public.status import blocking_gaps, checklist
from care_ops_agent.sim.network import load_scenario


def test_hosted_tools_are_required(monkeypatch):
    for name in (
        "ASANA_BACKEND", "ASANA_ACCESS_TOKEN", "ASANA_WORKSPACE_GID",
        "SALESFORCE_BACKEND", "SF_CLIENT_ID", "SF_CLIENT_SECRET", "SF_USERNAME",
        "SF_PASSWORD", "SF_SECURITY_TOKEN", "TABLEAU_PUBLIC_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    rows = {item["name"]: item for item in checklist()}
    for name in ("Asana", "Salesforce", "Tableau Public"):
        assert rows[name]["required"] == "yes"
        assert rows[name]["ready"] == "no"
    assert set(blocking_gaps()) >= {"Asana", "Salesforce", "Tableau Public"}
    message = credential_message()
    assert "ASANA_ACCESS_TOKEN" in message
    assert "SF_PASSWORD" in message
    assert "TABLEAU_PUBLIC_URL" in message
    assert "not optional" not in message.lower()
    assert "required" in message.lower()


def test_message_does_not_echo_a_token(monkeypatch):
    monkeypatch.setenv("ASANA_BACKEND", "offline")
    monkeypatch.setenv("ASANA_ACCESS_TOKEN", "secret-asana-token")
    monkeypatch.delenv("ASANA_WORKSPACE_GID", raising=False)
    monkeypatch.delenv("TABLEAU_PUBLIC_URL", raising=False)
    message = credential_message()
    assert "secret-asana-token" not in message


def test_tableau_rejects_a_non_public_host(monkeypatch):
    monkeypatch.setenv("TABLEAU_PUBLIC_URL", "https://example.com/views/demo")
    assert "Tableau Public" in credential_gaps()
    with pytest.raises(PortfolioNotConfigured):
        tableau_url()
    monkeypatch.setenv("TABLEAU_PUBLIC_URL", "https://public.tableau.com/app/profile/demo/viz/CareGaps")
    assert "Tableau Public" not in credential_gaps()
    assert tableau_url().startswith("https://public.tableau.com/")


def test_asana_status_raises_until_configured(monkeypatch):
    monkeypatch.delenv("ASANA_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ASANA_WORKSPACE_GID", raising=False)
    monkeypatch.setenv("ASANA_BACKEND", "live")
    with pytest.raises(PortfolioNotConfigured, match="ASANA_ACCESS_TOKEN"):
        asana_status()


def test_asana_probe_is_read_only_and_hides_the_token(monkeypatch):
    monkeypatch.setenv("ASANA_BACKEND", "live")
    monkeypatch.setenv("ASANA_ACCESS_TOKEN", "secret-asana-token")
    monkeypatch.setenv("ASANA_WORKSPACE_GID", "123")
    calls = []

    class Response:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append((url, headers["Authorization"], params))
        if url.endswith("/workspaces/123"):
            return Response({"data": {"name": "Care Ops"}})
        return Response({"data": [{"name": "Weekly"}]})

    monkeypatch.setattr("httpx.get", fake_get)
    status = asana_status()
    assert status["ok"] is True
    assert "Care Ops" in status["summary"]
    assert "secret-asana-token" not in status["summary"]
    assert calls[0][1] == "Bearer secret-asana-token"
    assert all("post" not in url for url, _, _ in calls)


def test_program_story_uses_the_hrsa_baselines():
    scenario = load_scenario(find_repo_root() / "scenarios" / "program_story.yaml")
    assert scenario["baseline_met"]["bp_control"] == PROGRAM_BASELINE["bp_control"] == 0.69
    assert scenario["baseline_met"]["breast_cancer_screening"] == 0.56
    assert scenario["baseline_met"]["hba1c_control"] == 0.62
