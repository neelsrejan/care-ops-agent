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

Streamlit Community Cloud hosts a public app from a public GitHub repo at no charge. Viewers do not need an account. The app reads `CARE_OPS_PG_DSN` and `ASANA_*` from the environment, and, when those are empty, from Streamlit secrets of the same names. An environment variable that is already set is left alone. Secrets stay in the host, not in the repo.

## Ordered checklist

Do these in order. Nothing below is stored in the repository.

1. **Neon Postgres — required.** Create a free project at https://neon.com (sign up, New project, Postgres 17 if offered). Open Connect and copy the connection string. Put it in the environment as `CARE_OPS_PG_DSN`. `DATABASE_URL` is accepted as the same value. Do not commit it. The URL contains a password.
2. **Load — required.** From this repo, with the variable set:

   ```bash
   python -m pip install -e ".[dev]"
   python -m care_ops_agent.public.load
   ```

   The `dev` extra includes Streamlit. Streamlit Community Cloud installs `requirements.txt` from the repo root instead of the extra. Either install is enough to run `streamlit run streamlit_app.py` on a laptop.

   That downloads the three public files (no API key) and loads schema `published`. The command fails with the variable name if the URL is missing, and it refuses `localhost` unless `CARE_OPS_ALLOW_LOCAL=1` (CI and a laptop SQL check only). It also refuses to print the URL.
3. **GitHub Actions secret — required for a repeatable load.** In the GitHub repo, Settings → Secrets and variables → Actions → New repository secret. Name: `CARE_OPS_PG_DSN`. Value: the same Neon URL. Then run the workflow **Load published data** (`workflow_dispatch`). An empty secret fails the load on purpose.
4. **Streamlit Community Cloud — required for the hiring-manager URL.** Sign in at https://share.streamlit.io with the GitHub account that can see this repo. Deploy `streamlit_app.py` from the branch that contains it (or from `main` after merge). In the app’s Advanced settings, paste the secrets block below. Share the app as public. Viewers do not get the secrets. The page never creates Asana tasks.
5. **Asana — required.** Free personal access token: https://app.asana.com/0/my-apps. Set `ASANA_BACKEND=live`, `ASANA_ACCESS_TOKEN`, and `ASANA_WORKSPACE_GID` in the environment and in the Streamlit secrets. Until those are set, the demo raises `PortfolioNotConfigured`. Once they are set, `python -m care_ops_agent.public.status` says Asana is connected and does not say "pending owner credentials". Then run the owner-only seed, which creates the project and tasks:

   ```bash
   python -m care_ops_agent.pm.asana seed
   ```

   The project name is `Care-gap work plan`. The command finds that project by exact name, or creates it, then creates each plan task only when that exact name is not already in the project. A second run creates 0 tasks. It prints the project URL. The public page only reads that project: the link, the open count, the complete count, and each task status. Visitors cannot create anything. CI still uses the offline CSV client and does not call Asana.
6. **Salesforce Developer Edition — required, pending owner credentials.** Free org: https://developer.salesforce.com/signup. Set `SALESFORCE_BACKEND=live`, `SF_LOGIN_URL` (default `https://login.salesforce.com`), `SF_CLIENT_ID`, `SF_CLIENT_SECRET`, `SF_USERNAME`, `SF_PASSWORD`, and `SF_SECURITY_TOKEN`. Until those are set, the demo raises and does not invent a login. Once set, the page logs in read-only and shows the org host and the Account count.
7. **Tableau Public — required, pending owner credentials.** Tableau Public and Tableau Desktop are free: https://public.tableau.com. There is still no publish API. Publish the workbook from the CSV extracts, then set `TABLEAU_PUBLIC_URL` to the `https://public.tableau.com/...` viz link. Any other host is rejected. Until that is set, the demo raises and does not invent a dashboard URL. Once set, the page shows the link.

`python -m care_ops_agent.public.status` prints the same list and exits 1 while Neon, Asana, Salesforce, or Tableau Public is unset. It does not print secret values. When Asana’s three variables are set, that line says connected. Streamlit and the GitHub secret are required too, and this command cannot see them (`not visible here`).

Streamlit Community Cloud secrets, names only. Paste this into the app secrets and fill the values there. Do not commit the file.

```toml
CARE_OPS_PG_DSN = ""
DATABASE_URL = ""
ASANA_BACKEND = ""
ASANA_ACCESS_TOKEN = ""
ASANA_WORKSPACE_GID = ""
SALESFORCE_BACKEND = ""
SF_LOGIN_URL = ""
SF_CLIENT_ID = ""
SF_CLIENT_SECRET = ""
SF_USERNAME = ""
SF_PASSWORD = ""
SF_SECURITY_TOKEN = ""
TABLEAU_PUBLIC_URL = ""
```

`ASANA_BACKEND` and `SALESFORCE_BACKEND` must be the value `live` in that file for the hosted app. `SF_LOGIN_URL` is `https://login.salesforce.com` unless the org uses another login host.

## What a visitor sees

Open the Streamlit URL. Choose a source and a measure. Filter by state (HRSA and PLACES) or by name. The comparator is national even when the table is filtered. Download the filtered table as CSV. The note under the metrics is the deterministic narration; the caption says the fidelity check passed.

The page also has **Required connections**. Until steps 5–7 are in the Streamlit secrets, that section is an error naming the variables. After they are set, it shows the Asana project link plus each task’s open or complete status, the Salesforce org and Account count, and the Tableau Public link. The page does not create Asana tasks. Turning on `LLM_BACKEND=ollama` is a local prose option. A draft that adds a number is rejected.

## What stays offline

`pytest` does not download the public files and does not need Neon. Set `CARE_OPS_PUBLIC_DIR` to a folder that already holds `places_county_2025.csv`, `cms_star_ratings.zip`, and `H80-2025.xlsx` to run `tests/test_public_live.py` against those files.

The bulk Socrata CSV for PLACES carried a sunset date of 2026-12-22. The loader tries that URL, then the SODA CSV (`/resource/i46a-9kgh.csv`), then the pinned archive `data/published/places_county_2025.csv`. Headers are matched without case, because SODA lowercases them. Re-run the load after this change so Neon picks up `percent_status` on the HRSA rows.
