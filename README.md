# care-ops-agent · SIMULATION

A portfolio project for program, project-management, and healthcare-operations analytics roles. It runs a **simulated** care-gap closure program for a fictional payer, Harbor Health Plan. Eight partner groups are synthetic. Patients are synthetic. Nothing here is a live network, a real contract, or a clinical tool.

The program tracks three simplified, HEDIS-style measures: diabetes control (HbA1c under 8.0%), blood-pressure control (under 140/90), and breast cancer screening. Each week is a PDSA cycle. The code separates a real care gap from a missing lab feed, keeps a Salesforce-shaped partner pipeline, writes the plan as an Asana import file, and puts the numbers in Excel and in Tableau-ready CSV extracts.

Every rate, interval, sample size, and p-value is computed in Python. A language model, if you turn one on, may only rewrite prose, and the numeric-fidelity guard rejects numbers that the code did not produce.

Read [SIMULATION_DISCLAIMER.md](SIMULATION_DISCLAIMER.md), [PRD.md](PRD.md), [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md), and [RESUME_BULLETS.md](RESUME_BULLETS.md).

## What a reviewer can run

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m care_ops_agent.run_program
python -m care_ops_agent.run_program --eval
```

`pytest` and `run_program` use a small committed roster. They do not download data and they do not need PostgreSQL, Asana, Salesforce, or Tableau.

`run_program` writes `out/`:

- `program_controls.xlsx` — charter, WBS, RAID, change log, budget burn, capacity, swimlane
- `harbor_care_gap.xml` — MS Project XML for the same WBS
- `asana/asana_import.csv` — tasks for Asana's CSV importer (`SIM-` ids, not a live board)
- `crm_export/*.csv` — Salesforce Data Import Wizard shape
- `updates/` — partner, internal, and steering notes, plus the permissions spec
- `pdsa_log.json` — plan / do / study / act for each program week
- `ab_trial.json` — outreach A/B readout
- `rfp_tracker.xlsx` — synthetic payer questions, library entries, and citations
- `tableau/*.csv` and `tableau/preview.html` — flat extracts and a local HTML preview

Checked-in copies of those files are in [docs/samples](docs/samples). The held-out score is in [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md). On this build the single-cause triage matched 11 of 11 held-out scenarios, with 1 false alarm on 5 quiet scenarios, so the scaling workbook's rule says **NO-GO**. That gate is doing the job it was given: zero chance flags, or do not scale.

## Optional full data load

The CMS hospital file and the Synthea FHIR R4 sample are about 1.5 GB and are gitignored.

```bash
python -m care_ops_agent.data.download
export CARE_OPS_PG_DSN=postgresql://postgres@localhost:5433/care_ops
python -m care_ops_agent.data.load
python -m care_ops_agent.run_triage scenarios/*.yaml
```

FHIR bundles stay in local files. The project does not upload them to a public FHIR server.

## Accounts that are not connected

| System | What is in the repo | What going live needs |
|---|---|---|
| Asana | CSV import and `OfflineAsanaClient` | `ASANA_BACKEND=live`, `ASANA_ACCESS_TOKEN`, `ASANA_WORKSPACE_GID` |
| Salesforce | Data Import Wizard CSVs and `OfflineSalesforceClient` | `SALESFORCE_BACKEND=live` plus the `SF_*` variables in `.env.example` |
| Tableau Public | CSV extracts, a local HTML preview, and [docs/tableau/DASHBOARD_SPEC.md](docs/tableau/DASHBOARD_SPEC.md) | Tableau Public Desktop, then a manual publish from Neel's account |
| Ollama | Optional prose rewrite | A local model. The default backend is `deterministic` and does not call one |

Tokens are read from the environment. None are stored in the repo. See [.env.example](.env.example).

## Learning site

[academy/](academy/) is a static course, one page per session, with an architecture note before each line-by-line walkthrough and a high-level quiz. GitHub Actions workflow `pages` publishes `academy/site`. Videos are rendered locally with edge-tts (voice `en-US-AndrewNeural`) and committed under `academy/site/videos` so the Pages artifact can serve them.

## Layout

Sessions 1–4 (2026-11-03) built the PRD, the FHIR-to-PostgreSQL views, care-gap triage, and the Salesforce-shaped pipeline. Sessions 5–10 add program controls, the PDSA loop, the outreach test, the RFP library, the held-out eval and MS Project export, and the dashboard extracts. Details are in [PLAN.md](PLAN.md) and [docs/sessions](docs/sessions).
