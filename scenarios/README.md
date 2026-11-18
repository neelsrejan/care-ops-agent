# Scenarios (SYNTHETIC draws, public baselines where the construct matches)

Each YAML seeds one simulated network with a known injected truth so triage is scored against it.
The patient roster is still Synthea. The weekly visit is still a draw. The injected shocks
(`met_prob_after`, missing-feed shares) are still scenario parameters so the held-out truth stays known.

`baseline_met` is no longer a round guess for two measures. `bp_control` is 0.69 and
`breast_cancer_screening` is 0.56, the HRSA UDS 2025 pooled rates computed in Python on
2026-11-18 (exact values 0.6899 and 0.5625). See `src/care_ops_agent/public/baselines.py`.

`hba1c_control` stays 0.62. HRSA publishes poor glycemic status (>9% or missing), pooled at
26.1%, which is not HbA1c under 8%. CMS C12 was 87.6% on Medicare Advantage contracts.
Using that figure would turn the held-out near-threshold shock (a draw at 0.60) into a large
drop, so the scored experiment would change. It stays a scenario parameter.
