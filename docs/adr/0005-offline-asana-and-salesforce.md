# ADR 0005 — Asana and Salesforce stay behind an offline default
Status: accepted (S5)

Neel has not provided Asana or Salesforce credentials. The demo and the tests construct `OfflineAsanaClient` and `OfflineSalesforceClient`. Those write an Asana CSV import (`SIM-` gids) and Salesforce Data Import Wizard CSVs. `ASANA_BACKEND=live` and `SALESFORCE_BACKEND=live` build the HTTP clients, and they raise a clear configuration error when the environment variables are empty. No token is hard-coded. The live classes are not called by `run_program` or by pytest.
