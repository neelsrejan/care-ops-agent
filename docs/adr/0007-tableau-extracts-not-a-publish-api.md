# ADR 0007 — Tableau gets extracts and a spec, not an API call
Status: accepted (S10)

Tableau Public publishing needs Neel's account and Tableau Desktop. This repo writes flat CSV extracts (one scalar per cell) and `docs/tableau/DASHBOARD_SPEC.md`. A `.hyper` extract is created inside Tableau from those CSVs. `out/tableau/preview.html` is a local table preview so a reviewer can see the rows without Tableau. It is not a published dashboard.
