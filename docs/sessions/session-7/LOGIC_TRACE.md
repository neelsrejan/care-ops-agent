# Session 7 logic trace — outreach A/B as a PDSA cycle

1. **Goal.** Size a two-arm outreach test, randomize synthetic patients, and read gaps closed. Recover a seeded effect. Stay quiet when the two scripts match.
2. **Needed next.** A place to file the method when a payer asks (S8).
3. **Libraries.** numpy for the draws, scipy for the normal quantiles and the two-proportion p-value. No experiment platform.
4. **Code.** `experiment/ab.py` computes the equal-arm sample size for a two-sided test at 90% power, shuffles arm labels, and draws a closed-gap outcome per patient. The decision is scale B, scale A, or no difference. `pdsa_from_trial` maps that decision onto adopt or abandon so the test is a PDSA cycle, not a side analysis.
5. **Docs.** The seeded rates (0.22 and 0.48, null 0.35) are scenario parameters, not Synthea outputs.
6. **Buy-in.** None. There is no live outreach vendor.
7. **Capability added.** `out/ab_trial.json`, and the repeat counts in the eval report.
8. **What it proves.** Power, randomization, and a readout whose numbers are not written by a model.
