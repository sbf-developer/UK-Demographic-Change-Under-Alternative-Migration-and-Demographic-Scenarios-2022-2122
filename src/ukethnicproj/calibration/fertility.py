"""Fertility parameters from ONS live births and Census 2021."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import yaml

from ukethnicproj import AGE_MAX, AGE_MIN, BROAD_ETHNIC_GROUPS, GENERATIONS
from ukethnicproj.config import PROJECT_ROOT
from ukethnicproj.base_population.builder import fetch_mye_age_sex_profile, load_rm032_harmonised
from ukethnicproj.calibration.fetch import parse_births_by_mother_age

_NPP_CONFIG = PROJECT_ROOT / "configs" / "ons_npp_2022_scenarios.yml"

# Nomis mother age band -> inclusive age range for disaggregation
MOTHER_AGE_BANDS: dict[str, tuple[int, int]] = {
    "Mother aged under 20": (15, 19),
    "Mother aged 20-24": (20, 24),
    "Mother aged 25-29": (25, 29),
    "Mother aged 30-34": (30, 34),
    "Mother aged 35-39": (35, 39),
    "Mother aged 40-44": (40, 44),
    "Mother aged 45 and over": (45, 49),
}


def _load_npp_config() -> dict:
    with _NPP_CONFIG.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _female_population_by_age(nations: tuple[str, ...], year: int = 2022) -> pd.DataFrame:
    frames = [fetch_mye_age_sex_profile(n, year=year) for n in nations]
    mye = pd.concat(frames, ignore_index=True)
    return mye[mye["sex"] == "female"].groupby("age", as_index=False)["count"].sum()


def compute_national_asfr(nations: tuple[str, ...], year: int = 2022) -> np.ndarray:
    """Compute national age-specific fertility rates from Nomis births and MYE."""
    births = parse_births_by_mother_age(year=year)
    female_pop = _female_population_by_age(nations, year=year).set_index("age")["count"]

    n_ages = AGE_MAX - AGE_MIN + 1
    asfr = np.zeros(n_ages)
    ages = np.arange(AGE_MIN, AGE_MAX + 1)

    for _, row in births.iterrows():
        band = row["age_band"]
        if band not in MOTHER_AGE_BANDS:
            continue
        lo, hi = MOTHER_AGE_BANDS[band]
        band_ages = [a for a in range(lo, hi + 1) if a <= 49]
        pop_band = sum(float(female_pop.get(a, 0)) for a in band_ages)
        if pop_band <= 0:
            continue
        births_per_age = row["births"] / len(band_ages)
        for a in band_ages:
            idx = a - AGE_MIN
            pop_a = float(female_pop.get(a, 0))
            if pop_a > 0:
                asfr[idx] = births_per_age / pop_a

    return asfr


def compute_ethnic_fertility_scalars(nations: tuple[str, ...]) -> dict[str, float]:
    """
    Estimate ethnic-group fertility scalars relative to national average.

    Uses Census 2021 RM032: children aged 0-4 proxy / women 15-49 by broad ethnic group.
    """
    child_proxy: dict[str, float] = {g: 0.0 for g in BROAD_ETHNIC_GROUPS}
    women: dict[str, float] = {g: 0.0 for g in BROAD_ETHNIC_GROUPS}

    for nation in nations:
        rm032 = load_rm032_harmonised(nation)
        females = rm032[rm032["sex"] == "female"]
        for ethnic in BROAD_ETHNIC_GROUPS:
            sub = females[females["harmonised_broad"] == ethnic]
            under24 = sub[sub["age_band_id"] == "1"]["count"].sum()
            child_proxy[ethnic] += under24 * (5.0 / 25.0)
            for band in ("1", "2", "3"):
                women[ethnic] += sub[sub["age_band_id"] == band]["count"].sum()

    tfr_proxy = {
        g: child_proxy[g] / women[g] if women[g] > 0 else 0.0 for g in BROAD_ETHNIC_GROUPS
    }
    positive = [v for v in tfr_proxy.values() if v > 0]
    national = sum(positive) / len(positive) if positive else 1.0
    if national <= 0:
        return {g: 1.0 for g in BROAD_ETHNIC_GROUPS}
    return {g: (tfr_proxy[g] / national if tfr_proxy[g] > 0 else 1.0) for g in BROAD_ETHNIC_GROUPS}


def build_fertility_array(
    nations: tuple[str, ...],
    *,
    fertility_variant: str = "principal",
    year: int = 2022,
) -> np.ndarray:
    """Build ethnic-specific ASFR array calibrated to ONS births and Census fertility differentials."""
    cfg = _load_npp_config()
    variant = cfg["fertility_variants"][fertility_variant]
    target_tfr = float(variant["long_term_tfr"])

    national_asfr = compute_national_asfr(nations, year=year)
    current_tfr = float(national_asfr[15:50].sum())
    if current_tfr > 0:
        national_asfr = national_asfr * (target_tfr / current_tfr)

    ethnic_scalars = compute_ethnic_fertility_scalars(nations)
    n_nations = len(nations)
    n_ethnic = len(BROAD_ETHNIC_GROUPS)
    n_gen = len(GENERATIONS)
    n_ages = AGE_MAX - AGE_MIN + 1

    fertility = np.zeros((n_nations, n_ethnic, n_gen, n_ages))
    for n in range(n_nations):
        for e_idx, group in enumerate(BROAD_ETHNIC_GROUPS):
            scale = ethnic_scalars.get(group, 1.0)
            for g in range(n_gen):
                fertility[n, e_idx, g, :] = national_asfr * scale

    return fertility
