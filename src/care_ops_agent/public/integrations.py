"""Required Asana, Salesforce, and Tableau Public connections.

The hosted demo does not invent a sync. A missing variable raises
PortfolioNotConfigured and names the variable. Values are never included
in the message. Probes are read-only.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from care_ops_agent.public.dsn import redact

ASANA_VARS = ("ASANA_BACKEND", "ASANA_ACCESS_TOKEN", "ASANA_WORKSPACE_GID")
SALESFORCE_VARS = (
    "SALESFORCE_BACKEND",
    "SF_CLIENT_ID",
    "SF_CLIENT_SECRET",
    "SF_USERNAME",
    "SF_PASSWORD",
    "SF_SECURITY_TOKEN",
)
TABLEAU_VAR = "TABLEAU_PUBLIC_URL"
_TABLEAU_HOSTS = {"public.tableau.com"}


class PortfolioNotConfigured(RuntimeError):
    """A required hosted integration was asked to run without its credentials."""


def _set(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _missing(names: tuple[str, ...], *, live_flag: str | None = None) -> list[str]:
    missing = [name for name in names if not _set(name)]
    if live_flag is not None and os.environ.get(live_flag, "").strip().lower() != "live":
        if live_flag not in missing:
            missing.insert(0, live_flag)
    return missing


def credential_gaps() -> dict[str, list[str]]:
    """Systems that are required and not configured. Keys are display names."""
    gaps: dict[str, list[str]] = {}
    asana = _missing(("ASANA_ACCESS_TOKEN", "ASANA_WORKSPACE_GID"), live_flag="ASANA_BACKEND")
    if asana:
        gaps["Asana"] = asana
    salesforce = _missing(
        ("SF_CLIENT_ID", "SF_CLIENT_SECRET", "SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN"),
        live_flag="SALESFORCE_BACKEND",
    )
    if salesforce:
        gaps["Salesforce"] = salesforce
    tableau = _tableau_problem()
    if tableau:
        gaps["Tableau Public"] = [tableau]
    return gaps


def credential_message(gaps: dict[str, list[str]] | None = None) -> str:
    gaps = credential_gaps() if gaps is None else gaps
    if not gaps:
        return ""
    lines = [
        "Asana, Salesforce Developer Edition, and Tableau Public are required for the hosted portfolio. "
        "Nothing is faked. Set these and the demo will show live sync status and the published viz. "
        "Free tiers: Asana personal access token (https://app.asana.com/0/my-apps), "
        "Salesforce Developer Edition (https://developer.salesforce.com/signup), "
        "Tableau Public (https://public.tableau.com)."
    ]
    for name, missing in gaps.items():
        lines.append(f"{name} is not configured. Set {', '.join(missing)}.")
    lines.append("Put the same names in Streamlit secrets. Do not commit the values.")
    return " ".join(lines)


def require_portfolio() -> None:
    gaps = credential_gaps()
    if gaps:
        raise PortfolioNotConfigured(credential_message(gaps))


def _strip_secrets(text: str) -> str:
    redacted = redact(text)
    for name in ("ASANA_ACCESS_TOKEN", "SF_PASSWORD", "SF_SECURITY_TOKEN", "SF_CLIENT_SECRET"):
        value = os.environ.get(name, "").strip()
        if value:
            redacted = redacted.replace(value, "[redacted]")
    return redacted


def _tableau_problem() -> str:
    """Empty string when the URL is a Tableau Public https link."""
    raw = os.environ.get(TABLEAU_VAR, "").strip()
    if not raw:
        return TABLEAU_VAR
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in _TABLEAU_HOSTS:
        return TABLEAU_VAR
    return ""


def tableau_url() -> str:
    if _tableau_problem():
        raise PortfolioNotConfigured(credential_message({"Tableau Public": [TABLEAU_VAR]}))
    return os.environ[TABLEAU_VAR].strip()


def asana_status() -> dict[str, Any]:
    """Read the Care-gap work plan. Does not create a project or a task."""
    missing = _missing(("ASANA_ACCESS_TOKEN", "ASANA_WORKSPACE_GID"), live_flag="ASANA_BACKEND")
    if missing:
        raise PortfolioNotConfigured(credential_message({"Asana": missing}))
    from care_ops_agent.pm.asana import LiveAsanaClient, read_plan

    client = LiveAsanaClient(
        os.environ["ASANA_ACCESS_TOKEN"].strip(),
        os.environ["ASANA_WORKSPACE_GID"].strip(),
    )
    try:
        status = read_plan(client)
    except Exception as exc:
        return {"system": "Asana", "ok": False, "summary": _strip_secrets(str(exc)), "url": "", "tasks": []}
    status["system"] = "Asana"
    return status


def salesforce_status() -> dict[str, Any]:
    """Log in and count Account rows. Does not write."""
    missing = _missing(
        ("SF_CLIENT_ID", "SF_CLIENT_SECRET", "SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN"),
        live_flag="SALESFORCE_BACKEND",
    )
    if missing:
        raise PortfolioNotConfigured(credential_message({"Salesforce": missing}))
    from care_ops_agent.crm.client import LiveSalesforceClient

    client = LiveSalesforceClient(
        username=os.environ["SF_USERNAME"].strip(),
        password=os.environ["SF_PASSWORD"].strip(),
        security_token=os.environ["SF_SECURITY_TOKEN"].strip(),
        client_id=os.environ["SF_CLIENT_ID"].strip(),
        client_secret=os.environ["SF_CLIENT_SECRET"].strip(),
        login_url=os.environ.get("SF_LOGIN_URL", "https://login.salesforce.com").strip()
        or "https://login.salesforce.com",
    )
    try:
        client.login()
        counted = client.query("SELECT COUNT() FROM Account")
        total = int(counted.get("totalSize") or 0)
    except Exception as exc:
        return {"system": "Salesforce", "ok": False, "summary": _strip_secrets(str(exc)), "url": ""}
    host = urlparse(client.instance_url).hostname or "the org"
    return {
        "system": "Salesforce",
        "ok": True,
        "summary": f"Salesforce is connected. Org host {host}. Account records: {total}.",
        "url": client.instance_url,
        "link_label": "Open the Salesforce org",
    }


def tableau_status() -> dict[str, Any]:
    url = tableau_url()
    return {
        "system": "Tableau Public",
        "ok": True,
        "summary": "Tableau Public viz is configured.",
        "url": url,
        "link_label": "Open the Tableau Public viz",
    }


def live_status() -> list[dict[str, Any]]:
    """Probe each required system that is already configured."""
    gaps = credential_gaps()
    probes = []
    if "Asana" not in gaps:
        probes.append(asana_status())
    if "Salesforce" not in gaps:
        probes.append(salesforce_status())
    if "Tableau Public" not in gaps:
        probes.append(tableau_status())
    return probes
