# ADR 0003 — SQL views return patient-level rows; Python computes every rate
Status: accepted (S2)
Views (`sql/views/`) decide denominator membership and latest results per patient. `metrics/measures.py` counts and computes rates + Wilson intervals. SQL tests (`sql/tests/`) must return zero rows.
Why: one place for numbers (Python, unit-tested), SQL readable by analysts, portable to any Postgres.
