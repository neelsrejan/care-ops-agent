"""Connection strings for the hosted demo.

The public loader never falls back to local Postgres. A missing or local URL
raises HostedDatabaseRequired with the variable names and where to get them.
The message never includes the URL, because a Neon URL contains a password.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

HOSTED_DSN_HELP = (
    "The hosted demo needs a Postgres connection string. Set CARE_OPS_PG_DSN "
    "or DATABASE_URL to a Neon free-plan URL (https://neon.com, no credit card, "
    "Project -> Connect). On Streamlit Community Cloud, put the same value in "
    "a secret named CARE_OPS_PG_DSN. Do not commit the URL. Then load the "
    "tables with: python -m care_ops_agent.public.load"
)

_USERINFO = re.compile(r"://([^/@:]+):([^@]+)@")


class HostedDatabaseRequired(RuntimeError):
    """The public path was asked to run without a hosted database URL."""


def hostname(dsn: str) -> str:
    host = urlparse(dsn).hostname or ""
    return host.lower()


def redact(text: str) -> str:
    return _USERINFO.sub(r"://\1:[redacted]@", text)


def require_hosted_dsn() -> str:
    """Return the hosted URL, or raise without echoing it."""
    dsn = os.environ.get("CARE_OPS_PG_DSN", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        raise HostedDatabaseRequired(HOSTED_DSN_HELP)
    if (not hostname(dsn) or hostname(dsn) in LOCAL_HOSTS) and os.environ.get("CARE_OPS_ALLOW_LOCAL") != "1":
        raise HostedDatabaseRequired(
            "CARE_OPS_PG_DSN points at local Postgres. The demo has to use a hosted "
            "Neon URL so someone who is not on this machine can query it. "
            "CARE_OPS_ALLOW_LOCAL=1 is only for CI and for checking the SQL on a laptop. "
            + HOSTED_DSN_HELP
        )
    return dsn


def assert_synthetic_stays_local(dsn: str) -> None:
    """Block a Synthea load against a remote database.

    The hosted database is for public aggregate files. Synthetic patients
    stay on the CI and offline path.
    """
    if hostname(dsn) in LOCAL_HOSTS or not hostname(dsn):
        return
    if os.environ.get("CARE_OPS_ALLOW_SYNTHETIC_UPLOAD") == "1":
        return
    raise RuntimeError(
        "Refusing to load Synthea FHIR into a non-local database. "
        "Synthetic patients stay on the CI and offline path. "
        "Point CARE_OPS_PG_DSN at localhost for that load, or set "
        "CARE_OPS_ALLOW_SYNTHETIC_UPLOAD=1 to override."
    )
