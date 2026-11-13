# Session 10 logic trace — extracts, the go/no-go, the README

1. **Goal.** Hand a reviewer Tableau-ready files, a written dashboard spec, a scaling decision computed from the eval, and resume bullets whose numbers are that eval.
2. **Needed next.** Neel's Tableau Public account if the workbook should be a public URL. The spec and the local preview stand until then.
3. **Libraries.** openpyxl and the csv module. No Tableau SDK.
4. **Code.** `export/tableau.py` flattens weekly rates, the pipeline, the PDSA log, and the budget burn to scalar columns. `export/preview.py` is an HTML table, labeled as not Tableau. `eval/harness.py` turns gate results into GO or NO-GO. On this build every gate passes except false alarms (1 of 5 quiet scenarios), so the decision is NO-GO. `resume_bullets` fills the resume from that same dict. `run_program.py` is the one command that writes the pack without PostgreSQL.
5. **Docs.** `docs/tableau/DASHBOARD_SPEC.md`, `RESUME_BULLETS.md`, `README.md`.
6. **Buy-in.** Tableau Public publish, Asana import, and Salesforce import are manual once Neel has the accounts.
7. **Capability added.** `out/tableau/`, `out/scaling_gonogo.xlsx` when `--eval` is set, and the resume file.
8. **What it proves.** A close-out pack whose claims match the harness, including the decision not to scale.
