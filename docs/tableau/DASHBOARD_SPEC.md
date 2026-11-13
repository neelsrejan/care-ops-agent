# Tableau Public dashboard spec (SYNTHETIC)

Publishing is a manual step. This repo does not call Tableau Online or Tableau Public.

## Extracts

Produced by `python -m care_ops_agent.run_program` under `out/tableau/`, with a copy in `docs/samples/tableau/`.

| File | Grain | Use |
|---|---|---|
| `care_gap_weekly.csv` | week × partner × clinic × measure | met rate and missing-result share |
| `pipeline.csv` | account × measure | stage, days in stage, stalled, open gaps |
| `pdsa.csv` | program week | plan / do / study / act and flag count |
| `budget_burn.csv` | week × role | synthetic project-controls hours and cost |

Every file has a `label` column with the value `SYNTHETIC`. Open the CSVs in Tableau Public Desktop and create an extract there if you want a `.hyper` file. Do not add a live Salesforce or Postgres connection in the workbook.

## Sheets to build

1. **Network rates.** Columns: measure. Rows: partner. Color: `met_rate`. Filter: week. Caption the sheet "synthetic HEDIS-style rates, not certified HEDIS".
2. **Missing results.** Same grain, color `missing_share`. This is the data-issue view. A high missing share is not a care gap.
3. **Pipeline × gaps.** Bars of `open_gaps` by `stage`, with `stalled` as color. Title it as a simulated pipeline.
4. **PDSA log.** A table of week, act, flag count, and focus. Text, not a KPI tile.
5. **Budget burn.** Line of `cumulative_cost` by week. Subtitle: "synthetic project-controls figures, not a P&L".

Put a text box on the dashboard: "SYNTHETIC SIMULATION. Harbor Health Plan and the partner groups are fictional. Not for clinical or contracting use."

## Publish

1. Sign in to Tableau Public with Neel's account.
2. Open Tableau Public Desktop and connect to the four CSVs.
3. Build the sheets above. Do not join in any patient-level file. These extracts are already aggregated.
4. Server, Tableau Public, Save to Tableau Public. The workbook will be public. That is acceptable only because the data is synthetic.
5. Paste the public URL into the README. Until that URL exists, the dashboard is the spec plus the local preview.
