"""Tests for Census 2021 base population construction."""

from __future__ import annotations

from pathlib import Path

import pytest

from ukethnicproj.base_population.builder import (
    REFERENCE_TOTALS,
    build_base_population,
    disaggregate_to_single_year,
    fetch_mye_age_sex_profile,
    load_rm032_harmonised,
    scale_to_mye_midyear,
)

ONS_ENGLAND = Path("data/raw/ons/rm032/rm032_E92000001.json")
ONS_WALES = Path("data/raw/ons/rm032/rm032_W92000004.json")


@pytest.mark.skipif(not ONS_ENGLAND.exists(), reason="ONS RM032 not fetched")
class TestBasePopulationBuilder:
    def test_rm032_harmonised_england_total(self) -> None:
        df = load_rm032_harmonised("england")
        total = df["count"].sum()
        assert abs(total - REFERENCE_TOTALS["england"]) < 500_000

    def test_mye_england_total(self) -> None:
        profile = fetch_mye_age_sex_profile("england", year=2022)
        total = profile["count"].sum()
        assert 56_000_000 < total < 57_500_000

    def test_disaggregation_preserves_band_totals(self) -> None:
        rm032 = load_rm032_harmonised("england")
        mye = fetch_mye_age_sex_profile("england", year=2022)
        disagg = disaggregate_to_single_year(rm032, mye, "england")

        census_by_band = rm032.groupby(["sex", "age_band_id"])["count"].sum()
        disagg_with_band = disagg.copy()
        disagg_with_band["age_band_id"] = disagg_with_band["age"].apply(
            lambda a: "1"
            if a <= 24
            else "2"
            if a <= 34
            else "3"
            if a <= 49
            else "4"
            if a <= 64
            else "5"
        )
        rebuilt = disagg_with_band.groupby(["sex", "age_band_id"])["count"].sum()
        for key, census_val in census_by_band.items():
            assert abs(rebuilt[key] - census_val) < 1.0

    def test_scale_to_mye_matches_official_total(self) -> None:
        rm032 = load_rm032_harmonised("england")
        mye = fetch_mye_age_sex_profile("england", year=2022)
        disagg = disaggregate_to_single_year(rm032, mye, "england")
        scaled = scale_to_mye_midyear(disagg, mye, "england")
        mye_total = mye["count"].sum()
        assert abs(scaled["count"].sum() - mye_total) < 10.0

    @pytest.mark.skipif(not ONS_WALES.exists(), reason="Wales RM032 not fetched")
    def test_build_england_wales_combined(self) -> None:
        state, report = build_base_population(
            nations=("england", "wales"),
            save=False,
        )
        assert state.total_population > 59_000_000
        assert state.total_population < 61_000_000
        assert report.ethnic_shares["england"]["white"] > 0.75
        assert state.validate() == []
