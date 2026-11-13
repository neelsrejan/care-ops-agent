# Data sources and licenses (verified 2026-11-03)

| Source | File(s) | How downloaded | License / terms | Attribution |
|---|---|---|---|---|
| CMS Provider Data Catalog: *Hospital General Information* (dataset `xubh-q36u`, modified 2026-07-22) | `data/raw/cms/Hospital_General_Information.csv` (5,419 rows) | CSV link resolved from the PDC metastore API (CMS guidance: don't hard-code URLs) | US-government work, public domain. CMS API FAQ: "Works of the U.S. Government are in the public domain… attribution to the agency as the source is appreciated"; no false impression of endorsement (42 U.S.C. 1320b-10). No separate dataset license listed. | Centers for Medicare & Medicaid Services, data.cms.gov/provider-data |
| Synthea 1K-patient **FHIR R4** sample (Sep 2019) — used for the measures | `data/raw/synthea_fhir/fhir/*.json` (1,180 patient bundles) | https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_fhir_r4_sep2019.zip | Synthea software Apache-2.0 (repo LICENSE checked 2026-11-03). Downloads page: data "free from cost, privacy, and security restrictions… can be used without restriction". | Walonoski J, et al. JAMIA 25(3):230–238, 2018. doi:10.1093/jamia/ocx079 |
| Synthea 1K-patient CSV sample (Apr 2020) — first look only | `data/raw/synthea/csv/*.csv` | https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_apr2020.zip | same as above | same |
| HAPI FHIR R4 public test server | adapter only (`fhir/hapi.py`); capability check returned HTTP 200 on 2026-11-03 | https://hapi.fhir.org/baseR4 | Public test server: no credentials, data purged regularly, synthetic data only, never PHI. Uploads are off by default. | — |
| Synthetic (this repo) | scenarios/, out/ | generated | MIT | labeled SYNTHETIC |
