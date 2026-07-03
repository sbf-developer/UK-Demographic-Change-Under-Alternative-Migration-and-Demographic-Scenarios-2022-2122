"""Migration flow parameters from ONS NPP assumptions and Census age profiles."""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from ukethnicproj import AGE_MAX, AGE_MIN, BROAD_ETHNIC_GROUPS, GENERATIONS, SEXES
from ukethnicproj.config import PROJECT_ROOT
from ukethnicproj.base_population.builder import fetch_mye_age_sex_profile
from ukethnicproj.calibration.nativity import immigration_ethnic_composition, load_rm011_by_age
from ukethnicproj.projection.state import PopulationState

_NPP_CONFIG = PROJECT_ROOT / "configs" / "ons_npp_2022_scenarios.yml"

# RM011 age band id -> inclusive range
RM011_AGE_BANDS: dict[str, tuple[int, int]] = {
    "1": (0, 15),
    "2": (16, 24),
    "3": (25, 34),
    "4": (35, 49),
    "5": (50, 64),
    "6": (65, 100),
}


def _load_npp_config() -> dict:
    with _NPP_CONFIG.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def compute_ew_share(nations: tuple[str, ...], year: int = 2022) -> float:
    """England & Wales share of UK population from MYE."""
    ew = sum(fetch_mye_age_sex_profile(n, year=year)["count"].sum() for n in nations)
    uk = fetch_mye_age_sex_profile("england", year=year)  # noqa: just to init
    from ukethnicproj.data_sources.base import CachedHTTPClient
    from ukethnicproj.config import RAW_DIR

    http = CachedHTTPClient("https://www.nomisweb.co.uk/api/v01", RAW_DIR / "nomis" / "cache")
    try:
        r = http.get_json(
            "/dataset/NM_2002_1.data.json",
            params={"geography": "2092957697", "date": str(year), "measures": "20100", "gender": "1,2"},
        )
        import re

        single = [o for o in r["obs"] if re.match(r"^Age \d+$", o["c_age"]["description"])]
        open90 = [o for o in r["obs"] if o["c_age"]["description"] == "Aged 90+"]
        uk_total = sum(o["obs_value"]["value"] for o in single)
        uk_total += sum(o["obs_value"]["value"] for o in open90)
    finally:
        http.close()
    return ew / uk_total if uk_total > 0 else float(_load_npp_config()["ew_share_default"])


def migration_volumes(
    migration_variant: str,
    nations: tuple[str, ...],
    year: int = 2022,
) -> tuple[float, float]:
    """Return annual immigration and emigration for model nations (EW-scaled ONS NPP)."""
    cfg = _load_npp_config()
    variant = cfg["migration_variants"][migration_variant]
    ew_share = compute_ew_share(nations, year=year)
    return (
        float(variant["uk_immigration"]) * ew_share,
        float(variant["uk_emigration"]) * ew_share,
    )


def _nonuk_age_profile(nations: tuple[str, ...]) -> np.ndarray:
    """Immigration age weights from Census non-UK-born age structure (RM011 + MYE disaggregation)."""
    n_ages = AGE_MAX - AGE_MIN + 1
    weights = np.zeros(n_ages)

    for nation in nations:
        rm011 = load_rm011_by_age(nation)
        nonuk = rm011[~rm011["uk_born"]]
        mye = fetch_mye_age_sex_profile(nation).groupby("age")["count"].sum()
        for _, row in nonuk.iterrows():
            band_id = str(row["resident_age_6a_id"])
            lo, hi = RM011_AGE_BANDS.get(band_id, (0, 100))
            band_ages = list(range(lo, min(hi, AGE_MAX) + 1))
            band_pop = sum(float(mye.get(a, 0)) for a in band_ages)
            if band_pop <= 0:
                uniform = row["count"] / max(len(band_ages), 1)
                for a in band_ages:
                    if a < n_ages:
                        weights[a] += uniform
            else:
                for a in band_ages:
                    if a < n_ages:
                        weights[a] += row["count"] * float(mye.get(a, 0)) / band_pop

    if weights.sum() > 0:
        weights /= weights.sum()
    else:
        weights[20:45] = 1.0
        weights /= weights.sum()
    return weights


def _emigration_age_profile(state: PopulationState) -> np.ndarray:
    """Emigration age weights: population-weighted with elevated outflow at working ages."""
    n_ages = state.n_ages
    pop_by_age = state.array.sum(axis=(0, 1, 2, 3))
    weights = pop_by_age.copy()
    ages = np.arange(AGE_MIN, AGE_MAX + 1)
    working = (ages >= 20) & (ages <= 45)
    weights[working] *= 1.5
    if weights.sum() > 0:
        weights /= weights.sum()
    else:
        weights[:] = 1.0 / n_ages
    return weights


def build_migration_arrays(
    state: PopulationState,
    nations: tuple[str, ...],
    *,
    migration_variant: str = "principal",
    ethnic_composition: dict[str, float] | None = None,
    year: int = 2022,
) -> tuple[np.ndarray, np.ndarray]:
    """Build immigration and emigration arrays from ONS NPP volumes and Census age profiles."""
    annual_imm, annual_emig = migration_volumes(migration_variant, nations, year=year)
    n_nations = len(nations)
    n_ethnic = len(BROAD_ETHNIC_GROUPS)
    n_gen = len(GENERATIONS)
    n_sex = len(SEXES)
    n_ages = state.n_ages

    immigration = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))
    emigration = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))

    if annual_imm <= 0 and annual_emig <= 0:
        return immigration, emigration

    comp = ethnic_composition or immigration_ethnic_composition(nations)
    comp_total = sum(comp.values())
    imm_age_w = _nonuk_age_profile(nations)
    emig_age_w = _emigration_age_profile(state)
    g_imm = GENERATIONS.index("foreign_born_adult")

    for n in range(n_nations):
        nation_imm = annual_imm / n_nations
        nation_emig = annual_emig / n_nations

        for e_idx, e_name in enumerate(BROAD_ETHNIC_GROUPS):
            e_share = comp.get(e_name, 0) / comp_total
            for s_idx in range(n_sex):
                for a_idx in range(n_ages):
                    immigration[n, e_idx, g_imm, s_idx, a_idx] = (
                        nation_imm * e_share * imm_age_w[a_idx] / n_sex
                    )

    for n_idx in range(n_nations):
        nation_emig = annual_emig / n_nations
        pop_age = state.array[n_idx].sum(axis=(0, 1, 2))
        for e_idx in range(n_ethnic):
            for g_idx in range(n_gen):
                for s_idx in range(n_sex):
                    for a_idx in range(n_ages):
                        cell = state.array[n_idx, e_idx, g_idx, s_idx, a_idx]
                        if pop_age[a_idx] > 0:
                            emigration[n_idx, e_idx, g_idx, s_idx, a_idx] = (
                                nation_emig * emig_age_w[a_idx] * (cell / pop_age[a_idx])
                            )

    return immigration, emigration
