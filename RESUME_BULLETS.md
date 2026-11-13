# Resume bullets

Portfolio simulation only. These lines describe synthetic partner groups and synthetic patients. They are not a claim about a real panel, a real customer, or a production system. Numbers come from `python -m care_ops_agent.eval.harness`.

- Built a simulated care-gap closure program across 8 synthetic partner practices that finds where patients are falling behind on diabetes control, blood-pressure control, and breast cancer screening. On single-cause held-out scenarios, triage named the right practice and measure in 11 of 11 cases.
- Loaded synthetic patient records from local FHIR R4 files into PostgreSQL and wrote the SQL for three HEDIS-style measures, with data checks that must return zero bad rows. Every rate is computed in Python. The public Synthea sample is the roster only. Outcome probabilities are labeled scenario parameters, because that sample shows every diabetic patient already under an HbA1c of 8.0%.
- Separated care gaps from missing lab-result feeds so outreach is held when the problem is the data feed. The care-versus-data call matched the seeded truth in 11 of 11 single-cause scenarios, with 1 false alarm on 5 no-signal and near-threshold scenarios.
- Ran the simulation as weekly PDSA cycles, kept partner onboarding in a Salesforce-shaped stand-in, kept the plan in an Asana CSV import, and wrote Excel workbooks plus Tableau-ready extracts. Live Asana, Salesforce, and Tableau Public are not connected.
- Designed a simulated outreach A/B test on gaps closed, including the sample-size calculation and a two-proportion readout. The seeded effect was recovered in 20 of 20 runs, and the equal-rate version stayed quiet in 28 of 30 runs.
