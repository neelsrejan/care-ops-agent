"""Download the three public files. No token and no account."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import httpx

from care_ops_agent.public.catalog import (
    CMS_PAGE_URL,
    CMS_ZIP_URL,
    HRSA_XLSX_URL,
    PLACES_CSV_URL,
    PLACES_PAGE_URL,
)

_ZIP_HREF = re.compile(r'href="(/files/zip/20\d{2}-star-ratings-data-tables[^"]+\.zip)"')


def cms_zip_url(client: httpx.Client | None = None) -> str:
    own = client is None
    client = client or httpx.Client(timeout=60, follow_redirects=True)
    try:
        return _cms_zip_url(client)
    finally:
        if own:
            client.close()


def _cms_zip_url(client: httpx.Client) -> str:
    status = "request failed"
    try:
        head = client.head(CMS_ZIP_URL)
        status = str(head.status_code)
        if head.status_code == 200:
            return CMS_ZIP_URL
    except httpx.HTTPError:
        status = "request failed"
    try:
        page = client.get(CMS_PAGE_URL)
        page.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"CMS star-ratings zip was not found. Tried {CMS_ZIP_URL} (HTTP {status}) "
            f"and {CMS_PAGE_URL}. {type(exc).__name__}."
        ) from exc
    match = _ZIP_HREF.search(page.text)
    if match is None:
        raise RuntimeError(
            f"CMS star-ratings zip was not found. Tried {CMS_ZIP_URL} "
            f"(HTTP {status}) and {CMS_PAGE_URL}."
        )
    return "https://www.cms.gov" + match.group(1)


def download_all(folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    targets = {
        "places": (PLACES_CSV_URL, folder / "places_county_2025.csv"),
        "cms": (cms_zip_url(), folder / "cms_star_ratings.zip"),
        "hrsa": (HRSA_XLSX_URL, folder / "H80-2025.xlsx"),
    }
    written: dict[str, Path] = {}
    with httpx.Client(timeout=180, follow_redirects=True) as client:
        for key, (url, dest) in targets.items():
            _download(client, url, dest, hint=_hint(key))
            written[key] = dest
    return written


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hint(key: str) -> str:
    if key == "places":
        return (
            f"CDC PLACES CSV failed. The Socrata export for {PLACES_PAGE_URL} "
            "carried a sunset of 2026-12-22. Download the county GIS file by hand "
            "and pass its path, or update PLACES_CSV_URL."
        )
    if key == "hrsa":
        return f"HRSA H80 workbook failed. The file is linked from {HRSA_XLSX_URL}."
    return f"CMS star-ratings zip failed. The index is {CMS_PAGE_URL}."


def _download(client: httpx.Client, url: str, dest: Path, hint: str) -> None:
    try:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"{hint} URL: {url}. {type(exc).__name__}.") from exc
    if dest.stat().st_size < 1000:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"{hint} The download was empty. URL: {url}.")
