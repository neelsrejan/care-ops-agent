# ADR 0002 — Stack differs from invalid-agent
Status: ACCEPTED 2026-11-03 18:38 PT (Neel). Research: TOOL_RESEARCH.md
| Need | invalid-agent | care-ops-agent |
|---|---|---|
| PM tool | Jira | **Asana** (CSV import now; API later) |
| Dashboard | Streamlit | **Tableau Public** (flat CSV extracts in out/tableau/ now) |
| Exec output | python-pptx | **Excel via openpyxl** |
| Data layer | dbt + DuckDB | **PostgreSQL + plain SQL views** (local PG 17 on the box, port 5433) |
| CRM | — | **Salesforce Developer Edition** (Salesforce-shaped local stand-in + Data Import Wizard CSVs now) |
| Clinical data | — | **FHIR R4** (Synthea R4 bundles; HAPI public test server adapter, read-only by default) |
| Measures | — | **HEDIS-style** simplified measures (never called "HEDIS") |
| Method | 8D/CAPA, DMAIC | **Lean / PDSA cycles** |
| Orchestration | LangGraph | **plain Python** functions |
| Numbers | Python | Python (rates computed in Python from patient-level SQL rows) |
Kept from invalid-agent: Python, pytest, GitHub Actions, the numeric-fidelity guard and stats modules, optional local LLM (Ollama) for prose only.
