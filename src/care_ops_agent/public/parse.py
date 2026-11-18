"""Turn the three public files into rows. No rates are computed here."""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Any

CMS_CODES = {
    "C01": "breast_cancer_screening",
    "C12": "diabetes_blood_sugar_controlled",
    "C14": "bp_control",
}
PLACES_IDS = {
    "DIABETES": "diabetes_prevalence",
    "BPMED": "bp_medication",
    "MAMMOUSE": "mammography",
}
_CI = re.compile(r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)")
_CODE = re.compile(r"^(C\d+|D\d+)\s*:")


def parse_count(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text.lower() in {"", "-", "--", "nan", "none", "*"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_percent_cell(value: Any) -> tuple[float | None, str | None]:
    """Return (percent 0–100, status). A non-numeric cell is a status, not a zero."""
    if value is None:
        return None, None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none"}:
        return None, None
    number = text[:-1].strip() if text.endswith("%") else text
    number = number.replace(",", "")
    try:
        parsed = float(number)
    except ValueError:
        return None, text
    if parsed < 0 or parsed > 100:
        return None, text
    return parsed, None


def parse_ci(value: Any) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    match = _CI.search(str(value))
    if match is None:
        return None, None
    return float(match.group(1)), float(match.group(2))


def bhcmis_id(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if not text.isdigit():
        return ""
    return text.zfill(6)


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "-"}:
        return ""
    return text


def _whole_pair(numerator: float | None, denominator: float | None) -> tuple[float, float] | None:
    if numerator is None or denominator is None or denominator <= 0 or numerator < 0:
        return None
    if abs(numerator - round(numerator)) < 1e-6:
        numerator = float(round(numerator))
    if abs(denominator - round(denominator)) < 1e-6:
        denominator = float(round(denominator))
    if numerator > denominator:
        return None
    return numerator, denominator


def parse_places_csv(source: Path | io.TextIOBase) -> list[dict[str, Any]]:
    handle, close = _open_text(source)
    try:
        reader = csv.DictReader(handle)
        missing = [f"{code}_CrudePrev" for code in PLACES_IDS if f"{code}_CrudePrev" not in (reader.fieldnames or [])]
        identity = ["StateAbbr", "StateDesc", "CountyName", "CountyFIPS", "TotalPopulation", "TotalPop18plus"]
        missing += [name for name in identity if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CDC PLACES file is missing columns: " + ", ".join(missing))
        rows: list[dict[str, Any]] = []
        for record in reader:
            fips = str(record["CountyFIPS"]).strip().zfill(5)
            if not fips.isdigit() or len(fips) != 5:
                continue
            population = parse_count(record["TotalPopulation"])
            adults = parse_count(record["TotalPop18plus"])
            for code, measure_id in PLACES_IDS.items():
                percent, _status = parse_percent_cell(record.get(f"{code}_CrudePrev"))
                low, high = parse_ci(record.get(f"{code}_Crude95CI"))
                rows.append({
                    "county_fips": fips,
                    "state_abbr": _text(record["StateAbbr"]),
                    "state_name": _text(record["StateDesc"]),
                    "county_name": _text(record["CountyName"]),
                    "total_population": None if population is None else int(population),
                    "pop_18plus": None if adults is None else int(adults),
                    "measure_id": measure_id,
                    "crude_percent": percent,
                    "published_ci_low": low,
                    "published_ci_high": high,
                })
        if not rows:
            raise ValueError("CDC PLACES file produced no county rows.")
        return rows
    finally:
        if close:
            handle.close()


def parse_cms_measure_file(source: Path | io.TextIOBase) -> list[dict[str, Any]]:
    handle, close = _open_text(source, encoding="cp1252")
    try:
        grid = list(csv.reader(handle))
    finally:
        if close:
            handle.close()
    if len(grid) < 5:
        raise ValueError("CMS measure file does not have the report-card header.")
    labels = grid[2]
    periods = grid[3]
    columns: dict[int, tuple[str, str, str]] = {}
    for index, label in enumerate(labels):
        match = _CODE.match(label.strip())
        if match is None:
            continue
        code = match.group(1)
        if code not in CMS_CODES:
            continue
        name = label.split(":", 1)[1].strip()
        period = periods[index].strip() if index < len(periods) else ""
        columns[index] = (code, name, period)
    missing = [code for code in CMS_CODES if code not in {item[0] for item in columns.values()}]
    if missing:
        raise ValueError("CMS measure file is missing " + ", ".join(missing))
    rows: list[dict[str, Any]] = []
    for record in grid[4:]:
        if not record or not record[0].strip():
            continue
        contract_id = record[0].strip()
        organization_type = record[1].strip() if len(record) > 1 else ""
        contract_name = record[2].strip() if len(record) > 2 else ""
        marketing = record[3].strip() if len(record) > 3 else ""
        parent = record[4].strip() if len(record) > 4 else ""
        for index, (code, name, period) in columns.items():
            cell = record[index] if index < len(record) else ""
            percent, status = parse_percent_cell(cell)
            rows.append({
                "contract_id": contract_id,
                "organization_type": organization_type,
                "contract_name": marketing or contract_name,
                "parent_organization": parent,
                "measure_code": code,
                "measure_id": CMS_CODES[code],
                "measure_name": name,
                "measurement_period": period,
                "published_percent": percent,
                "status": status,
            })
    if not rows:
        raise ValueError("CMS measure file produced no contract rows.")
    return rows


def parse_cms_zip(path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        name = next(
            (
                item for item in archive.namelist()
                if "measure data" in item.lower() and item.lower().endswith(".csv")
            ),
            None,
        )
        if name is None:
            raise ValueError(f"{path.name} has no Measure Data CSV.")
        text = io.StringIO(archive.read(name).decode("cp1252"))
    return parse_cms_measure_file(text)


def parse_hrsa_xlsx(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    info = pd.read_excel(path, sheet_name="HealthCenterInfo", dtype=str)
    centers: dict[str, dict[str, Any]] = {}
    for record in info.to_dict("records"):
        identifier = bhcmis_id(record.get("BHCMISID"))
        if not identifier:
            continue
        year = parse_count(record.get("ReportingYear"))
        centers[identifier] = {
            "health_center_name": _text(record.get("HealthCenterName")) or identifier,
            "city": _text(record.get("HealthCenterCity")),
            "state": _text(record.get("HealthCenterState")),
            "reporting_year": None if year is None else int(year),
        }
    if not centers:
        raise ValueError("HRSA HealthCenterInfo has no health-center ids.")

    rows: list[dict[str, Any]] = []
    rows.extend(_mammography(path, centers))
    rows.extend(_table7_totals(
        path, centers, sheet="Table7_1",
        numerator_code="T7_Li_C2c", denominator_code="T7_Li_C2a",
        measure_id="bp_control",
    ))
    rows.extend(_table7_totals(
        path, centers, sheet="Table7_2",
        numerator_code="T7_Li_C3f", denominator_code="T7_Li_C3a",
        measure_id="diabetes_poor_control",
    ))
    if not rows:
        raise ValueError("HRSA workbook produced no measure rows.")
    return rows


def _mammography(path: Path, centers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_excel(path, sheet_name="Table6BClinicalmeasures", dtype=str)
    rows = []
    for record in frame.to_dict("records"):
        identifier = bhcmis_id(record.get("BHCMISID"))
        center = centers.get(identifier)
        if center is None:
            continue
        pair = _whole_pair(
            parse_count(record.get("#ofPatientswithMammogram")),
            parse_count(record.get("TotalFemalePatients52-74Yearsage")),
        )
        if pair is None:
            continue
        numerator, denominator = pair
        published, _status = parse_percent_cell(record.get("%ofPatientswithMammogram"))
        rows.append({
            **center,
            "bhcmis_id": identifier,
            "measure_id": "breast_cancer_screening",
            "numerator": numerator,
            "denominator": denominator,
            "published_percent": published,
        })
    return rows


def _table7_totals(
    path: Path,
    centers: dict[str, dict[str, Any]],
    *,
    sheet: str,
    numerator_code: str,
    denominator_code: str,
    measure_id: str,
) -> list[dict[str, Any]]:
    import pandas as pd

    header = pd.read_excel(path, sheet_name=sheet, header=None, nrows=1)
    codes = ["" if value is None or str(value) == "nan" else str(value).strip() for value in header.iloc[0].tolist()]
    try:
        denominator_at = codes.index(denominator_code)
        numerator_at = codes.index(numerator_code)
    except ValueError as exc:
        raise ValueError(f"{sheet} is missing {numerator_code} or {denominator_code}") from exc
    selected = [0, numerator_at, denominator_at]
    frame = pd.read_excel(
        path, sheet_name=sheet, header=None, skiprows=2, dtype=str,
        usecols=selected,
    )
    # Excel column order, not the order of `selected`.
    names = {0: "identifier", numerator_at: "numerator", denominator_at: "denominator"}
    frame.columns = [names[index] for index in sorted(selected)]
    rows = []
    for identifier_raw, numerator_raw, denominator_raw in frame[["identifier", "numerator", "denominator"]].itertuples(index=False):
        identifier = bhcmis_id(identifier_raw)
        center = centers.get(identifier)
        if center is None:
            continue
        pair = _whole_pair(parse_count(numerator_raw), parse_count(denominator_raw))
        if pair is None:
            continue
        numerator, denominator = pair
        rows.append({
            **center,
            "bhcmis_id": identifier,
            "measure_id": measure_id,
            "numerator": numerator,
            "denominator": denominator,
            "published_percent": None,
        })
    return rows


def _open_text(source: Path | io.TextIOBase, encoding: str = "utf-8-sig") -> tuple[io.TextIOBase, bool]:
    if isinstance(source, Path):
        return source.open(newline="", encoding=encoding), True
    return source, False

