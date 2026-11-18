"""Hosted care-gap demo. Reads public rows from Postgres and computes rates in Python.

Streamlit Community Cloud runs this file. It does not fall back to Synthea.
A missing connection string stops the page with the variable name and where to get it.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from care_ops_agent.public import catalog
from care_ops_agent.public.dsn import HostedDatabaseRequired, redact, require_hosted_dsn
from care_ops_agent.public.integrations import credential_gaps, credential_message, live_status
from care_ops_agent.public.parse import HRSA_PERCENT_NOTES
from care_ops_agent.public.query import build_view
from care_ops_agent.public.secrets import SECRET_NAMES, apply_secret_values

st.set_page_config(page_title="Care-gap rates", layout="wide")
st.title("Care-gap rates from public data")
st.caption(
    "Health-center counts are HRSA UDS 2025. Contract percents are CMS 2027 Star Ratings. "
    "County figures are CDC PLACES 2025 model-based estimates. Python computes every rate and gap. "
    "The Harbor Health Plan weekly program is a separate labeled simulation and is not shown here."
)


def _secret(name: str) -> str:
    try:
        value = st.secrets[name]
    except Exception:
        return ""
    return str(value or "").strip()


def _secret_map() -> dict[str, str]:
    values: dict[str, str] = {}
    for name in SECRET_NAMES:
        values[name] = _secret(name)
    return values


def _apply_secrets() -> None:
    apply_secret_values(_secret_map())


def _fingerprint() -> str:
    raw = os.environ.get("CARE_OPS_PG_DSN", "") or os.environ.get("DATABASE_URL", "")
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _integration_fingerprint() -> str:
    blob = "\n".join(os.environ.get(name, "") for name in SECRET_NAMES)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


@st.cache_data(ttl=300, show_spinner=False)
def _probes(fingerprint: str) -> list[dict]:
    del fingerprint
    return live_status()


@st.cache_data(ttl=300, show_spinner=False)
def _load(source_id: str, measure_id: str, fingerprint: str) -> dict:
    del fingerprint
    import psycopg

    with psycopg.connect(require_hosted_dsn(), autocommit=True) as con:
        return build_view(con, source_id, measure_id)


def _show_count(value: float | None) -> int | float | None:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-6:
        return int(round(value))
    return round(float(value), 1)


def _percent(rate: float | None) -> str:
    if rate is None:
        return ""
    return f"{rate * 100:.1f}"


_apply_secrets()
try:
    require_hosted_dsn()
except HostedDatabaseRequired as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.header("Query")
    source_id = st.selectbox(
        "Source",
        list(catalog.MEASURES),
        format_func=lambda key: catalog.SOURCES[key]["title"],
    )
    measure_ids = list(catalog.MEASURES[source_id])
    measure_id = st.selectbox(
        "Measure",
        measure_ids,
        format_func=lambda key: catalog.MEASURES[source_id][key]["label"],
    )

try:
    view = _load(source_id, measure_id, _fingerprint())
except Exception as exc:
    st.error(redact(str(exc)))
    st.info("If the published tables are missing, run `python -m care_ops_agent.public.load` with CARE_OPS_PG_DSN set.")
    st.stop()

summary = view["summary"]
rows = view["rows"]
states = sorted({row.get("state") or "" for row in rows if row.get("state")})
left, right = st.columns(2)
with left:
    state = st.selectbox("State", ["All", *states]) if states else "All"
with right:
    search = st.text_input("Name contains", "")

shown = rows
if state != "All":
    shown = [row for row in shown if row.get("state") == state]
if search.strip():
    needle = search.strip().lower()
    shown = [row for row in shown if needle in (row.get("entity_name") or "").lower()]

st.subheader(view["definition"]["measure_label"])
if measure_id in HRSA_PERCENT_NOTES and source_id == "hrsa_uds":
    st.info(HRSA_PERCENT_NOTES[measure_id])
metric_cols = st.columns(4)
metric_cols[0].metric("Comparator", _percent(summary["comparator"]) or "—", help="Percent. Computed in Python from the loaded rows.")
metric_cols[1].metric("Entities with a rate", f"{summary['n_with_rate']} / {summary['n_entities']}")
metric_cols[2].metric(f"Worse by ≥ {summary['threshold_pp']:.0f} points", summary["n_worse"])
pooled = ""
if summary.get("pooled_numerator") is not None:
    pooled = f"{summary['pooled_numerator']:.0f} / {summary['pooled_denominator']:.0f}"
metric_cols[3].metric("Pooled counts", pooled or "—")
if state != "All":
    st.caption("The comparator stays national. The table is filtered.")

note = view["note"]
st.write(note["text"])
if note["fidelity"]["ok"]:
    st.caption(f"Numeric fidelity check passed ({note['backend']}).")
else:
    st.warning("Numeric fidelity check failed. The note was not shown as verified.")

frame = pd.DataFrame([
    {
        "name": row.get("entity_name"),
        "id": row.get("entity_id"),
        "state": row.get("state") or "",
        "rate_percent": None if row.get("rate") is None else round(row["rate"] * 100, 1),
        "gap_pp": None if row.get("gap_pp") is None else round(row["gap_pp"], 1),
        "numerator": _show_count(row.get("numerator")),
        "denominator": _show_count(row.get("denominator")),
        "status": row.get("status") or "",
    }
    for row in shown
])
chart = frame.dropna(subset=["gap_pp"]).head(15)
if not chart.empty:
    st.bar_chart(chart.set_index("name")["gap_pp"], horizontal=True)
st.dataframe(frame, width="stretch", hide_index=True)
st.download_button(
    "Download this table",
    frame.to_csv(index=False).encode(),
    file_name=f"{source_id}_{measure_id}.csv",
    mime="text/csv",
)

st.subheader("Required connections")
gaps = credential_gaps()
if gaps:
    st.error(credential_message(gaps))
for row in _probes(_integration_fingerprint()):
    if row["ok"]:
        st.success(row["summary"])
        if row.get("url"):
            st.link_button(row.get("link_label") or row["system"], row["url"])
        if row.get("tasks"):
            st.dataframe(
                [
                    {"name": task["name"], "status": "complete" if task["completed"] else "open"}
                    for task in row["tasks"]
                ],
                width="stretch",
                hide_index=True,
            )
    else:
        st.error(f"{row['system']}: {row['summary']}")

source = view["source"]
if source:
    st.subheader("Source")
    st.markdown(f"**{source['title']}**")
    st.write(source["publisher"])
    st.write(f"Vintage: {source['vintage']}. Retrieved {source['retrieved_on']}. Rows loaded: {source['row_count']}.")
    st.write(source["notes"])
    st.write(source["license"])
    st.markdown(f"[File]({source['source_url']})")
