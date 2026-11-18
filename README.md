# care-ops-agent

A portfolio project for program, project-management, and healthcare-operations analytics roles. The hosted demo queries **real public care-gap rates**: HRSA health-center counts, CMS Medicare Advantage contract rates, and CDC PLACES county estimates. Python computes every rate. A language model, if one is turned on, may only rewrite prose, and the numeric-fidelity guard rejects numbers the code did not produce.

The weekly Harbor Health Plan program is still a **labeled simulation**: eight synthetic partner groups, Synthea patients, outreach draws, a synthetic RFP, and synthetic budgets. It is the CI and offline fallback. It is not a live network, a real contract, or a clinical tool. Read [SIMULATION_DISCLAIMER.md](SIMULATION_DISCLAIMER.md).

The hosted path is not optional, and it is not wired up in this repository because the database URL is a secret. The ordered steps, the free tiers, and the env var names are in [docs/HOSTING.md](docs/HOSTING.md).

Read [PRD.md](PRD.md), [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md), and [RESUME_BULLETS.md](RESUME_BULLETS.md).

## What a reviewer can run

Offline, with the synthetic roster (no database, no download):

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m care_ops_agent.run_program
python -m care_ops_agent.run_program --eval
```

Hosted, after `CARE_OPS_PG_DSN` is set to a Neon URL (see [docs/HOSTING.md](docs/HOSTING.md)):

```bash
python -m care_ops_agent.public.load
python -m care_ops_agent.public.status
streamlit run streamlit_app.py
```

`pytest` and `run_program` use a small committed roster. They do not download data and they do not need PostgreSQL, Asana, Salesforce, or Tableau. The public loader does not use that roster.

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

## Offline Synthea load

The CMS hospital file and the Synthea FHIR R4 sample are about 1.5 GB and are gitignored. This load is the offline fallback. It refuses a non-local `CARE_OPS_PG_DSN` so synthetic patients are not written to the hosted database.

```bash
python -m care_ops_agent.data.download
export CARE_OPS_PG_DSN=postgresql://postgres@localhost:5433/care_ops
python -m care_ops_agent.data.load
python -m care_ops_agent.run_triage scenarios/*.yaml
```

FHIR bundles stay in local files. The project does not upload them to a public FHIR server.

## Required hosted connections

These are part of the hosted portfolio. They are pending the owner's credentials. The demo names the missing variables and does not invent a sync. CI still uses the offline clients.

| System | Free tier | What going live needs |
|---|---|---|
| Asana | Personal access token on a free account | `ASANA_BACKEND=live`, `ASANA_ACCESS_TOKEN`, `ASANA_WORKSPACE_GID` |
| Salesforce | Developer Edition | `SALESFORCE_BACKEND=live` plus the `SF_*` variables in `.env.example` |
| Tableau Public | Tableau Public account and Desktop | Publish the workbook, then `TABLEAU_PUBLIC_URL` (`https://public.tableau.com/...`) |
| Ollama | Local only | A local model. The default backend is `deterministic` and does not call one |

Tokens are read from the environment. None are stored in the repo. See [.env.example](.env.example) and [docs/HOSTING.md](docs/HOSTING.md).

## Learning site

[academy/](academy/) is a static course, one page per session, with an architecture note before each line-by-line walkthrough and a high-level quiz. GitHub Actions workflow `pages` publishes `academy/site`. Videos are rendered locally with edge-tts (voice `en-US-AndrewNeural`) and committed under `academy/site/videos` so the Pages artifact can serve them.

## Layout

Sessions 1–4 (2026-11-03) built the PRD, the FHIR-to-PostgreSQL views, care-gap triage, and the Salesforce-shaped pipeline. Sessions 5–10 add program controls, the PDSA loop, the outreach test, the RFP library, the held-out eval and MS Project export, and the dashboard extracts. Details are in [PLAN.md](PLAN.md) and [docs/sessions](docs/sessions).
