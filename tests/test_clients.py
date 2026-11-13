import pytest

from care_ops_agent.crm.client import SalesforceNotConfigured, salesforce_client_from_env
from care_ops_agent.crm.mock import build_crm
from care_ops_agent.fhir.hapi import upload_bundle
from care_ops_agent.pm.asana import AsanaNotConfigured, OfflineAsanaClient, asana_client_from_env


def test_asana_default_is_offline_and_does_not_call_httpx(tmp_path, monkeypatch):
    monkeypatch.delenv("ASANA_BACKEND", raising=False)
    monkeypatch.delenv("ASANA_ACCESS_TOKEN", raising=False)

    def boom(*_a, **_k):
        raise AssertionError("offline Asana must not call httpx")

    monkeypatch.setattr("httpx.post", boom)
    client = asana_client_from_env(tmp_path)
    assert isinstance(client, OfflineAsanaClient)
    saved = client.create_tasks([
        {"name": "Write the charter", "notes": "SYNTHETIC", "section": "Charter", "due_on": "2026-11-06"},
    ])
    assert saved[0]["gid"] == "SIM-0001"
    text = (tmp_path / "asana_import.csv").read_text()
    assert "Write the charter" in text and "SYNTHETIC" in text


def test_asana_live_requires_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ASANA_BACKEND", "live")
    monkeypatch.delenv("ASANA_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ASANA_WORKSPACE_GID", raising=False)
    with pytest.raises(AsanaNotConfigured):
        asana_client_from_env(tmp_path)


def test_salesforce_live_requires_env(monkeypatch):
    monkeypatch.setenv("SALESFORCE_BACKEND", "live")
    for name in ("SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN", "SF_CLIENT_ID", "SF_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(SalesforceNotConfigured):
        salesforce_client_from_env({"Account": []})


def test_salesforce_offline_exports(tmp_path, monkeypatch):
    monkeypatch.delenv("SALESFORCE_BACKEND", raising=False)
    from datetime import date

    crm = build_crm([{"partner_id": "P1", "name": "P1 (SYNTHETIC)", "city": "X"}], 1, date(2026, 11, 3), n_prospects=1)
    client = salesforce_client_from_env(crm)
    paths = client.export_csv(tmp_path)
    assert {path.name for path in paths} == {"Account.csv", "Contact.csv", "Opportunity.csv", "StageHistory.csv"}


def test_hapi_upload_is_blocked(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("upload must not open a socket")

    monkeypatch.setattr("httpx.post", boom)
    blocked = upload_bundle({"entry": [{}, {}]}, allow_write=True)
    assert blocked["mode"] == "blocked"
    assert blocked["entries"] == 2
