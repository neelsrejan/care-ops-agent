# Held-out eval report

SYNTHETIC SIMULATION. The four dev scenarios (`clinic_bp_drop`, `missing_a1c_feed`, `partner_screening_gap`, `no_signal`) are not in this score. Numbers come from `care_ops_agent.eval.harness`.

Decision: **NO-GO**.

The scaling rule requires zero false alarms on no-signal and near-threshold weeks. A chance flag in a cell that was not the injected shift keeps the decision at NO-GO. The other gates passed on this run.

## Gates

| Gate | Result | Evidence | Rule |
|---|---|---|---|
| numeric_fidelity | pass | 20 of 20 | every held-out memo passed the numeric-fidelity guard |
| partner_leaks | pass | 0 | partner updates named no other partner |
| false_alarms | fail | 1 of 5 | no-signal and near-threshold scenarios stayed quiet |
| single_cause_top1 | pass | 11 of 11 | at least 80% of single-cause held-out scenarios named the right practice and measure |
| care_vs_data | pass | 11 of 11 | at least 80% of single-cause care-versus-data calls matched |
| mixed_causes | pass | 2 of 2 | both shocks were flagged in every mixed scenario |
| onboarding_stalls | pass | 2 of 2 | every seeded stalled account was marked stalled |
| ab_effect | pass | 20 of 20 | the seeded outreach effect was recovered in at least 80% of runs |
| ab_null | pass | 28 of 30 | the equal-rate outreach test stayed quiet in at least 80% of runs |

## Failure taxonomy

- correct: 19
- false_alarm: 1

## Scenario results

| Scenario | Family | Failure |
|---|---|---|
| hold_clinic_bp_p1_c1 | clinic_gap | correct |
| hold_clinic_a1c_p5_c3 | clinic_gap | correct |
| hold_clinic_bcs_p7_c2 | clinic_gap | correct |
| hold_partner_a1c_p3 | partner_gap | correct |
| hold_partner_bp_p6 | partner_gap | correct |
| hold_partner_bcs_p8 | partner_gap | correct |
| hold_feed_a1c_p2 | missing_feed | correct |
| hold_feed_a1c_p4 | missing_feed | correct |
| hold_feed_a1c_p7 | missing_feed | correct |
| hold_feed_bp_p3 | other_measure_feed | correct |
| hold_feed_bcs_p5 | other_measure_feed | correct |
| hold_stall_p3 | stall | correct |
| hold_stall_p6 | stall | correct |
| hold_mixed_bp_and_a1c | mixed | correct |
| hold_mixed_bcs_and_bp | mixed | correct |
| hold_quiet_a | no_signal | correct |
| hold_quiet_b | no_signal | correct |
| hold_quiet_c | no_signal | correct |
| hold_near_bp_p2 | near_threshold | false_alarm |
| hold_near_a1c_p4 | near_threshold | correct |
