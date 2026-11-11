"""Salesforce client boundary.

The default backend is the local CRM in ``crm/mock.py``. CSV files from
``export_salesforce_csv`` are what a Salesforce Data Import Wizard would load
later. ``SALESFORCE_BACKEND=live`` requires credentials from the environment
and is not called by the demo or the tests.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from care_ops_agent.crm.mock import export_salesforce_csv

LOGIN_URL = "https://login.salesforce.com"


class SalesforceNotConfigured(RuntimeError):
    """Live Salesforce was requested and the environment does not have the credentials."""


class OfflineSalesforceClient:
    def __init__(self, crm: dict[str, list[dict[str, Any]]]):
        self.crm = crm

    def records(self, object_name: str) -> list[dict[str, Any]]:
        if object_name not in self.crm:
            raise KeyError(object_name)
        return list(self.crm[object_name])

    def export_csv(self, folder: Path) -> list[Path]:
        return export_salesforce_csv(self.crm, folder)


class LiveSalesforceClient:
    """OAuth password grant against a Developer Edition org. Not used unless configured."""

    def __init__(self, username: str, password: str, security_token: str,
                 client_id: str, client_secret: str, login_url: str = LOGIN_URL):
        missing = [
            name for name, value in (
                ("SF_USERNAME", username),
                ("SF_PASSWORD", password),
                ("SF_SECURITY_TOKEN", security_token),
                ("SF_CLIENT_ID", client_id),
                ("SF_CLIENT_SECRET", client_secret),
            ) if not value
        ]
        if missing:
            raise SalesforceNotConfigured("missing " + ", ".join(missing))
        self.username = username
        self.password = password
        self.security_token = security_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_url = login_url.rstrip("/")
        self.instance_url = ""
        self._access_token = ""

    def login(self) -> dict[str, str]:
        import httpx

        response = httpx.post(
            f"{self.login_url}/services/oauth2/token",
            data={
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password + self.security_token,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        body = response.json()
        self.instance_url = body["instance_url"]
        self._access_token = body["access_token"]
        return {"instance_url": self.instance_url}

    def query(self, soql: str) -> dict[str, Any]:
        import httpx

        if not self._access_token:
            self.login()
        response = httpx.get(
            f"{self.instance_url}/services/data/v60.0/query",
            params={"q": soql},
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


def salesforce_client_from_env(crm: dict[str, list[dict[str, Any]]]) -> OfflineSalesforceClient | LiveSalesforceClient:
    backend = os.environ.get("SALESFORCE_BACKEND", "offline").strip().lower()
    if backend in {"", "offline", "fake", "local"}:
        return OfflineSalesforceClient(crm)
    if backend != "live":
        raise SalesforceNotConfigured(f"SALESFORCE_BACKEND must be offline or live, got {backend!r}")
    return LiveSalesforceClient(
        username=os.environ.get("SF_USERNAME", "").strip(),
        password=os.environ.get("SF_PASSWORD", "").strip(),
        security_token=os.environ.get("SF_SECURITY_TOKEN", "").strip(),
        client_id=os.environ.get("SF_CLIENT_ID", "").strip(),
        client_secret=os.environ.get("SF_CLIENT_SECRET", "").strip(),
        login_url=os.environ.get("SF_LOGIN_URL", LOGIN_URL).strip() or LOGIN_URL,
    )
