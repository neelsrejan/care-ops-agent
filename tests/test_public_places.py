import io
from pathlib import Path

import pytest

from care_ops_agent.config import find_repo_root
from care_ops_agent.public import download
from care_ops_agent.public.parse import parse_places_csv


def test_pinned_places_archive_keeps_autauga():
    rows = parse_places_csv(find_repo_root() / "data" / "published" / "places_county_2025.csv")
    autauga = next(row for row in rows if row["county_fips"] == "01001" and row["measure_id"] == "diabetes_prevalence")
    assert autauga["crude_percent"] == 13.3
    assert autauga["published_ci_low"] == 11.4
    assert sum(1 for row in rows if row["measure_id"] == "diabetes_prevalence") >= 3000


def test_soda_lowercase_headers_parse():
    text = io.StringIO(
        "stateabbr,statedesc,countyname,countyfips,totalpopulation,totalpop18plus,"
        "diabetes_crudeprev,diabetes_crude95ci,bpmed_crudeprev,bpmed_crude95ci,"
        "mammouse_crudeprev,mammouse_crude95ci\n"
        "AL,Alabama,Autauga,01001,60342,46253,13.3,\"(11.4, 15.3)\",78.2,\"(75.3, 80.9)\",80.9,\"(74.0, 86.6)\"\n"
    )
    rows = parse_places_csv(text)
    autauga = next(row for row in rows if row["measure_id"] == "diabetes_prevalence")
    assert autauga["crude_percent"] == 13.3
    assert autauga["state_abbr"] == "AL"


def test_places_download_uses_soda_after_the_bulk_export_fails(tmp_path, monkeypatch):
    calls = []

    def fake_download(_client, url, dest, hint):
        calls.append(url)
        if "rows.csv" in url:
            raise RuntimeError("bulk export retired")
        dest.write_text("soda")

    monkeypatch.setattr(download, "_download", fake_download)
    dest = tmp_path / "places.csv"
    assert download.download_places(client=None, dest=dest) == "soda"
    assert dest.read_text() == "soda"
    assert len(calls) == 2


def test_places_download_uses_the_pin_when_both_exports_fail(tmp_path, monkeypatch):
    def boom(_client, url, dest, hint):
        raise RuntimeError(f"down {url}")

    monkeypatch.setattr(download, "_download", boom)
    pin = tmp_path / "pin.csv"
    pin.write_text("county,fips\n" + "Autauga,01001\n" * 80)
    monkeypatch.setattr(download, "pinned_places_path", lambda: pin)
    dest = tmp_path / "out.csv"
    assert download.download_places(client=None, dest=dest) == "pinned"
    assert "Autauga" in dest.read_text()
