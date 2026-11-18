# ADR 0008 — Public rates live in hosted Postgres; Synthea stays offline
Status: accepted (2026-11-18)

The portfolio has to be queryable by someone who is not on the author's machine, on free tiers, with real public data. Patient-level charts are not public, so the hosted tables are aggregates:

- HRSA UDS 2025 health-center numerators and denominators (blood pressure control, diabetes poor glycemic status, mammography).
- CMS 2027 Star Ratings contract percents for the same three HEDIS measures (C14, C12, C01).
- CDC PLACES 2025 county crude prevalence (diabetes, blood-pressure medication, mammography) as geographic context.

Python computes every rate, pooled comparator, gap, and Wilson interval. SQL stores and checks inputs. A model may only rewrite the note, and the numeric-fidelity guard still applies. The public note is not labeled synthetic.

Neon is the database because the free plan is $0 without a credit card and it is plain Postgres. Streamlit Community Cloud is the demo because a public app is free to view and can hold `CARE_OPS_PG_DSN` as a secret. The loader refuses a missing URL and refuses localhost unless `CARE_OPS_ALLOW_LOCAL=1`. It refuses to load Synthea into a non-local database.

The weekly Harbor simulation, the outreach draws, the RFP bank, and the Asana and Salesforce offline clients stay the CI path. Asana, Salesforce, and Tableau Public still need the owner's accounts; those clients fail clearly when the variables are empty. No quiz question became false, because those modules still behave as the sessions describe. The hospital general-information file is still only a name seed. Star Ratings are a different CMS file.

The connection string is never written into the repo.
