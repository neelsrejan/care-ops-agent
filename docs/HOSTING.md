# Hosted demo

A hiring manager should be able to open one URL, filter a measure, and see rates computed in Python from public files. That path is Neon (Postgres) plus Streamlit Community Cloud. Both have a free tier and do not require a credit card. This repository does not contain either login, and it does not contain a connection string.

The Harbor Health Plan weekly program (partners, outreach draws, RFP, budgets, Excel, MS Project XML) stays a labeled simulation. `pytest` and `python -m care_ops_agent.run_program` still run it with no database. Synthea FHIR is not loaded into the hosted database.

## Why these sources

Patient-level charts are not public. Three free files still match the care-gap story, at three grains:

| Source | Grain | What Python computes | What it does not do |
|---|---|---|---|
| HRSA UDS 2025, H80 awardee workbook | Health center | Rate = numerator / denominator, Wilson interval when both are whole numbers, gap versus the pooled national rate | It does not call the published percent the answer. Mammography is checked against that percent (rounding). |
| CMS 2027 Star Ratings measure data | Medicare Advantage contract | Unweighted mean of contracts that reported a number, and the gap from that mean | It does not recompute HEDIS from claims. The file has no numerator, so there is no Wilson interval. |
| CDC PLACES 2025 county file | County | Adult-population-weighted mean and each county's gap | It does not recompute the CDC small-area model. Diabetes here is prevalence, not HbA1c control. |

HRSA diabetes is **poor** glycemic status (>9% or missing). A higher rate is a wider gap. That is the opposite direction from the simulation's HbA1c < 8% flag, and the demo says so.

Licenses and the exact URLs are in [DATA_LICENSES.md](../DATA_LICENSES.md). The decision is [ADR 0008](adr/0008-public-hosted-data.md).

## Why this host

Neon’s free plan is $0, has no time limit, and does not ask for a credit card (checked 2026-11-18 at https://neon.com/pricing). It is Postgres, which is already what the SQL in this repo targets. One project includes 1 GB of storage and 100 CU-hours a month, and compute scales to zero after a few idle minutes. The public tables are a few megabytes.

Supabase’s free tier also offers Postgres, plus auth and storage this demo does not use, and it pauses inactive projects. Railway does not currently have a permanent $0 Postgres tier. Neon is the smaller fit.

Streamlit Community Cloud hosts a public app from a public GitHub repo at no charge. Viewers do not need an account. The app reads `CARE_OPS_PG_DSN` from an environment variable or from a Streamlit secret of the same name. Secrets stay in the host, not in the repo.

## Ordered checklist

Do these in order. Nothing below is stored in the repository.

1. **Neon Postgres — required.** Create a free project at https://neon.com (sign up, New project, Postgres 17 if offered). Open Connect and copy the connection string. Put it in the environment as `CARE_OPS_PG_DSN`. `DATABASE_URL` is accepted as the same value. Do not commit it. The URL contains a password.
2. **Load — required.** From this repo, with the variable set:

   ```bash
   python -m pip install -e .
   python -m care_ops_agent.public.load
   ```

   That downloads the three public files (no API key) and loads schema `published`. The command fails with the variable name if the URL is missing, and it refuses `localhost` unless `CARE_OPS_ALLOW_LOCAL=1` (CI and a laptop SQL check only). It also refuses to print the URL.
3. **GitHub Actions secret — required for a repeatable load.** In the GitHub repo, Settings → Secrets and variables → Actions → New repository secret. Name: `CARE_OPS_PG_DSN`. Value: the same Neon URL. Then run the workflow **Load published data** (`workflow_dispatch`). An empty secret fails the load on purpose.
4. **Streamlit Community Cloud — required for the hiring-manager URL.** Sign in at https://share.streamlit.io with the GitHub account that can see this repo. Deploy `streamlit_app.py` from the branch that contains it (or from `main` after merge). In the app’s secrets, set `CARE_OPS_PG_DSN` to the same URL. Share the app as public. Viewers do not get the secret.
5. **Asana — required only for a live tracker.** Free personal access token: https://app.asana.com/0/my-apps. Set `ASANA_BACKEND=live`, `ASANA_ACCESS_TOKEN`, and `ASANA_WORKSPACE_GID`. Until then, `LiveAsanaClient` raises `AsanaNotConfigured`. The offline CSV stays the CI path. The public demo does not call Asana.
6. **Salesforce — required only for a live CRM.** Free Developer Edition: https://developer.salesforce.com/signup. Set `SALESFORCE_BACKEND=live`, `SF_LOGIN_URL` (default `https://login.salesforce.com`), `SF_CLIENT_ID`, `SF_CLIENT_SECRET`, `SF_USERNAME`, `SF_PASSWORD`, and `SF_SECURITY_TOKEN`. Until then, `LiveSalesforceClient` raises `SalesforceNotConfigured`. The public demo does not call Salesforce.
7. **Tableau Public — required only for a Tableau publish.** There is still no publish API in this repo. Tableau Public and Tableau Desktop are free and need the owner’s account. The view a hiring manager can open without that account is the Streamlit app. Flat CSV extracts remain for a later manual publish.

`python -m care_ops_agent.public.status` prints the same list and whether the variables are present. It does not print the values.

## What a visitor can do after steps 1–4

Open the Streamlit URL. Choose a source and a measure. Filter by state (HRSA and PLACES) or by name. The comparator is national even when the table is filtered. Download the filtered table as CSV. The note under the metrics is the deterministic narration; the caption says the fidelity check passed. Turning on `LLM_BACKEND=ollama` is optional and local. A draft that adds a number is rejected.

## What stays offline

`pytest` does not download the public files and does not need Neon. Set `CARE_OPS_PUBLIC_DIR` to a folder that already holds `places_county_2025.csv`, `cms_star_ratings.zip`, and `H80-2025.xlsx` to run `tests/test_public_live.py` against those files.

The Socrata CSV export for PLACES carried a sunset date of 2026-12-22. If that URL starts failing, the loader’s error names the dataset page. Update `PLACES_CSV_URL` in `src/care_ops_agent/public/catalog.py` when CDC posts the replacement.
