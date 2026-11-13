# Held-out scenarios (SYNTHETIC)

`evals/heldout/*.yaml` is the 20-scenario score set. The four files in `scenarios/` (`clinic_bp_drop`, `missing_a1c_feed`, `partner_screening_gap`, `no_signal`) are the dev set and are excluded from the score.

Families: clinic care gap ×3, partner-wide gap ×3, missing feed ×3, missing feed on a measure other than the dev HbA1c case ×2, onboarding stall ×2, mixed causes ×2, no-signal ×3, near-threshold ×2.

Near-threshold cases inject a shift of about two points, under the 10-point flag rule. A quiet scenario can still flag a different cell by chance. The scaling rule treats any such flag as a failed gate. See `docs/EVAL_REPORT.md`.

```bash
python -m care_ops_agent.eval.harness
```
