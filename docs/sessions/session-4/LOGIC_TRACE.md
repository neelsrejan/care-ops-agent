# Session 4 logic trace — Salesforce-shaped partner pipeline (2026-11-03)
Snapshot: `snapshots/session-4.zip`.

1. **Goal.** Know which partners can start outreach now, and where onboarding is stuck.
2. **Needed next.** S5 controls workbook + Asana plan.
3. **Libraries.** openpyxl (Excel output, approved instead of pptx), csv (Salesforce Data Import Wizard files, Tableau extract).
4. **Code.**
   - `crm/mock.py`: Account/Contact/Opportunity/stage history in Salesforce shape. Stages: Prospect → Qualified → Agreement (simulated) → Data Onboarding → Live. Exports CSVs.
   - `metrics/pipeline.py`:
     - stage counts and stage-to-stage conversion;
     - days in stage, with stalled meaning more than 14 days and not Live;
     - open gaps per partner, based on each patient's latest result;
     - readiness × gaps.
   - `export/workbook.py`: banner-labeled xlsx.
   - `run_pipeline.py`: writes `out/crm_export/`, the xlsx, the Tableau CSV, and account plans with a stakeholder map template.
5. **Bug caught.** The first run marked 13 of 14 opportunities stalled because the stage dates were generated forward from the start date. The fix gives time-in-current-stage 1–30 days.
6. **Buy-in needed.** Neel creates a free Salesforce Developer Edition org to import the CSVs; the agent creates no accounts.
7. **Capability added.** `python -m care_ops_agent.run_pipeline scenarios/clinic_bp_drop.yaml`.
8. **What it proves.** CRM pipeline hygiene tied to patient outcomes (open gaps), not just deal counts.
