# HEDIS-style measure definitions (simplified; SIMULATION — not certified measure logic)

Patient-level rows from PostgreSQL views in `sql/views/` (Synthea FHIR R4); rates computed in Python (`metrics/measures.py`), measurement year = the latest year in the extract.

| Measure | Denominator | Numerator (= "met") | Synthea codes |
|---|---|---|---|
| hba1c_control | living patients age 18–75 with Diabetes (SNOMED 44054006); no result = gap open | latest HbA1c (LOINC 4548-4) < 8.0 % | 44054006, 4548-4 |
| bp_control | living patients age 18–85 with Hypertension (SNOMED 59621000); no reading = gap open | latest systolic (8480-6) < 140 **and** diastolic (8462-4) < 90 | 59621000; BP panel 85354-9 or 55284-4 with components 8480-6, 8462-4 |
| breast_cancer_screening | living women age 52–74 at end of year | any mammography procedure (SNOMED 71651007, 24623002, 241055006) in the 27 months before year end | as listed |

A **gap** = denominator patient not meeting the numerator. Gap rate = 1 − met rate.
