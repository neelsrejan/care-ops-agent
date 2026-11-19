# UI audit — hosted care-gap demo

Reviewed 2026-11-19.

- Live app: https://care-ops-agent.streamlit.app/ (the legacy share link `https://share.streamlit.io/neelsrejan/care-ops-agent/main/streamlit_app.py` redirects there).
- Source of that page: `streamlit_app.py` on `main` at the time of the review.
- Visual reference: https://invalid-agent-lwycv4pt4vd4emwhuiqde3.streamlit.app/ and `app/streamlit_app.py` in https://github.com/neelsrejan/invalid-agent.

The live page was opened in a browser. The first screen is HRSA UDS 2025, breast cancer screening, state = All. The notes below describe that screen and the rest of the page from the source.

## Current layout

Default Streamlit wide layout. No custom banner, no stepper, no page title beyond the H1.

Sidebar, header **Query**:

- Source (HRSA health centers, CMS Star Ratings, or CDC PLACES).
- Measure (three per source). The first item in the dict is breast cancer screening, so that is what a visitor lands on.

Main column, top to bottom, all at once:

1. Title: “Care-gap rates from public data.”
2. A gray caption naming HRSA, CMS, CDC, the Python rule, and the Harbor simulation.
3. State dropdown and a “Name contains” box.
4. The measure name again, as a subheading.
5. Four metrics: Comparator, Entities with a rate, Worse by ≥ 5 points, Pooled counts. On the live mammography view those were 56.2, 958 / 958, 381, and 1714948 / 3048987.
6. One dense paragraph: the deterministic note, including the diabetes direction caveat even though the selected measure is mammography.
7. A caption: “Numeric fidelity check passed (deterministic).”
8. A horizontal bar chart of `gap_pp` with no title. Streamlit’s default bar chart sorts the category axis alphabetically, so the longest bar is not at the top. Labels are truncated (`ADVOCATES FOR…`). The code takes the first 15 rows after the gap sort, but the chart does not say “15” or “widest.”
9. The full filtered table (hundreds of rows on HRSA), then a CSV download.
10. **Required connections** — Asana, Salesforce, Tableau Public. Missing secrets become an error that names the variables. Configured systems show a link and, for Asana, task status. This block sits under the full table, so it is below the first screen.
11. **Source** — publisher, vintage, row count, license, file link.

There is no scenario, no Next, and no recommendation.

## This is a control panel

A visitor has to invent the order. The sidebar is two unlabeled-in-context knobs (“Query”), the main column repeats the filters, and every artifact for the chosen measure is stacked on one page. Nothing says “start here” or “you are done.” Free exploration is the only mode.

Invalid-agent is the visual target, and it is still a control panel (sidebar case, week, rules-only toggle, then metrics, two charts, strata, tabs). What is worth copying is the surface, not that information architecture:

- A navy banner (`#0B3A5B`, cream text) that states the data rule in one place.
- A short caption under the title (“Python does the math”).
- A single row of large metrics.
- One chart with a title and a caption that says what the mark means.
- Suggested buttons when the page wants a question asked.
- Lots of unused whitespace, default Streamlit type, no extra theme.

The care-gap page has the metrics and the default Streamlit chrome. It does not have the banner, the chart title, the “what this mark means” caption, or a suggested action.

## What a first-time visitor has to figure out

Landed on the live mammography screen, with no tour:

- **What the demo is for.** The title is “Care-gap rates from public data.” It does not say who the visitor is, what decision the page supports, or that the path is brief → file → national rate → who is worse → recommendation.
- **Which control to touch first.** Source, measure, state, and name are all active before any explanation. The default measure is whichever key is first in `catalog.MEASURES`, not the measure that teaches the direction rule.
- **What “Comparator” means.** The help text is “Percent. Computed in Python from the loaded rows.” It does not say pooled national rate, unweighted contract mean, or population-weighted county mean.
- **Which way is bad.** The paragraph on the mammography screen still explains that a higher diabetes rate is a wider gap. That sentence is the HRSA source caveat, attached to every HRSA measure. A visitor can apply it to mammography and reverse the story.
- **What the blue bars are.** There is no axis title in the default chart, the sort is alphabetical, and a 56-point bar for a health center at 0% sits in the middle of the list. The table underneath is the entire file, so the chart and the table look like two unrelated views.
- **Whether 0% is a data problem.** Centers with numerator 0 and a full-sized denominator (the live table’s first rows include Ministry of Health and Environment, state `MH`) look like the worst gap. The page never says “these are the published counts” or offers “start with this row.”
- **What to do with 381 entities.** The metric is real. The page never turns it into “review these, start with this name.”
- **The red block at the bottom.** If Asana, Salesforce, or Tableau secrets are unset, `credential_message` renders as `st.error` after a long table. That reads as a broken demo, not as “the calculation worked and the owner’s follow-up systems are not connected yet.”
- **The Harbor sentence in the caption.** It correctly says the weekly program is a simulation and is not shown. On a first screen full of knobs, it is easy to miss, and nothing later repeats the boundary next to a decision.

A power user who already knows HRSA versus CMS versus PLACES can drive the sidebar. A hiring manager opening the URL cannot.

## Redesign plan

Replace the one-page control panel with a seven-step walkthrough. Keep the invalid-agent banner, metric row, caption, and suggested-button pattern. Show one artifact per step. Put the old page behind a **Free explore** toggle so every current control still exists.

| Step | Title | What the visitor does | What is on the page |
|---|---|---|---|
| 1 of 7 | The brief | Click Diabetes, Blood pressure, or Breast cancer screening | The scenario in plain words. No chart. Default question: diabetes, because the direction rule matters. |
| 2 of 7 | Which file | Click HRSA, CMS, or CDC | Grain, publisher, and what Python will compute for that file. No rows yet. |
| 3 of 7 | The national picture | Click “Show the widest gaps” | The four existing metrics and the fidelity-checked sentence. Direction is stated for this measure only. |
| 4 of 7 | The widest gaps | Click the worst name, or a state that has entities over the threshold | One bar chart, longest bar at the top, capped at 15, titled in percentage points. |
| 5 of 7 | One slice | Use the suggested state or name, or type a filter. Download CSV. | The existing table and only the matching rows. |
| 6 of 7 | Check the work | Open the source file. Click through to the recommendation. | Publisher, vintage, license, direction, HRSA percent note when it applies, fidelity caption. |
| 7 of 7 | The recommendation | Open free explore, or start over | A recommendation whose numbers come from the Python summary. Then the existing Asana, Salesforce, and Tableau status, framed as read-only follow-up. |

Back and Next sit on every step. The step label is “Step N of 7.” Free explore is a toggle on every step and a button on the last step. In that mode the sidebar Query controls return: source, measure, state, name, metrics, chart, full table, CSV, connections, and source. The walkthrough does not add a second calculator. `build_view` still computes the rates. `narrate` still rewrites only the sentence, and the recommendation goes through the same numeric check.

Out of scope for this pass: changing Neon, Streamlit Community Cloud, the public files, or the offline Harbor simulation. Synthetic patients stay on the CI path. Secrets stay in Streamlit secrets and the environment.
