# ADR 0004 — Salesforce-shaped local CRM until the Developer Edition org exists
Status: accepted (S4)
Objects mirror Account / Contact / Opportunity (+ stage history). `export_salesforce_csv` writes Data Import Wizard CSVs so the same SYNTHETIC records load into a free Developer Edition org later. No account created by the agent.
