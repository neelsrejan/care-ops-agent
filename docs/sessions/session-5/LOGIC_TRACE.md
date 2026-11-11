# Session 5 logic trace — program controls and the Asana stand-in

1. **Goal.** Give the simulated program a charter, a dated WBS, a RAID log, a change log, and a budget that a reviewer can open in Excel, plus a task file Asana can import.
2. **Needed next.** The weekly PDSA loop that spends those tasks (S6).
3. **Libraries.** openpyxl for the workbook. The standard library for dates and, later, MS Project XML. No Asana SDK.
4. **Code.** `controls/plan.py` schedules business days from Monday 2026-11-02, prices each leaf at a synthetic hourly rate, and refuses a plan whose assigned hours exceed funded capacity. CR-001 (lab-feed remediation) is outside the baseline, so forecast = baseline + change. `pm/asana.py` writes `SIM-` tasks and a CSV. `ASANA_BACKEND=live` is a separate class that reads `ASANA_ACCESS_TOKEN` and is not called here.
5. **Docs.** ADR 0005. Sample workbook in `docs/samples/`.
6. **Buy-in.** A live Asana workspace needs Neel's token. The CSV is the deliverable until then.
7. **Capability added.** `python -m care_ops_agent.run_program` writes `out/program_controls.xlsx` and `out/asana/asana_import.csv`.
8. **What it proves.** Project controls (WBS, RAID, change control, budget burn, capacity) on a synthetic care-gap program, with the dollars computed rather than typed into the narrative.
