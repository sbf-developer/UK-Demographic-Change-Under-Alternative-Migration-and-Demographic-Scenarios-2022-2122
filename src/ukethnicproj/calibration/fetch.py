"""Fetch and cache official calibration datasets."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pandas as pd
import yaml

from ukethnicproj.config import PROJECT_ROOT, RAW_DIR
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.data_sources.ons import ONSClient

_NPP_CONFIG = PROJECT_ROOT / "configs" / "ons_npp_2022_scenarios.yml"
_LIFE_TABLES_DIR = RAW_DIR / "ons" / "life_tables"
_BIRTHS_DIR = RAW_DIR / "nomis" / "births"
_COB_DIR = RAW_DIR / "ons" / "country_of_birth"


def _load_npp_config() -> dict:
    with _NPP_CONFIG.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def fetch_life_tables(force: bool = False) -> Path:
    """Download ONS National Life Tables xlsx (2020-2022 period)."""
    cfg = _load_npp_config()["mortality"]
    target = _LIFE_TABLES_DIR / "life_tables_uk.xlsx"
    if target.exists() and not force:
        return target

    _LIFE_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    page = (
        "https://www.ons.gov.uk/peoplepopulationandcommunity/"
        "birthsdeathsandmarriages/lifeexpectancies/datasets/"
        "nationallifetablesunitedkingdomreferencetables"
    )
    resp = httpx.get(page, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    uris = re.findall(r"file\?uri=([^\"'&]+)", resp.text, re.I)
    uri = cfg.get("xlsx_uri")
    if uri not in uris and uris:
        uri = uris[0]
    url = f"https://www.ons.gov.uk/file?uri={uri}"
    data = httpx.get(url, follow_redirects=True, timeout=60)
    data.raise_for_status()
    target.write_bytes(data.content)
    return target


def parse_life_table_qx(sheet: str | None = None) -> pd.DataFrame:
    """Parse ONS period life table qx by age and sex."""
    cfg = _load_npp_config()["mortality"]
    path = fetch_life_tables()
    sheet_name = sheet or cfg["sheet"]
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)

    # Males: cols 0-5 (age, mx, qx, lx, dx, ex); Females: cols 7-12
    records: list[dict[str, object]] = []
    for offset, sex in [(0, "male"), (7, "female")]:
        header_row = raw.index[raw.iloc[:, offset] == "age"]
        if len(header_row) == 0:
            continue
        start = header_row[0] + 1
        for i in range(start, raw.shape[0]):
            age_val = raw.iloc[i, offset]
            if pd.isna(age_val) or not str(age_val).strip().isdigit():
                break
            qx = float(raw.iloc[i, offset + 2])
            records.append({"age": int(age_val), "sex": sex, "qx": qx, "px": 1.0 - qx})

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError(f"No qx values parsed from life table sheet {sheet_name}")
    return df


def fetch_births_by_mother_age(year: int = 2022, force: bool = False) -> Path:
    """Fetch Nomis NM_203_1 live births by mother's age band (England & Wales)."""
    cfg = _load_npp_config()["births"]
    target = _BIRTHS_DIR / f"births_mother_age_{year}.json"
    if target.exists() and not force:
        return target

    _BIRTHS_DIR.mkdir(parents=True, exist_ok=True)
    http = CachedHTTPClient("https://www.nomisweb.co.uk/api/v01", RAW_DIR / "nomis" / "cache")
    try:
        data = http.get_json(
            f"/dataset/{cfg['dataset']}.data.json",
            params={
                "geography": cfg["geography_code"],
                "date": str(year),
                "measures": "20100",
                "gender": "0",
                "multiple": "0",
                "registration_type": "0",
                "cob_mother": "0",
            },
        )
        if data.get("error"):
            raise RuntimeError(data["error"])
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    finally:
        http.close()
    return target


def parse_births_by_mother_age(path: Path | None = None, year: int = 2022) -> pd.DataFrame:
    """Parse mother age band birth counts."""
    target = path or fetch_births_by_mother_age(year=year)
    payload = json.loads(target.read_text(encoding="utf-8"))
    skip = {"Total", "Age of mother unknown or not stated"}
    records: list[dict[str, object]] = []
    for obs in payload.get("obs", []):
        label = obs["age_of_mother"]["description"]
        if label in skip:
            continue
        records.append(
            {
                "age_band": label,
                "births": float(obs["obs_value"]["value"]),
            }
        )
    return pd.DataFrame(records)


def fetch_country_of_birth_tables(nation: str = "england", force: bool = False) -> dict[str, Path]:
    """Fetch ONS RM010 and RM011 for country-of-birth linkage."""
    from ukethnicproj import NATION_CODES

    area = NATION_CODES[nation]
    _COB_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    client = ONSClient()
    try:
        for dataset in ("RM010", "RM011"):
            target = _COB_DIR / f"{dataset.lower()}_{area}.json"
            if target.exists() and not force:
                paths[dataset] = target
                continue
            data = client.http.get_json(
                f"/datasets/{dataset}/editions/2021/versions/1/json",
                params={"area-type": f"ctry,{area}"},
            )
            target.write_text(json.dumps(data, indent=2), encoding="utf-8")
            paths[dataset] = target
    finally:
        client.close()
    return paths


def fetch_all_calibration_data(force: bool = False) -> dict[str, Path]:
    """Fetch all datasets required for empirical parameter calibration."""
    fetched: dict[str, Path] = {}
    fetched["life_tables"] = fetch_life_tables(force=force)
    fetched["births"] = fetch_births_by_mother_age(force=force)
    for nation in ("england", "wales"):
        cob = fetch_country_of_birth_tables(nation=nation, force=force)
        fetched[f"rm010_{nation}"] = cob["RM010"]
        fetched[f"rm011_{nation}"] = cob["RM011"]
    return fetched
