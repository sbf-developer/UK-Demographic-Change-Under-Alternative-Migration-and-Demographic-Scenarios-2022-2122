"""Northern Ireland NISRA census adapter (stub for Phase 6)."""

from __future__ import annotations

from pathlib import Path

import httpx

from ukethnicproj.config import RAW_DIR


class NISRACensusClient:
    """Download adapter for NISRA Census 2021 tables."""

    DT_0035_URL = (
        "https://www.nisra.gov.uk/system/files/statistics/census-2021-main-statistics-for-northern-ireland-phase-1/DT-0035.xlsx"
    )

    def __init__(self) -> None:
        self.raw_dir = RAW_DIR / "nisra"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch_dt0035(self) -> Path:
        """Attempt download of DT-0035: Ethnic Group by Age by Sex."""
        out_path = self.raw_dir / "DT-0035.xlsx"
        if out_path.exists():
            return out_path

        with httpx.Client(follow_redirects=True, timeout=120.0) as client:
            response = client.get(self.DT_0035_URL)
            response.raise_for_status()
            out_path.write_bytes(response.content)
        return out_path
