"""Tests for data source clients."""

from __future__ import annotations

import pytest

from ukethnicproj.data_sources.nomis import NomisClient
from ukethnicproj.data_sources.ons import ONSClient

pytestmark = pytest.mark.integration


class TestONSClient:
    def test_list_datasets(self) -> None:
        with ONSClient() as client:
            result = client.list_datasets(limit=5)
            assert "items" in result
            assert len(result["items"]) > 0

    def test_rm032_metadata(self) -> None:
        with ONSClient() as client:
            metadata = client.get_rm032_metadata()
            assert metadata.get("id") == "RM032" or "RM032" in str(metadata)


class TestNomisClient:
    def test_dataset_definition(self) -> None:
        with NomisClient() as client:
            definition = client.dataset_definition()
            assert definition is not None

    def test_discover_dimensions(self) -> None:
        with NomisClient() as client:
            discovery = client.discover_c2021rm032_dimensions()
            assert discovery["dataset_code"] == "C2021RM032"
            assert discovery["dataset_id"] == "NM_2132"
            assert "C2021_ETH_20" in discovery.get("dimensions", [])
