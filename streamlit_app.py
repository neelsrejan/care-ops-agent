"""Hosted care-gap walkthrough.

Streamlit Community Cloud runs this file. Python computes every rate from the
public Postgres rows. A model may only rewrite a sentence. A missing connection
string stops the page with the variable name and where to get it.
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
from care_ops_agent.public.walkthrough import (
    BANNER,
    CHART_LIMIT,
    DEFAULT_FOCUS,
    DEFAULT_SOURCE,
    FOCUSES,
    SOURCE_SHORT,
    STEPS,
    Prompt,
    direction_sentence,
    filter_rows,
    guide_copy,
    measure_for,
    prompts_for,
    recommendation_note,
    state_options,
    step_index,
    table_records,
    widest_rows,
)


def _secret(name: str) -> str:
    try:
        value = st.secrets[name]
    except Exception:
        return ""
    return str(value or "").strip()


def _secret_map() -> dict[str, str]:
    return {name: _secret(name) for name in SECRET_NAMES}


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


def _percent(rate: float | None) -> str:
    if rate is None:
        return ""
    return f"{rate * 100:.1f}"


def _init_state() -> None:
    st.session_state.setdefault("step", 0)
    st.session_state.setdefault("focus_id", DEFAULT_FOCUS)
    st.session_state.setdefault("source_id", DEFAULT_SOURCE)
    st.session_state.setdefault(
        "measure_id",
        measure_for(st.session_state.focus_id, st.session_state.source_id),
    )
    st.session_state.setdefault("slice_state", "All")
    st.session_state.setdefault("slice_search", "")
    st.session_state.setdefault("free_explore", False)
    if st.session_state.pop("explore_request", False):
        st.session_state.free_explore = True
    step = int(st.session_state.step)
    st.session_state.step = min(max(step, 0), len(STEPS) - 1)


def _sync_measure() -> None:
    """Guided mode takes the measure from the question and the file."""
    if st.session_state.free_explore:
        return
    st.session_state.measure_id = measure_for(
        st.session_state.focus_id,
        st.session_state.source_id,
    )


def _apply(prompt: Prompt) -> None:
    if prompt.reset:
        st.session_state.focus_id = DEFAULT_FOCUS
        st.session_state.source_id = DEFAULT_SOURCE
        st.session_state.measure_id = measure_for(DEFAULT_FOCUS, DEFAULT_SOURCE)
    if prompt.focus_id:
        st.session_state.focus_id = prompt.focus_id
        source_id = prompt.source_id or st.session_state.source_id
        st.session_state.source_id = source_id
        st.session_state.measure_id = measure_for(prompt.focus_id, source_id)
    elif prompt.source_id:
        st.session_state.source_id = prompt.source_id
        st.session_state.measure_id = measure_for(
            st.session_state.focus_id,
            prompt.source_id,
        )
    if prompt.clear_slice:
        st.session_state.slice_state = "All"
        st.session_state.slice_search = ""
    if prompt.state is not None:
        st.session_state.slice_state = prompt.state
    if prompt.search is not None:
        st.session_state.slice_search = prompt.search
    if prompt.free_explore:
        st.session_state.explore_request = True
    if prompt.goto:
        st.session_state.step = step_index(prompt.goto)
    st.rerun()


def _prompt_row(prompts: list[Prompt]) -> None:
    if not prompts:
        return
    st.caption("Suggested next move")
    columns = st.columns(min(3, len(prompts)))
    for index, prompt in enumerate(prompts):
        selected = _prompt_selected(prompt)
        if columns[index % len(columns)].button(
            prompt.label,
            key=f"prompt-{prompt.id}",
            type="primary" if selected else "secondary",
        ):
            _apply(prompt)


def _prompt_selected(prompt: Prompt) -> bool:
    if prompt.focus_id and not prompt.source_id:
        return prompt.focus_id == st.session_state.focus_id
    if prompt.source_id and not prompt.focus_id:
        return prompt.source_id == st.session_state.source_id
    return False


def _go(delta: int) -> None:
    st.session_state.step = min(max(int(st.session_state.step) + delta, 0), len(STEPS) - 1)
    st.rerun()


def _banner() -> None:
    # A single HTML div was a flex item that refused to wrap, so the bar showed
    # only the end of the sentence. This paints the normal markdown block instead.
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.2rem; }
          div[data-testid="stMarkdown"]:has(.banner-mark) {
            background: #0B3A5B;
            color: #F7F5F2;
            padding: 0.7rem 1rem;
            border-radius: 6px;
            margin-bottom: 0.8rem;
          }
          div[data-testid="stMarkdown"]:has(.banner-mark) p {
            color: #F7F5F2;
            margin: 0;
            white-space: normal;
          }
          .banner-mark { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="banner-mark"></span>\n\n{BANNER}',
        unsafe_allow_html=True,
    )


def _render_copy(step_id: str) -> None:
    copy = guide_copy(step_id, st.session_state.focus_id, st.session_state.source_id)
    st.markdown(f"**What the agent is doing.** {copy['doing']}")
    st.markdown(f"**Why.** {copy['why']}")
    st.markdown(f"**What to look at.** {copy['look']}")


def _load_view():
    try:
        return _load(
            st.session_state.source_id,
            st.session_state.measure_id,
            _fingerprint(),
        ), None
    except Exception as exc:
        return None, redact(str(exc))


def _data_error(message: str) -> None:
    st.error(message)
    st.info(
        "If the published tables are missing, run `python -m care_ops_agent.public.load` "
        "with CARE_OPS_PG_DSN set."
    )


def _render_metrics(summary: dict) -> None:
    pooled = ""
    if summary.get("pooled_numerator") is not None:
        pooled = f"{summary['pooled_numerator']:.0f} / {summary['pooled_denominator']:.0f}"
    columns = st.columns(4)
    columns[0].metric(
        "Comparator",
        _percent(summary["comparator"]) or "—",
        help="Percent. Computed in Python from the loaded rows. It stays national when the table is filtered.",
    )
    columns[1].metric("Entities with a rate", f"{summary['n_with_rate']} / {summary['n_entities']}")
    columns[2].metric(f"Worse by ≥ {summary['threshold_pp']:.0f} points", summary["n_worse"])
    columns[3].metric("Pooled counts", pooled or "—")


def _render_note(view: dict) -> None:
    note = view["note"]
    st.write(note["text"])
    if note["fidelity"]["ok"]:
        st.caption(f"Numeric fidelity check passed ({note['backend']}).")
    else:
        st.warning("Numeric fidelity check failed. The note was not shown as verified.")


@st.cache_data(ttl=300, show_spinner=False)
def _recommendation(source_id: str, measure_id: str, fingerprint: str) -> dict:
    view = _load(source_id, measure_id, fingerprint)
    return recommendation_note(view["summary"], view["rows"], view["definition"])


def _render_chart(rows: list[dict]) -> None:
    records = table_records(widest_rows(rows, limit=CHART_LIMIT))
    if not records:
        st.caption("No entity has a gap on this measure.")
        return
    frame = pd.DataFrame(records)
    import altair as alt

    low = min(0.0, float(frame["gap_pp"].min()))
    high = max(5.0, float(frame["gap_pp"].max()))
    chart = (
        alt.Chart(frame)
        .mark_bar(color="#0B3A5B")
        .encode(
            x=alt.X(
                "gap_pp:Q",
                title="Percentage points worse than the comparator",
                scale=alt.Scale(domain=[low, high], nice=False),
            ),
            y=alt.Y("name:N", sort="-x", title=None),
            tooltip=["name", "state", "rate_percent", "gap_pp"],
        )
        .properties(height=max(220, 28 * len(frame)))
    )
    st.altair_chart(chart, width="stretch")
    noun = "bar" if len(frame) == 1 else "bars"
    st.caption(
        f"{len(frame)} {noun}. Length is how many points worse than the national comparator."
    )


def _render_table(rows: list[dict], *, source_id: str, measure_id: str) -> None:
    frame = pd.DataFrame(table_records(rows))
    st.dataframe(frame, width="stretch", hide_index=True)
    st.download_button(
        "Download this table",
        frame.to_csv(index=False).encode(),
        file_name=f"{source_id}_{measure_id}.csv",
        mime="text/csv",
    )


def _render_connections() -> None:
    st.subheader("Required connections")
    st.caption(
        "Asana holds the work plan, Salesforce holds the org, and Tableau Public holds the viz. "
        "This page only reads them. It does not create tasks."
    )
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


def _render_source(view: dict) -> None:
    source = view["source"]
    if not source:
        return
    st.subheader("Source")
    st.markdown(f"**{source['title']}**")
    st.write(source["publisher"])
    st.write(f"Vintage: {source['vintage']}. Retrieved {source['retrieved_on']}. Rows loaded: {source['row_count']}.")
    st.write(source["notes"])
    st.write(source["license"])
    if source.get("source_url"):
        st.link_button("Open the source file", source["source_url"])
    st.markdown(f"[File]({source['source_url']})")


def _hrsa_note(source_id: str, measure_id: str) -> None:
    if source_id == "hrsa_uds" and measure_id in HRSA_PERCENT_NOTES:
        st.info(HRSA_PERCENT_NOTES[measure_id])


def _slice_controls(rows: list[dict]) -> tuple[str, str]:
    options = state_options(rows)
    if st.session_state.slice_state not in options:
        st.session_state.slice_state = "All"
    left, right = st.columns(2)
    with left:
        st.selectbox("State", options, key="slice_state")
    with right:
        st.text_input("Name contains", key="slice_search")
    return st.session_state.slice_state, st.session_state.slice_search


def _render_guided() -> None:
    step = STEPS[int(st.session_state.step)]
    st.progress((int(st.session_state.step) + 1) / len(STEPS))
    st.caption(f"Step {int(st.session_state.step) + 1} of {len(STEPS)} — {step.title}")
    pills = st.columns(len(STEPS))
    for index, item in enumerate(STEPS):
        if pills[index].button(
            f"{index + 1}. {item.short}",
            key=f"step-{item.id}",
            type="primary" if index == st.session_state.step else "secondary",
        ):
            st.session_state.step = index
            st.rerun()

    st.subheader(step.title)
    _render_copy(step.id)
    needs_rows = step.id in {"national", "gaps", "slice", "check", "outcome"}
    view = None
    rows: list[dict] = []
    if needs_rows:
        view, error = _load_view()
        if error or view is None:
            _data_error(error or "The measure did not load.")
        else:
            rows = view["rows"]
            _render_step_body(step.id, view, rows)
    else:
        _render_step_body(step.id, None, rows)

    # Actions that set a widget value have to run before that widget exists.
    # National, file, and brief prompts do not touch slice widgets. Gap prompts
    # do, and they are drawn above the slice widgets on the next run.
    if step.id != "slice":
        _prompt_row(prompts_for(
            step.id,
            focus_id=st.session_state.focus_id,
            source_id=st.session_state.source_id,
            rows=rows,
        ))

    left, _, right = st.columns([1, 2, 1])
    with left:
        if st.session_state.step > 0 and st.button("Back", width="stretch"):
            _go(-1)
    with right:
        if st.session_state.step < len(STEPS) - 1 and st.button("Next", type="primary", width="stretch"):
            _go(1)


def _render_step_body(step_id: str, view: dict | None, rows: list[dict]) -> None:
    focus = FOCUSES[st.session_state.focus_id]
    if step_id == "brief":
        st.write(
            "You are walking a care-gap question the way a hiring manager would. "
            "Patient charts are not public. The agent will read one free file, and Python "
            "will compute every rate and every gap."
        )
        st.write(focus["blurb"])
        return
    if step_id == "file":
        st.write(SOURCE_SHORT[st.session_state.source_id])
        meta = catalog.SOURCES[st.session_state.source_id]
        st.write(meta["notes"])
        return
    if view is None:
        return
    summary = view["summary"]
    measure_id = st.session_state.measure_id
    source_id = st.session_state.source_id
    if step_id == "national":
        st.subheader(view["definition"]["measure_label"])
        _hrsa_note(source_id, measure_id)
        _render_metrics(summary)
        _render_note(view)
        return
    if step_id == "gaps":
        _render_chart(rows)
        return
    if step_id == "slice":
        _prompt_row(prompts_for(
            "slice",
            focus_id=st.session_state.focus_id,
            source_id=source_id,
            rows=rows,
        ))
        state, search = _slice_controls(rows)
        shown = filter_rows(rows, state=state, search=search)
        if state != "All" or search.strip():
            st.caption("The comparator stays national. This table is the slice you picked.")
        if not shown:
            st.info("No rows match this slice.")
        _render_table(shown, source_id=source_id, measure_id=measure_id)
        return
    if step_id == "check":
        _hrsa_note(source_id, measure_id)
        _render_note(view)
        _render_source(view)
        return
    if step_id == "outcome":
        note = _recommendation(source_id, measure_id, _fingerprint())
        worst = next((row for row in rows if row.get("gap_pp") is not None), None)
        columns = st.columns(3)
        columns[0].metric("Entities to review", summary["n_worse"])
        columns[1].metric("Start with", (worst or {}).get("entity_name") or "—")
        gap = None if worst is None else round(float(worst["gap_pp"]), 1)
        columns[2].metric("Gap (points)", "—" if gap is None else gap)
        st.write(note["text"])
        if note["fidelity"]["ok"]:
            st.caption(f"Numeric fidelity check passed ({note['backend']}).")
        else:
            st.warning("Numeric fidelity check failed. The recommendation was not shown as verified.")
        _render_connections()


def _render_explore() -> None:
    st.caption("Free explore. Same Python rates as the walkthrough. The sidebar is the filter set.")
    with st.sidebar:
        st.header("Query")
        st.selectbox(
            "Source",
            list(catalog.MEASURES),
            format_func=lambda key: catalog.SOURCES[key]["title"],
            key="source_id",
        )
        measure_ids = list(catalog.MEASURES[st.session_state.source_id])
        if st.session_state.measure_id not in measure_ids:
            st.session_state.measure_id = measure_ids[0]
        st.selectbox(
            "Measure",
            measure_ids,
            format_func=lambda key: catalog.MEASURES[st.session_state.source_id][key]["label"],
            key="measure_id",
        )
    view, error = _load_view()
    if error or view is None:
        _data_error(error or "The measure did not load.")
        return
    rows = view["rows"]
    state, search = _slice_controls(rows)
    shown = filter_rows(rows, state=state, search=search)
    st.subheader(view["definition"]["measure_label"])
    st.caption(direction_sentence(st.session_state.source_id, st.session_state.measure_id))
    _hrsa_note(st.session_state.source_id, st.session_state.measure_id)
    _render_metrics(view["summary"])
    if state != "All":
        st.caption("The comparator stays national. The table is filtered.")
    _render_note(view)
    _render_chart(shown)
    _render_table(shown, source_id=st.session_state.source_id, measure_id=st.session_state.measure_id)
    _render_connections()
    _render_source(view)


def main() -> None:
    st.set_page_config(page_title="Care-gap walkthrough", layout="wide", initial_sidebar_state="auto")
    _apply_secrets()
    try:
        require_hosted_dsn()
    except HostedDatabaseRequired as exc:
        st.error(str(exc))
        st.stop()
    _init_state()
    _banner()
    title, toggle = st.columns([4, 1])
    with title:
        st.title("Care-gap walkthrough")
        st.caption("Seven steps, from the question to the recommendation. Python does the math.")
    with toggle:
        st.toggle(
            "Free explore",
            key="free_explore",
            help="Leave the steps and use the source, measure, state, and name filters yourself.",
        )
    _sync_measure()
    if st.session_state.free_explore:
        _render_explore()
        return
    _render_guided()


if __name__ == "__main__":
    main()
