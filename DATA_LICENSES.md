# Data sources and licenses

## Hosted public files (verified 2026-11-18)

These are the files the hosted demo loads. No account and no API key. Patient-level rows are not in these files.

| Source | File | How downloaded | License / terms | What this project computes |
|---|---|---|---|---|
| HRSA Health Center Program Awardee Data (H80), UDS reporting year 2025 | `data/raw/public/H80-2025.xlsx` (gitignored, about 28 MB) | https://data.hrsa.gov/DataDownload/StaticDocuments/H80-2025.xlsx — linked from https://data.hrsa.gov/topics/health-centers/uds | HRSA publishes the UDS files for free under FOIA 5 U.S.C. 552(a)(2)(D). The UDS download terms say usage limitations: none. Suppressed cells (`-`, `--`) are not treated as zeros. No endorsement implied. | Python divides Table 6B mammography counts and the Table 7 health-center totals for blood-pressure control (`T7_Li_C2a` / `T7_Li_C2c`) and diabetes poor glycemic status (`T7_Li_C3a` / `T7_Li_C3f`). |
| CMS 2027 Part C and D Star Ratings Data Tables (Oct 8, 2026) | `data/raw/public/cms_star_ratings.zip` | https://www.cms.gov/files/zip/2027-star-ratings-data-tables-oct-8-2026.zip — index https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data | U.S. government work, public domain. Attribute CMS. No false impression of endorsement (42 U.S.C. 1320b-10). | Python reads the published percents for C01, C12, and C14 and computes the unweighted mean and gaps. It does not recompute the measure. |
| CDC PLACES county data, GIS-friendly format, 2025 release (dataset `i46a-9kgh`, last modified 2025-12-04) | `data/raw/public/places_county_2025.csv` (download) and pinned `data/published/places_county_2025.csv` | Bulk CSV https://data.cdc.gov/api/views/i46a-9kgh/rows.csv?accessType=DOWNLOAD , then SODA https://data.cdc.gov/resource/i46a-9kgh.csv , then the pinned archive. Page https://data.cdc.gov/500-Cities-Places/PLACES-County-Data-GIS-Friendly-Format-2025-releas/i46a-9kgh | U.S. government work, public domain. Cite CDC PLACES. Methods: https://www.cdc.gov/places/ . The bulk CSV export returned a sunset header of 2026-12-22. | Python computes the adult-population-weighted mean of the crude prevalence values. It does not recompute the small-area model. Measures: `DIABETES`, `BPMED`, `MAMMOUSE`. |

Checked by downloading each file on 2026-11-18. Autauga County, Alabama, crude diagnosed-diabetes prevalence in the PLACES file is 13.3% with published interval (11.4, 15.3). CMS contract H0028, C01 Breast Cancer Screening, is the published 77%. HRSA health center 010030 (Holyoke Health Center) mammography is 1,565 / 2,187, and the workbook's published percent 71.56 matches that division within rounding.

## Original files (verified 2026-11-03)

| Source | File(s) | How downloaded | License / terms | Attribution |
|---|---|---|---|---|
| CMS Provider Data Catalog: *Hospital General Information* (dataset `xubh-q36u`, modified 2026-07-22) | `data/raw/cms/Hospital_General_Information.csv` (5,419 rows) | CSV link resolved from the PDC metastore API (CMS guidance: don't hard-code URLs) | US-government work, public domain. CMS API FAQ: "Works of the U.S. Government are in the public domain… attribution to the agency as the source is appreciated"; no false impression of endorsement (42 U.S.C. 1320b-10). No separate dataset license listed. | Centers for Medicare & Medicaid Services, data.cms.gov/provider-data |
| Synthea 1K-patient **FHIR R4** sample (Sep 2019) — used for the measures | `data/raw/synthea_fhir/fhir/*.json` (1,180 patient bundles) | https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_fhir_r4_sep2019.zip | Synthea software Apache-2.0 (repo LICENSE checked 2026-11-03). Downloads page: data "free from cost, privacy, and security restrictions… can be used without restriction". | Walonoski J, et al. JAMIA 25(3):230–238, 2018. doi:10.1093/jamia/ocx079 |
| Synthea 1K-patient CSV sample (Apr 2020) — first look only | `data/raw/synthea/csv/*.csv` | https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_apr2020.zip | same as above | same |
| HAPI FHIR R4 public test server | adapter only (`fhir/hapi.py`); capability check returned HTTP 200 on 2026-11-03 | https://hapi.fhir.org/baseR4 | Public test server: no credentials, data purged regularly, synthetic data only, never PHI. Uploads are off by default. | — |
| Synthetic (this repo) | scenarios/, out/ | generated | MIT | labeled SYNTHETIC |
