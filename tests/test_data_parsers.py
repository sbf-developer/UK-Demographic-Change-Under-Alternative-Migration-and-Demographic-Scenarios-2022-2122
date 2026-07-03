"""Tests for census data parsers and empirical cross-validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from ukethnicproj.data_sources.nomis import NomisClient
from ukethnicproj.data_sources.ons import ONSClient

ONS_ENGLAND_PATH = Path("data/raw/ons/rm032/rm032_E92000001.json")
NOMIS_REGIONS_PATH = Path("data/raw/nomis/c2021rm032/c2021rm032_TYPE480_0.json")

# ONS Census 2021 usual residents, England: 56,489,800
# Source: Census 2021 RM032 country total
ENGLAND_CENSUS_2021 = 56_489_800
ENGLAND_TOTAL_TOLERANCE = 500_000  # broad age bands and rounding


@pytest.mark.skipif(not ONS_ENGLAND_PATH.exists(), reason="ONS RM032 not fetched")
class TestONSParser:
    def test_parse_rm032_structure(self) -> None:
        client = ONSClient()
        df = client.parse_rm032_to_dataframe(ONS_ENGLAND_PATH)
        assert len(df) == 200
        assert "count" in df.columns
        assert df["count"].min() >= 0

    def test_england_total_near_census(self) -> None:
        client = ONSClient()
        df = client.parse_rm032_to_dataframe(ONS_ENGLAND_PATH)
        total = df["count"].sum()
        assert abs(total - ENGLAND_CENSUS_2021) < ENGLAND_TOTAL_TOLERANCE


@pytest.mark.skipif(not NOMIS_REGIONS_PATH.exists(), reason="Nomis C2021RM032 not fetched")
class TestNomisParser:
    def test_parse_nomis_regions(self) -> None:
        client = NomisClient()
        df = client.parse_c2021rm032_to_dataframe(NOMIS_REGIONS_PATH)
        assert len(df) >= 10_000
        assert df["geography_name"].nunique() == 10
        assert df["count"].min() >= 0

    def test_nomis_ethnic_categories(self) -> None:
        client = NomisClient()
        df = client.parse_c2021rm032_to_dataframe(NOMIS_REGIONS_PATH)
        assert df["ethnic_value"].nunique() == 19
