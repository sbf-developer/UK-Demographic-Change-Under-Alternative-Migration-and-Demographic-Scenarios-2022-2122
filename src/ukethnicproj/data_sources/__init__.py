"""Data source adapters."""

from ukethnicproj.data_sources.ingest import discover_datasets, fetch_all_data, validate_data
from ukethnicproj.data_sources.nomis import NomisClient
from ukethnicproj.data_sources.ons import ONSClient

__all__ = [
    "ONSClient",
    "NomisClient",
    "discover_datasets",
    "fetch_all_data",
    "validate_data",
]
