"""Sources and measure definitions for the hosted public path.

Patient-level charts are not public. These three files are the free sources
that still match a care-gap story: health-center numerators, Medicare
Advantage contract rates, and county prevalence estimates.
"""

from __future__ import annotations

# Pinned after a successful download on 2026-11-18. The CMS page lists a
# newer zip first; download.py falls back to that page if this URL 404s.
CMS_PAGE_URL = "https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data"
CMS_ZIP_URL = "https://www.cms.gov/files/zip/2027-star-ratings-data-tables-oct-8-2026.zip"

# Socrata rows.csv for this dataset returns a Deprecation header with sunset
# 2026-12-22. The dataset page is the durable citation if that export moves.
PLACES_PAGE_URL = (
    "https://data.cdc.gov/500-Cities-Places/"
    "PLACES-County-Data-GIS-Friendly-Format-2025-releas/i46a-9kgh"
)
PLACES_CSV_URL = "https://data.cdc.gov/api/views/i46a-9kgh/rows.csv?accessType=DOWNLOAD"

HRSA_PAGE_URL = "https://data.hrsa.gov/topics/health-centers/uds"
HRSA_XLSX_URL = "https://data.hrsa.gov/DataDownload/StaticDocuments/H80-2025.xlsx"

SOURCES = {
    "hrsa_uds": {
        "title": "HRSA Health Center Program Awardee Data (H80), UDS 2025",
        "publisher": "Health Resources and Services Administration, Bureau of Primary Health Care",
        "vintage": "2025",
        "source_url": HRSA_XLSX_URL,
        "page_url": HRSA_PAGE_URL,
        "license": (
            "Free public UDS release. HRSA states the files are made available at no cost "
            "under FOIA 5 U.S.C. 552(a)(2)(D). Usage limitations on the UDS download: none. "
            "Not a government endorsement (42 U.S.C. 1320b-10)."
        ),
        "grain": "health center (BHCMIS ID), reporting year 2025",
        "notes": (
            "Numerators and denominators are the Table 6B and Table 7 health-center totals. "
            "Python divides them. Diabetes is poor glycemic status (>9% or missing), so a "
            "higher rate is worse. Blood pressure is controlled under 140/90. Mammography is "
            "women age 52–74. These are UDS definitions, not certified HEDIS."
        ),
    },
    "cms_stars": {
        "title": "CMS 2027 Medicare Advantage and Part D Star Ratings, measure data",
        "publisher": "Centers for Medicare & Medicaid Services",
        "vintage": "2027 Star Ratings, published 2026-10-08; Part C measurement period 2025",
        "source_url": CMS_ZIP_URL,
        "page_url": CMS_PAGE_URL,
        "license": (
            "U.S. government work, public domain. CMS asks for attribution and forbids a false "
            "impression of endorsement (42 U.S.C. 1320b-10)."
        ),
        "grain": "Medicare Advantage contract",
        "notes": (
            "Values are the percents CMS already published (C01 breast cancer screening, "
            "C12 diabetes care blood sugar controlled, C14 controlling high blood pressure). "
            "Python computes the unweighted mean of contracts that reported a number and the "
            "gap from that mean. It does not recompute the measure from claims. The file has "
            "no numerator, so there is no Wilson interval."
        ),
    },
    "cdc_places": {
        "title": "CDC PLACES county estimates, 2025 release, GIS-friendly format",
        "publisher": "Centers for Disease Control and Prevention",
        "vintage": "2025 release (county file last modified 2025-12-04)",
        "source_url": PLACES_CSV_URL,
        "page_url": PLACES_PAGE_URL,
        "license": (
            "U.S. government work, public domain. Cite CDC PLACES. No endorsement implied."
        ),
        "grain": "county",
        "notes": (
            "Crude prevalence: diagnosed diabetes, blood-pressure medication among adults with "
            "high blood pressure, and mammography among women 50–74. These are model-based "
            "BRFSS small-area estimates, not patient outcomes and not HEDIS. Python computes "
            "the adult-population-weighted mean and each county's gap. It does not recompute "
            "the CDC model. The Socrata CSV export carried a sunset of 2026-12-22."
        ),
    },
}

# direction higher_better: a rate under the comparator is a gap.
# direction lower_better: a rate over the comparator is a gap.
MEASURES = {
    "hrsa_uds": {
        "breast_cancer_screening": {
            "label": "Breast cancer screening (mammogram, women 52–74)",
            "direction": "higher_better",
            "mode": "counts",
        },
        "bp_control": {
            "label": "Controlling high blood pressure (<140/90)",
            "direction": "higher_better",
            "mode": "counts",
        },
        "diabetes_poor_control": {
            "label": "Diabetes poor glycemic status (>9% or missing)",
            "direction": "lower_better",
            "mode": "counts",
        },
    },
    "cms_stars": {
        "breast_cancer_screening": {
            "label": "C01 Breast cancer screening",
            "direction": "higher_better",
            "mode": "percent",
            "code": "C01",
        },
        "diabetes_blood_sugar_controlled": {
            "label": "C12 Diabetes care — blood sugar controlled",
            "direction": "higher_better",
            "mode": "percent",
            "code": "C12",
        },
        "bp_control": {
            "label": "C14 Controlling high blood pressure",
            "direction": "higher_better",
            "mode": "percent",
            "code": "C14",
        },
    },
    "cdc_places": {
        "diabetes_prevalence": {
            "label": "Diagnosed diabetes among adults",
            "direction": "lower_better",
            "mode": "weighted_percent",
            "places_id": "DIABETES",
        },
        "bp_medication": {
            "label": "Taking blood-pressure medicine, among adults with high blood pressure",
            "direction": "higher_better",
            "mode": "weighted_percent",
            "places_id": "BPMED",
        },
        "mammography": {
            "label": "Mammography among women 50–74",
            "direction": "higher_better",
            "mode": "weighted_percent",
            "places_id": "MAMMOUSE",
        },
    },
}

GAP_THRESHOLD_PP = 5.0
