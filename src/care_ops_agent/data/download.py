"""Download the public seed data (real files; nothing generated here).

CMS: resolve the CSV link from the PDC metastore (CMS guidance: don't hard-code).
Synthea: 1K-patient CSV sample (Apr 2020) and 1K-patient FHIR R4 sample (Sep 2019).
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date
from pathlib import Path

import httpx

from care_ops_agent.config import find_repo_root

CMS_DATASET = "xubh-q36u"  # Hospital General Information
CMS_META = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{id}"
SYNTHEA_URL = "https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_apr2020.zip"
SYNTHEA_FHIR_URL = "https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_fhir_r4_sep2019.zip"


def cms_download_url(dataset_id: str = CMS_DATASET) -> tuple[str, dict]:
    meta = httpx.get(CMS_META.format(id=dataset_id), timeout=60).json()
    url = next(d["downloadURL"] for d in meta["distribution"] if d.get("mediaType") == "text/csv")
    return url, {"title": meta.get("title"), "modified": meta.get("modified"), "url": url}


def main() -> None:
    raw = find_repo_root() / "data" / "raw"
    (raw / "cms").mkdir(parents=True, exist_ok=True)
    (raw / "synthea").mkdir(parents=True, exist_ok=True)
    url, meta = cms_download_url()
    (raw / "cms" / "Hospital_General_Information.csv").write_bytes(httpx.get(url, timeout=120).content)
    blob = httpx.get(SYNTHEA_URL, timeout=300, follow_redirects=True).content
    zipfile.ZipFile(io.BytesIO(blob)).extractall(raw / "synthea")
    fhir = httpx.get(SYNTHEA_FHIR_URL, timeout=600, follow_redirects=True).content
    zipfile.ZipFile(io.BytesIO(fhir)).extractall(raw / "synthea_fhir")
    meta.update({"synthea_url": SYNTHEA_URL, "synthea_fhir_url": SYNTHEA_FHIR_URL, "downloaded": date.today().isoformat()})
    (raw / "download_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
