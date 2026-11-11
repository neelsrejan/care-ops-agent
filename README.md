# care-ops-agent · SIMULATION
Healthcare delivery portfolio project: an agent that helps a simulated provider network **close care gaps** (HEDIS-style HbA1c control, BP control, breast cancer screening) so more patients reach better outcomes. Public CMS + Synthea (FHIR R4) seeds; all program data synthetic. See PRD.md, ROADMAP.md, PLAN.md, SIMULATION_DISCLAIMER.md, DATA_LICENSES.md.

Stack: Python · PostgreSQL views · FHIR R4 · Asana (backlog CSV) · Salesforce-shaped CRM stand-in · Excel (openpyxl) · Tableau Public extracts · Lean/PDSA.

```bash
pip install -e ".[dev]" && pytest                     # 20 tests, no DB required
python -m care_ops_agent.data.download                # CMS CSV + Synthea CSV sample
#  FHIR R4 1K sample: see DATA_LICENSES.md (data/raw/synthea_fhir)
export CARE_OPS_PG_DSN=postgresql://postgres@localhost:5433/care_ops
python -m care_ops_agent.data.load                    # raw tables + views + SQL tests
python -m care_ops_agent.run_triage scenarios/*.yaml  # care-gap triage memos -> out/
python -m care_ops_agent.run_pipeline scenarios/clinic_bp_drop.yaml   # CRM export, xlsx, Tableau CSV, account plans
```
Status: Sessions 1–4 done (2026-11-03). Session 5 not started.
