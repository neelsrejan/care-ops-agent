"""Which connections exist. Prints names of variables, never their values."""

from __future__ import annotations

import os
import sys

from care_ops_agent.public.integrations import credential_gaps


def _set(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def checklist() -> list[dict[str, str]]:
    """Ordered owner steps. Every row is required. `ready` is yes, no, or not visible here."""
    hosted = _set("CARE_OPS_PG_DSN") or _set("DATABASE_URL")
    gaps = credential_gaps()
    return [
        {
            "step": "1",
            "name": "Neon Postgres",
            "required": "yes",
            "ready": "yes" if hosted else "no",
            "detail": (
                "REQUIRED. Set CARE_OPS_PG_DSN (or DATABASE_URL) to the Neon connection string. "
                "Free plan, no credit card: https://neon.com (Project, then Connect). "
                "Then run: python -m care_ops_agent.public.load"
            ),
        },
        {
            "step": "2",
            "name": "Streamlit Community Cloud",
            "required": "yes",
            "ready": "not visible here",
            "detail": (
                "REQUIRED. This process cannot see a Streamlit login. Deploy streamlit_app.py "
                "from the public GitHub repo at https://share.streamlit.io. Put every secret "
                "named below in the app secrets, and share the app as public. Viewing is free."
            ),
        },
        {
            "step": "3",
            "name": "GitHub Actions load",
            "required": "yes",
            "ready": "not visible here",
            "detail": (
                "REQUIRED. Add repository secret CARE_OPS_PG_DSN, then run the workflow "
                "Load published data. The secret is not in the repo."
            ),
        },
        {
            "step": "4",
            "name": "Asana",
            "required": "yes",
            "ready": "no" if "Asana" in gaps else "yes",
            "detail": (
                "REQUIRED. Connected. The public page only reads project Care-gap work plan "
                "(task counts and statuses). The owner seeds tasks with "
                "python -m care_ops_agent.pm.asana seed. Visitors cannot create tasks."
                if "Asana" not in gaps else
                "REQUIRED. Not connected. Free personal access token: "
                "https://app.asana.com/0/my-apps. Set ASANA_BACKEND=live, ASANA_ACCESS_TOKEN, "
                "and ASANA_WORKSPACE_GID. Until those are set, the demo raises PortfolioNotConfigured. "
                "CI still uses the offline CSV client and does not call Asana."
            ),
        },
        {
            "step": "5",
            "name": "Salesforce",
            "required": "yes",
            "ready": "no" if "Salesforce" in gaps else "yes",
            "detail": (
                "REQUIRED, pending owner credentials. Free Developer Edition: "
                "https://developer.salesforce.com/signup. Set SALESFORCE_BACKEND=live, "
                "SF_LOGIN_URL, SF_CLIENT_ID, SF_CLIENT_SECRET, SF_USERNAME, SF_PASSWORD, "
                "and SF_SECURITY_TOKEN. Until those are set, the demo raises and does not invent "
                "a login. Once set, the demo logs in read-only and reports the org and Account count."
            ),
        },
        {
            "step": "6",
            "name": "Tableau Public",
            "required": "yes",
            "ready": "no" if "Tableau Public" in gaps else "yes",
            "detail": (
                "REQUIRED, pending owner credentials. Tableau Public and Tableau Desktop are free "
                "(https://public.tableau.com). Publish the workbook, then set TABLEAU_PUBLIC_URL "
                "to the https://public.tableau.com viz link. Until that is set, the demo raises "
                "and does not invent a dashboard URL. Once set, the demo shows the link. "
                "There is still no Tableau publish API in this repo."
            ),
        },
    ]


def blocking_gaps() -> list[str]:
    """Required items this process can actually see are missing."""
    return [item["name"] for item in checklist() if item["required"] == "yes" and item["ready"] == "no"]


def main() -> None:
    for item in checklist():
        print(f"{item['step']}. {item['name']}: {item['ready']} (required: {item['required']})")
        print(f"   {item['detail']}")
    missing = blocking_gaps()
    if missing:
        print("Blocked until set: " + ", ".join(missing))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
