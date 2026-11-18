"""Which connections exist. Prints names of variables, never their values."""

from __future__ import annotations

import os


def _set(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def checklist() -> list[dict[str, str]]:
    """Ordered owner steps. `ready` is yes or no. Required steps block the hosted demo."""
    hosted = _set("CARE_OPS_PG_DSN") or _set("DATABASE_URL")
    asana = os.environ.get("ASANA_BACKEND", "offline").lower() == "live" and _set("ASANA_ACCESS_TOKEN") and _set("ASANA_WORKSPACE_GID")
    salesforce = os.environ.get("SALESFORCE_BACKEND", "offline").lower() == "live" and all(
        _set(name) for name in ("SF_CLIENT_ID", "SF_CLIENT_SECRET", "SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN")
    )
    return [
        {
            "step": "1",
            "name": "Neon Postgres",
            "required": "yes",
            "ready": "yes" if hosted else "no",
            "detail": (
                "Set CARE_OPS_PG_DSN (or DATABASE_URL) to the Neon connection string. "
                "Free plan, no credit card: https://neon.com (Project, then Connect). "
                "Then run: python -m care_ops_agent.public.load"
            ),
        },
        {
            "step": "2",
            "name": "Streamlit Community Cloud",
            "required": "yes",
            "ready": "no",
            "detail": (
                "This process cannot see a Streamlit login. Deploy streamlit_app.py from the "
                "public GitHub repo at https://share.streamlit.io and set secret CARE_OPS_PG_DSN "
                "to the same Neon URL. A public app is free to view."
            ),
        },
        {
            "step": "3",
            "name": "GitHub Actions load",
            "required": "yes",
            "ready": "no",
            "detail": (
                "Add repository secret CARE_OPS_PG_DSN, then run the workflow Load published data. "
                "That is the repeatable load. The secret is not in the repo."
            ),
        },
        {
            "step": "4",
            "name": "Asana",
            "required": "for the live tracker only",
            "ready": "yes" if asana else "no",
            "detail": (
                "Create a personal access token at https://app.asana.com/0/my-apps (free). "
                "Set ASANA_BACKEND=live, ASANA_ACCESS_TOKEN, and ASANA_WORKSPACE_GID. "
                "Until those are set, the live client raises AsanaNotConfigured. "
                "The CSV import remains the offline fallback."
            ),
        },
        {
            "step": "5",
            "name": "Salesforce",
            "required": "for the live CRM only",
            "ready": "yes" if salesforce else "no",
            "detail": (
                "A free Developer Edition org: https://developer.salesforce.com/signup. "
                "Set SALESFORCE_BACKEND=live, SF_LOGIN_URL, SF_CLIENT_ID, SF_CLIENT_SECRET, "
                "SF_USERNAME, SF_PASSWORD, and SF_SECURITY_TOKEN. "
                "Until those are set, the live client raises SalesforceNotConfigured."
            ),
        },
        {
            "step": "6",
            "name": "Tableau Public",
            "required": "for a Tableau publish only",
            "ready": "no",
            "detail": (
                "Tableau Public has no token in this project. Publishing still needs the owner's "
                "Tableau Public account and Tableau Desktop (both free). The hosted view a "
                "hiring manager can open without that account is the Streamlit app."
            ),
        },
    ]


def main() -> None:
    for item in checklist():
        print(f"{item['step']}. {item['name']}: {item['ready']} (required: {item['required']})")
        print(f"   {item['detail']}")


if __name__ == "__main__":
    main()
