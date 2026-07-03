"""Version-controlled ethnic category harmonisation schema."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera as pa
from pandera.typing import Series

from ukethnicproj import BROAD_ETHNIC_GROUPS
from ukethnicproj.config import PROJECT_ROOT

HARMONISATION_PATH = (
    PROJECT_ROOT / "configs" / "harmonisation" / "ethnic_category_mapping.csv"
)


class HarmonisationMappingSchema(pa.DataFrameModel):
    """Schema for ethnic category mapping table."""

    source_country: Series[str]
    source_census_year: Series[int]
    original_category: Series[str]
    original_category_code: Series[str] = pa.Field(nullable=True)
    nomis_api_code: Series[str] = pa.Field(nullable=True)
    harmonised_broad: Series[str] = pa.Field(isin=BROAD_ETHNIC_GROUPS)
    harmonised_detailed: Series[str]
    mapping_rationale: Series[str]
    comparability_quality: Series[str] = pa.Field(
        isin=["high", "moderate", "low", "uncertain"]
    )
    uncertainty_flag: Series[bool]
    notes: Series[str] = pa.Field(nullable=True)


# England/Wales Census 2021 categories mapped to harmonised broad groups
# Source: ONS Census 2021 RM032 variable definitions
# https://www.ons.gov.uk/datasets/RM032/editions/2021/versions/1
ENGLAND_WALES_2021_MAPPINGS: list[dict[str, object]] = [
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "White: English, Welsh, Scottish, Northern Irish or British",
        "original_category_code": "10001",
        "harmonised_broad": "white",
        "harmonised_detailed": "white_british",
        "mapping_rationale": "Direct mapping to harmonised White category",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": "Wording specific to England and Wales Census 2021",
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "White: Irish",
        "original_category_code": "10002",
        "harmonised_broad": "white",
        "harmonised_detailed": "white_irish",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "White: Gypsy or Irish Traveller",
        "original_category_code": "10003",
        "harmonised_broad": "white",
        "harmonised_detailed": "white_gypsy_traveller",
        "mapping_rationale": "ONS broad group classification",
        "comparability_quality": "moderate",
        "uncertainty_flag": True,
        "notes": "Category not available in all UK nations",
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "White: Roma",
        "original_category_code": "10004",
        "harmonised_broad": "white",
        "harmonised_detailed": "white_roma",
        "mapping_rationale": "New category in 2021; limited historical comparability",
        "comparability_quality": "low",
        "uncertainty_flag": True,
        "notes": "First appearance in Census 2021",
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "White: Other White",
        "original_category_code": "10005",
        "harmonised_broad": "white",
        "harmonised_detailed": "white_other",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Mixed or Multiple ethnic groups: White and Black Caribbean",
        "original_category_code": "20001",
        "harmonised_broad": "mixed",
        "harmonised_detailed": "mixed_white_black_caribbean",
        "mapping_rationale": "Direct mapping to Mixed broad group",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Mixed or Multiple ethnic groups: White and Black African",
        "original_category_code": "20002",
        "harmonised_broad": "mixed",
        "harmonised_detailed": "mixed_white_black_african",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Mixed or Multiple ethnic groups: White and Asian",
        "original_category_code": "20003",
        "harmonised_broad": "mixed",
        "harmonised_detailed": "mixed_white_asian",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Mixed or Multiple ethnic groups: Other Mixed or Multiple ethnic groups",
        "original_category_code": "20004",
        "harmonised_broad": "mixed",
        "harmonised_detailed": "mixed_other",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Asian, Asian British or Asian Welsh: Indian",
        "original_category_code": "30001",
        "harmonised_broad": "asian",
        "harmonised_detailed": "asian_indian",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Asian, Asian British or Asian Welsh: Pakistani",
        "original_category_code": "30002",
        "harmonised_broad": "asian",
        "harmonised_detailed": "asian_pakistani",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Asian, Asian British or Asian Welsh: Bangladeshi",
        "original_category_code": "30003",
        "harmonised_broad": "asian",
        "harmonised_detailed": "asian_bangladeshi",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Asian, Asian British or Asian Welsh: Chinese",
        "original_category_code": "30004",
        "harmonised_broad": "asian",
        "harmonised_detailed": "asian_chinese",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Asian, Asian British or Asian Welsh: Other Asian",
        "original_category_code": "30005",
        "harmonised_broad": "asian",
        "harmonised_detailed": "asian_other",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Black, Black British, Black Welsh, Caribbean or African: African",
        "original_category_code": "40001",
        "harmonised_broad": "black",
        "harmonised_detailed": "black_african",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Black, Black British, Black Welsh, Caribbean or African: Caribbean",
        "original_category_code": "40002",
        "harmonised_broad": "black",
        "harmonised_detailed": "black_caribbean",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Black, Black British, Black Welsh, Caribbean or African: Other Black",
        "original_category_code": "40003",
        "harmonised_broad": "black",
        "harmonised_detailed": "black_other",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Other ethnic group: Arab",
        "original_category_code": "50001",
        "harmonised_broad": "other",
        "harmonised_detailed": "other_arab",
        "mapping_rationale": "ONS broad group classification",
        "comparability_quality": "moderate",
        "uncertainty_flag": True,
        "notes": "Arab category introduced in 2011",
    },
    {
        "source_country": "england_wales",
        "source_census_year": 2021,
        "original_category": "Other ethnic group: Any other ethnic group",
        "original_category_code": "50002",
        "harmonised_broad": "other",
        "harmonised_detailed": "other_other",
        "mapping_rationale": "Direct mapping",
        "comparability_quality": "high",
        "uncertainty_flag": False,
        "notes": None,
    },
]


# Nomis/ONS RM032 API enumeration codes (1--19), distinct from Census output codes
NOMIS_API_CODES_BY_DETAILED: dict[str, str] = {
    "white_british": "13",
    "white_irish": "14",
    "white_gypsy_traveller": "15",
    "white_roma": "16",
    "white_other": "17",
    "mixed_white_black_caribbean": "11",
    "mixed_white_black_african": "10",
    "mixed_white_asian": "9",
    "mixed_other": "12",
    "asian_indian": "3",
    "asian_pakistani": "4",
    "asian_bangladeshi": "1",
    "asian_chinese": "2",
    "asian_other": "5",
    "black_african": "6",
    "black_caribbean": "7",
    "black_other": "8",
    "other_arab": "18",
    "other_other": "19",
}


def build_default_mapping_table() -> pd.DataFrame:
    """Create the default harmonisation mapping table."""
    df = pd.DataFrame(ENGLAND_WALES_2021_MAPPINGS)
    df["original_category_code"] = df["original_category_code"].astype(str)
    df["nomis_api_code"] = df["harmonised_detailed"].map(NOMIS_API_CODES_BY_DETAILED)
    HarmonisationMappingSchema.validate(df)
    return df


def save_mapping_table(path: Path | None = None) -> Path:
    """Write mapping table to CSV."""
    target = path or HARMONISATION_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    df = build_default_mapping_table()
    df.to_csv(target, index=False)
    return target


def load_mapping_table(path: Path | None = None) -> pd.DataFrame:
    """Load and validate harmonisation mapping table."""
    target = path or HARMONISATION_PATH
    if not target.exists():
        save_mapping_table(target)
    df = pd.read_csv(
        target,
        dtype={"original_category_code": str, "nomis_api_code": str},
    )
    HarmonisationMappingSchema.validate(df)
    return df


def map_to_broad(
    df: pd.DataFrame,
    category_col: str = "original_category",
    mapping: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Map source ethnic categories to harmonised broad groups."""
    mapping = mapping or load_mapping_table()
    lookup = mapping.set_index(category_col)["harmonised_broad"].to_dict()
    result = df.copy()
    result["harmonised_broad"] = result[category_col].map(lookup)
    unmapped = result["harmonised_broad"].isna().sum()
    if unmapped > 0:
        missing = result.loc[result["harmonised_broad"].isna(), category_col].unique()
        raise ValueError(f"Unmapped ethnic categories: {missing}")
    return result
