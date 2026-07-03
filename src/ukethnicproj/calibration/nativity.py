"""Nativity and generation assignment from Census country-of-birth tables."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd

from ukethnicproj import GENERATIONS, NATION_CODES
from ukethnicproj.projection.state import PopulationState
from ukethnicproj.config import RAW_DIR

# RM010 ethnic_group_tb_8a -> harmonised broad
RM010_ETHNIC_TO_BROAD: dict[str, str] = {
    "Asian, Asian British or Asian Welsh": "asian",
    "Black, Black British, Black Welsh, Caribbean or African": "black",
    "Mixed or Multiple ethnic groups": "mixed",
    "White: English, Welsh, Scottish, Northern Irish or British": "white",
    "White: Irish": "white",
    "White: Gypsy or Irish Traveller, Roma or Other White": "white",
    "Other ethnic group": "other",
}

UK_BORN_COB_ID = "1"


def _parse_ons_table(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dims = payload["dimensions"]
    options = [d["options"] for d in dims]
    names = [d["dimension_name"] for d in dims]
    records: list[dict[str, object]] = []
    for combo, value in zip(itertools.product(*options), payload["observations"]):
        if value is None:
            continue
        rec: dict[str, object] = {"count": float(value)}
        for name, opt in zip(names, combo):
            rec[f"{name}_id"] = opt["id"]
            rec[f"{name}_label"] = opt["label"]
        records.append(rec)
    return pd.DataFrame(records)


def load_rm010_harmonised(nation: str) -> pd.DataFrame:
    area = NATION_CODES[nation]
    path = RAW_DIR / "ons" / "country_of_birth" / f"rm010_{area}.json"
    if not path.exists():
        from ukethnicproj.calibration.fetch import fetch_country_of_birth_tables

        fetch_country_of_birth_tables(nation=nation)
    df = _parse_ons_table(path)
    df = df[df["ethnic_group_tb_8a_id"] != "-8"].copy()
    df["harmonised_broad"] = df["ethnic_group_tb_8a_label"].map(RM010_ETHNIC_TO_BROAD)
    df["uk_born"] = df["country_of_birth_12a_id"] == UK_BORN_COB_ID
    df["nation"] = nation
    return df


def load_rm011_by_age(nation: str) -> pd.DataFrame:
    area = NATION_CODES[nation]
    path = RAW_DIR / "ons" / "country_of_birth" / f"rm011_{area}.json"
    if not path.exists():
        from ukethnicproj.calibration.fetch import fetch_country_of_birth_tables

        fetch_country_of_birth_tables(nation=nation)
    df = _parse_ons_table(path)
    df = df[df["country_of_birth_12a_id"] != "-8"].copy()
    df["uk_born"] = df["country_of_birth_12a_id"] == UK_BORN_COB_ID
    df["nation"] = nation
    return df


def generation_shares_by_ethnic(nation: str) -> dict[str, dict[str, float]]:
    """
    Derive generation shares within each broad ethnic group from RM010 + RM011.

    Uses country of birth as observed in Census 2021. Parental COB is not available;
    UK-born with foreign-born parents cannot be separated (assigned to ukborn_two_ukborn_parents).
    """
    rm010 = load_rm010_harmonised(nation)
    grouped = rm010.groupby(["harmonised_broad", "uk_born"])["count"].sum().unstack(fill_value=0)
    shares: dict[str, dict[str, float]] = {}
    for ethnic in grouped.index:
        total = grouped.loc[ethnic].sum()
        if total <= 0:
            shares[ethnic] = {GENERATIONS[-1]: 1.0}
            continue
        uk = float(grouped.loc[ethnic].get(True, grouped.loc[ethnic].get("True", 0)))
        nonuk = total - uk
        shares[ethnic] = {
            GENERATIONS.index("foreign_born_adult"): nonuk / total,
            GENERATIONS.index("ukborn_two_ukborn_parents"): uk / total,
        }
    return shares


def apply_generation_from_census(
    state: PopulationState,
    nations: tuple[str, ...],
) -> PopulationState:
    """
    Reassign generation dimension using Census country-of-birth (RM010, RM011).

    Non-UK-born share by ethnic group from RM010; children vs adults split using
    RM011 age structure applied uniformly across ethnic groups.
    """
    from ukethnicproj import BROAD_ETHNIC_GROUPS, GENERATIONS, SEXES

    result = state.copy()
    source = state.array.copy()
    result.array.fill(0.0)

    g_uk = GENERATIONS.index("ukborn_two_ukborn_parents")
    g_fb_adult = GENERATIONS.index("foreign_born_adult")
    g_fb_child = GENERATIONS.index("foreign_born_child")

    for n_idx, nation in enumerate(nations):
        rm010 = load_rm010_harmonised(nation)
        rm011 = load_rm011_by_age(nation)
        nonuk_total = rm011[~rm011["uk_born"]]["count"].sum()
        nonuk_child = rm011[
            (~rm011["uk_born"]) & (rm011["resident_age_6a_id"] == "1")
        ]["count"].sum()
        child_share = nonuk_child / nonuk_total if nonuk_total > 0 else 0.0

        ethnic_nonuk_share: dict[str, float] = {}
        for ethnic in BROAD_ETHNIC_GROUPS:
            sub = rm010[rm010["harmonised_broad"] == ethnic]
            total = sub["count"].sum()
            nonuk = sub[~sub["uk_born"]]["count"].sum()
            ethnic_nonuk_share[ethnic] = nonuk / total if total > 0 else 0.0

        for e_idx, ethnic in enumerate(BROAD_ETHNIC_GROUPS):
            nonuk_frac = ethnic_nonuk_share.get(ethnic, 0.0)
            for s_idx in range(len(SEXES)):
                for a_idx in range(state.n_ages):
                    age = a_idx + state.age_min
                    total_cell = float(source[n_idx, e_idx, :, s_idx, a_idx].sum())
                    if total_cell <= 0:
                        continue
                    if nonuk_frac <= 0:
                        result.array[n_idx, e_idx, g_uk, s_idx, a_idx] = total_cell
                        continue
                    uk_part = total_cell * (1.0 - nonuk_frac)
                    nonuk_part = total_cell * nonuk_frac
                    if age <= 15:
                        result.array[n_idx, e_idx, g_fb_child, s_idx, a_idx] = (
                            nonuk_part * child_share
                        )
                        result.array[n_idx, e_idx, g_fb_adult, s_idx, a_idx] = (
                            nonuk_part * (1.0 - child_share)
                        )
                    else:
                        result.array[n_idx, e_idx, g_fb_adult, s_idx, a_idx] = nonuk_part
                    result.array[n_idx, e_idx, g_uk, s_idx, a_idx] = uk_part

    return result


def immigration_ethnic_composition(nations: tuple[str, ...]) -> dict[str, float]:
    """Non-UK-born ethnic composition from Census RM010 (empirical migrant stock composition)."""
    totals: dict[str, float] = {g: 0.0 for g in RM010_ETHNIC_TO_BROAD.values()}
    for nation in nations:
        rm010 = load_rm010_harmonised(nation)
        nonuk = rm010[~rm010["uk_born"]].groupby("harmonised_broad")["count"].sum()
        for ethnic, count in nonuk.items():
            totals[ethnic] += float(count)
    total = sum(totals.values())
    if total <= 0:
        n = len(totals)
        return {k: 1.0 / n for k in totals}
    return {k: v / total for k, v in totals.items()}
