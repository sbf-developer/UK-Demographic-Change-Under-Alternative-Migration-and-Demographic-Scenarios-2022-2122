"""Build harmonised mid-2022 base population from Census 2021 RM032 + MYE."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from ukethnicproj import (
    AGE_MAX,
    AGE_MIN,
    BROAD_ETHNIC_GROUPS,
    GENERATIONS,
    NATION_CODES,
    NATIONS,
    SEXES,
)
from ukethnicproj.config import PROCESSED_DIR, PROJECT_ROOT, RAW_DIR
from ukethnicproj.data_sources.nomis import NomisClient
from ukethnicproj.data_sources.ons import ONSClient
from ukethnicproj.harmonisation.schema import load_mapping_table
from ukethnicproj.projection.state import PopulationState

_MYE_CODES_PATH = PROJECT_ROOT / "configs" / "nomis_mye_codes.yml"
_BASE_POPULATION_PATH = PROCESSED_DIR / "base_population_mid2022.npz"
_BASE_POPULATION_META_PATH = PROCESSED_DIR / "base_population_mid2022.json"

# Census 2021 reference totals for validation (usual residents)
REFERENCE_TOTALS = {
    "england": 56_489_800,
    "wales": 3_107_500,
}


@dataclass(frozen=True)
class BasePopulationBuildReport:
    """Summary statistics from a base population build."""

    nations: tuple[str, ...]
    census_totals: dict[str, float]
    mye_totals: dict[str, float]
    scaled_totals: dict[str, float]
    ethnic_shares: dict[str, dict[str, float]]
    output_path: Path
    metadata_path: Path
    generation_note: str


def _load_mye_codes() -> dict[str, Any]:
    with _MYE_CODES_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _rm032_path(nation: str) -> Path:
    area_code = NATION_CODES[nation]
    return RAW_DIR / "ons" / "rm032" / f"rm032_{area_code}.json"


def _mye_path(nation: str, year: int = 2022) -> Path:
    return RAW_DIR / "nomis" / "mye" / f"mye_{nation}_{year}.json"


def _ethnic_api_to_broad() -> dict[str, str]:
    mapping = load_mapping_table()
    return mapping.set_index("nomis_api_code")["harmonised_broad"].astype(str).to_dict()


def load_rm032_harmonised(nation: str) -> pd.DataFrame:
    """Load ONS RM032 for a nation and map to harmonised broad ethnic groups."""
    path = _rm032_path(nation)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing Census RM032 for {nation} at {path}. Run: python -m ukethnicproj data fetch"
        )

    client = ONSClient()
    df = client.parse_rm032_to_dataframe(path)
    df = df[df["ethnic_group_tb_20b_id"] != "-8"].copy()
    df["ethnic_id"] = df["ethnic_group_tb_20b_id"].astype(str)
    df["harmonised_broad"] = df["ethnic_id"].map(_ethnic_api_to_broad())
    if df["harmonised_broad"].isna().any():
        missing = df.loc[df["harmonised_broad"].isna(), "ethnic_group_tb_20b_label"].unique()
        raise ValueError(f"Unmapped RM032 ethnic categories for {nation}: {missing}")

    df["nation"] = nation
    df["sex"] = df["sex_id"].map({"1": "female", "2": "male"})
    df["age_band_id"] = df["resident_age_5c_id"].astype(str)
    return df


def fetch_mye_age_sex_profile(
    nation: str,
    *,
    year: int = 2022,
    client: NomisClient | None = None,
) -> pd.DataFrame:
    """Fetch and parse ONS mid-year population estimates by single year of age."""
    codes = _load_mye_codes()
    geo_code = codes["NATION_GEO_CODES"][nation]
    out_path = _mye_path(nation, year)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    own_client = client is None
    nomis = client or NomisClient()
    try:
        if not out_path.exists():
            params = {
                codes["DIM_GEOGRAPHY"]: geo_code,
                codes["DIM_DATE"]: str(year),
                codes["DIM_MEASURES"]: codes["MEASURES_CODE"],
                codes["DIM_GENDER"]: f"{codes['GENDER_MALE']},{codes['GENDER_FEMALE']}",
            }
            data = nomis.http.get_json(
                f"/dataset/{codes['DATASET_ID']}.data.json",
                params=params,
            )
            if data.get("error"):
                raise RuntimeError(f"Nomis MYE fetch failed for {nation}: {data['error']}")
            out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            nomis.manifest.register(
                filepath=out_path,
                source_organisation="Nomis (Office for National Statistics)",
                dataset_title="Mid-year population estimates by single year of age",
                dataset_identifier=codes["DATASET_ID"],
                source_location=f"{nomis.BASE_URL}/dataset/{codes['DATASET_ID']}.data.json",
                reference_period=f"Mid-year {year}",
                geographical_coverage=nation,
                variable_definitions="Single year of age, sex; NM_2002_1",
                licence="Open Government Licence v3.0",
                processing_script="ukethnicproj.base_population.builder.fetch_mye_age_sex_profile",
                known_limitations=(
                    "Ages 90+ provided as open band; distributed to ages 90–100 for projection."
                ),
            )

        payload = json.loads(out_path.read_text(encoding="utf-8"))
        records: list[dict[str, Any]] = []
        for obs in payload.get("obs", []):
            desc = obs["c_age"]["description"]
            if not re.match(r"^Age \d+$", desc):
                continue
            age = int(desc.replace("Age ", ""))
            gender_val = str(obs["gender"]["value"])
            sex = "male" if gender_val == codes["GENDER_MALE"] else "female"
            records.append(
                {
                    "nation": nation,
                    "age": age,
                    "sex": sex,
                    "count": float(obs["obs_value"]["value"]),
                }
            )

        # Open age band 90+ → distribute to ages 90–100
        for gender_val, sex in [
            (codes["GENDER_MALE"], "male"),
            (codes["GENDER_FEMALE"], "female"),
        ]:
            open_band = [
                o
                for o in payload.get("obs", [])
                if o["c_age"]["description"] == "Aged 90+"
                and str(o["gender"]["value"]) == gender_val
            ]
            if open_band:
                open_total = float(open_band[0]["obs_value"]["value"])
                per_age = open_total / (AGE_MAX - 90 + 1)
                for age in range(90, AGE_MAX + 1):
                    records.append(
                        {"nation": nation, "age": age, "sex": sex, "count": per_age}
                    )

        profile = pd.DataFrame(records)
        if profile.empty:
            raise ValueError(f"No single-year MYE observations parsed for {nation}")
        return profile
    finally:
        if own_client:
            nomis.close()


def _ages_in_band(band_id: str) -> list[int]:
    codes = _load_mye_codes()
    low, high = codes["RM032_AGE_BANDS"][band_id]
    return list(range(max(AGE_MIN, low), min(AGE_MAX, high) + 1))


def disaggregate_to_single_year(
    rm032: pd.DataFrame,
    mye_profile: pd.DataFrame,
    nation: str,
) -> pd.DataFrame:
    """
    Disaggregate RM032 ethnic × sex × age-band counts to single-year ages.

    Within each age band, counts are allocated proportionally to the official
    MYE mid-2022 age×sex structure for that nation.
    """
    mye = mye_profile[mye_profile["nation"] == nation].copy()
    mye_weights: dict[tuple[str, str], dict[int, float]] = {}
    for (sex, band_id), _ in rm032.groupby(["sex", "age_band_id"]).groups.items():
        ages = _ages_in_band(band_id)
        subset = mye[(mye["sex"] == sex) & (mye["age"].isin(ages))]
        weights = {int(row.age): float(row.count) for row in subset.itertuples()}
        band_total = sum(weights.values())
        if band_total <= 0:
            uniform = 1.0 / len(ages)
            weights = {a: uniform for a in ages}
        mye_weights[(sex, band_id)] = weights

    rows: list[dict[str, Any]] = []
    grouped = rm032.groupby(
        ["harmonised_broad", "sex", "age_band_id"], as_index=False
    )["count"].sum()

    for row in grouped.itertuples():
        weights = mye_weights[(row.sex, row.age_band_id)]
        band_total_w = sum(weights.values())
        for age, weight in weights.items():
            rows.append(
                {
                    "nation": nation,
                    "harmonised_broad": row.harmonised_broad,
                    "sex": row.sex,
                    "age": age,
                    "count": row.count * weight / band_total_w,
                }
            )

    return pd.DataFrame(rows)


def scale_to_mye_midyear(
    disaggregated: pd.DataFrame,
    mye_profile: pd.DataFrame,
    nation: str,
) -> pd.DataFrame:
    """Scale disaggregated census counts so nation total matches MYE mid-2022."""
    census_total = disaggregated["count"].sum()
    mye_total = mye_profile[mye_profile["nation"] == nation]["count"].sum()
    if census_total <= 0:
        raise ValueError(f"Census total is zero for {nation}")
    factor = mye_total / census_total
    result = disaggregated.copy()
    result["count"] *= factor
    return result


def dataframe_to_population_state(
    df: pd.DataFrame,
    *,
    year: int = 2022,
    nations: tuple[str, ...] = ("england", "wales"),
) -> PopulationState:
    """
    Convert tidy base population table to PopulationState array.

    Generation is not observed in RM032; all persons are assigned to
    ukborn_two_ukborn_parents pending country-of-birth linkage (Phase 2b).
    """
    state = PopulationState.zeros(year=year, nations=nations)
    g_idx = GENERATIONS.index("ukborn_two_ukborn_parents")

    for row in df.itertuples():
        n_idx = nations.index(row.nation)
        e_idx = BROAD_ETHNIC_GROUPS.index(row.harmonised_broad)
        s_idx = SEXES.index(row.sex)
        a_idx = int(row.age) - AGE_MIN
        state.array[n_idx, e_idx, g_idx, s_idx, a_idx] += row.count

    return state


def build_base_population(
    *,
    nations: tuple[str, ...] = ("england", "wales"),
    base_year: int = 2022,
    save: bool = True,
) -> tuple[PopulationState, BasePopulationBuildReport]:
    """
    Build harmonised mid-2022 base population from Census 2021 RM032.

    Uses ONS Census 2021 ethnic × sex × age-band counts and disaggregates
    to single-year-of-age using Nomis mid-year population estimates (MYE).
    """
    frames: list[pd.DataFrame] = []
    census_totals: dict[str, float] = {}
    mye_totals: dict[str, float] = {}
    scaled_totals: dict[str, float] = {}

    with NomisClient() as nomis:
        for nation in nations:
            rm032 = load_rm032_harmonised(nation)
            census_totals[nation] = float(rm032["count"].sum())
            mye_profile = fetch_mye_age_sex_profile(nation, year=base_year, client=nomis)
            mye_totals[nation] = float(mye_profile["count"].sum())

            disagg = disaggregate_to_single_year(rm032, mye_profile, nation)
            scaled = scale_to_mye_midyear(disagg, mye_profile, nation)
            scaled_totals[nation] = float(scaled["count"].sum())
            frames.append(scaled)

    combined = pd.concat(frames, ignore_index=True)
    state = dataframe_to_population_state(combined, year=base_year, nations=nations)

    from ukethnicproj.calibration.nativity import apply_generation_from_census

    state = apply_generation_from_census(state, nations)

    ethnic_shares: dict[str, dict[str, float]] = {}
    for n_idx, nation in enumerate(nations):
        ethnic_shares[nation] = state.ethnic_shares(n_idx)

    report = BasePopulationBuildReport(
        nations=nations,
        census_totals=census_totals,
        mye_totals=mye_totals,
        scaled_totals=scaled_totals,
        ethnic_shares=ethnic_shares,
        output_path=_BASE_POPULATION_PATH,
        metadata_path=_BASE_POPULATION_META_PATH,
        generation_note=(
            "Generation assigned from Census 2021 RM010 (ethnic x country of birth) "
            "and RM011 (country of birth x age). UK-born with foreign-born parents "
            "not separately identified until parental COB linkage (Phase 2b)."
        ),
    )

    if save:
        save_base_population(state, report)

    return state, report


def save_base_population(
    state: PopulationState,
    report: BasePopulationBuildReport,
) -> None:
    """Persist base population array and build metadata."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        report.output_path,
        array=state.array,
        year=state.year,
        nations=np.array(state.nations),
    )
    meta = {
        "base_year": state.year,
        "nations": list(state.nations),
        "total_population": state.total_population,
        "census_totals": report.census_totals,
        "mye_totals": report.mye_totals,
        "scaled_totals": report.scaled_totals,
        "ethnic_shares": report.ethnic_shares,
        "reference_totals": REFERENCE_TOTALS,
        "generation_note": report.generation_note,
        "data_sources": [
            "ONS Census 2021 RM032 (ethnic group × sex × age band)",
            "Nomis NM_2002_1 mid-year population estimates 2022 (age disaggregation)",
        ],
    }
    report.metadata_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_base_population(
    path: Path | None = None,
    *,
    nations: tuple[str, ...] | None = None,
) -> PopulationState:
    """Load previously built base population from disk."""
    target = path or _BASE_POPULATION_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"No base population at {target}. Run: python -m ukethnicproj build-base-population"
        )

    data = np.load(target, allow_pickle=True)
    stored_nations = tuple(str(n) for n in data["nations"])
    use_nations = nations or stored_nations

    state = PopulationState.zeros(year=int(data["year"]), nations=use_nations)
    full_array = data["array"]

    for n_idx, nation in enumerate(use_nations):
        if nation not in stored_nations:
            raise ValueError(f"Nation {nation} not in stored base population {stored_nations}")
        src_idx = stored_nations.index(nation)
        state.array[n_idx] = full_array[src_idx]

    return state


def base_population_available() -> bool:
    return _BASE_POPULATION_PATH.exists()
