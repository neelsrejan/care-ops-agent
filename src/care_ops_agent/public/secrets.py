"""Copy host secrets into the environment. Values are never logged."""

from __future__ import annotations

import os

# Names only. Values come from the environment or from Streamlit secrets.
SECRET_NAMES = (
    "CARE_OPS_PG_DSN",
    "DATABASE_URL",
    "ASANA_BACKEND",
    "ASANA_ACCESS_TOKEN",
    "ASANA_WORKSPACE_GID",
    "SALESFORCE_BACKEND",
    "SF_LOGIN_URL",
    "SF_CLIENT_ID",
    "SF_CLIENT_SECRET",
    "SF_USERNAME",
    "SF_PASSWORD",
    "SF_SECURITY_TOKEN",
    "TABLEAU_PUBLIC_URL",
)


def apply_secret_values(values: dict[str, str]) -> None:
    """Fill empty environment variables from a mapping such as st.secrets.

    An environment variable that is already set wins, so a laptop override
    is not replaced by a secrets file.
    """
    for name in SECRET_NAMES:
        if os.environ.get(name, "").strip():
            continue
        raw = values.get(name, "")
        text = "" if raw is None else str(raw).strip()
        if text:
            os.environ[name] = text
