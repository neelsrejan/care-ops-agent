# data/ (raw is gitignored)

Downloaded 2026-11-03 (`python -m care_ops_agent.data.download`).

| File | Rows | Source |
|---|---|---|
| raw/cms/Hospital_General_Information.csv | 5,419 | CMS PDC xubh-q36u (modified 2026-07-22) |
| raw/synthea_fhir/fhir/*.json | 1,180 patient bundles | Synthea FHIR R4 1K sample (Sep 2019) |
| raw/synthea/csv/*.csv | 1,171 patients | Synthea CSV 1K sample (Apr 2020), first look only |

Loaded into PostgreSQL (`raw.*`, 2026-11-03): patient 1,180 · condition 431 (diabetes + hypertension only) · observation 31,598 (HbA1c + BP components) · procedure 221 (mammography) · cms_hospital 5,419.

## Baseline check (Synthea FHIR R4 sample, measurement year end 2019-12-31; computed in Python)
| HEDIS-style measure (simplified) | Denominator | Met | Met rate |
|---|---|---|---|
| HbA1c control (<8.0%) | 58 | 58 | 100.0% |
| BP control (<140/90) | 255 | 217 | 85.1% |
| Breast cancer screening | 142 | 13 | 9.2% |

**Finding (both Synthea samples):** HbA1c values run 2.5–7.6%, so every diabetic patient is "controlled" and some values are physiologically implausible; screening is near zero. So Synthea supplies the **patient roster and denominator membership**, while outcome probabilities per partner come from the **synthetic scenario parameters** (scenarios/*.yaml), labeled as such. A fresh, larger Synthea run (needs Java) could replace this later.
