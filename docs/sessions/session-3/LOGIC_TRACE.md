# Session 3 logic trace — network sim + care-gap triage (2026-11-03)
Snapshot: `snapshots/session-3.zip`.

1. **Goal.** Find where patients are falling behind, and say whether it's care or data.
2. **Needed next.** S4 joins open gaps per partner with pipeline stage.
3. **Libraries.** numpy (seeded RNG), pandas, scipy (normal tail for the z-test), pyyaml (scenarios as data).
4. **Code.**
   - `sim/network.py`: 8 CA acute-care facilities as SYNTHETIC partner seeds; 3 clinics each; 300 Synthea-roster patients per partner per measure; weekly visits (25%); injected truth from YAML.
   - `nodes/triage.py`:
     - baseline (weeks 1–13) vs program (14–20) per partner and clinic cell;
     - one-sided two-proportion test with per-level Bonferroni (24 partner cells, 72 clinic cells);
     - Wilson CI; p-chart rule hits;
     - "data issue" when ≥20% of recent visits lack a result and that share jumped ≥20 points;
     - the memo goes through the guard.
5. **Iterations.**
   - First pass flagged a false alarm on `no_signal`, which is the multiple-comparisons problem. The fix was Bonferroni.
   - That then missed the clinic signal at 120 patients per partner per measure, so the panel went to 300 with alpha per level.
   - All 4 dev scenarios are now recovered. Because these were tuned against, this is NOT an eval result.
6. **Buy-in needed.** Neel: ~20 min sanity check of scenarios/*.yaml and the baseline rates.
7. **Capability added.** `python -m care_ops_agent.run_triage scenarios/*.yaml` → out/*_triage.md.
8. **What it proves.** Prioritizing patient outreach with statistics a reviewer can check, and not sending outreach for a data problem.
