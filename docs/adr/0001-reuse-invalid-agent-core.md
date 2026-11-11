# ADR 0001 — Reuse invalid-agent core modules
Status: accepted (S1, 2026-11-03)
Context: second portfolio project; same PM loop, new industry.
Decision: copy `metrics/rates.py`, `metrics/spc.py`, `metrics/pareto.py`, `guards/numeric_fidelity.py` unchanged; adapt `config.py` and a slimmed `llm.py`; reuse the Jira dry-run pattern and the CI workflow.
Consequences: proven, tested math on day 1; two copies to keep in sync (a shared package is a later option).
