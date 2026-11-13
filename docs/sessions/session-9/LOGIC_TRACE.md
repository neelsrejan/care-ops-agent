# Session 9 logic trace — held-out eval and MS Project XML

1. **Goal.** Score about 20 scenarios the dev set did not tune, name the failure when a case misses, and export the WBS as MS Project XML.
2. **Needed next.** The go/no-go sheet and the resume lines that quote this report (S10).
3. **Libraries.** The triage, CRM, and A/B modules. `xml.etree` for MSPDI. No eval SaaS.
4. **Code.** `eval/catalog.py` is the 20-scenario list. `eval/harness.py` scores top-1 on single-cause cases, care-versus-data (the same call), mixed shocks, stalled onboarding, numeric fidelity, and partner-note leaks. The failure taxonomy is correct, false alarm, missed signal, wrong partner, wrong measure, wrong kind, wrong clinic, mixed incomplete, stall miss, fidelity fail, partner leak. Dev scenario ids are refused. `export/mspdi.py` writes finish-to-start links (type 1) for the same plan Excel already shows. Asana's free plan has no dependencies, so the Gantt lives here.
5. **Docs.** `docs/EVAL_REPORT.md` and `evals/README.md`.
6. **Buy-in.** None.
7. **Capability added.** `python -m care_ops_agent.eval.harness`.
8. **What it proves.** A labeled held-out set with an explicit failure taxonomy, and a schedule file a desktop Project client can open.
