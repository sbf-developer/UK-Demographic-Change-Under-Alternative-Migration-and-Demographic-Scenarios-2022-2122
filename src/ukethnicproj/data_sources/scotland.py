"""Scotland SPARQL endpoint adapter (stub for Phase 6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ukethnicproj.config import RAW_DIR
from ukethnicproj.data_sources.base import CachedHTTPClient


class ScotlandCensusClient:
    """Client for https://statistics.gov.scot/sparql.json."""

    BASE_URL = "https://statistics.gov.scot"

    def __init__(self, cache_dir: Path | None = None) -> None:
        cache = cache_dir or RAW_DIR / "scotland" / "cache"
        self.http = CachedHTTPClient(self.BASE_URL, cache)

    def sparql_query(self, query: str) -> dict[str, Any]:
        return self.http.get_json("/sparql.json", params={"query": query})

    def close(self) -> None:
        self.http.close()
