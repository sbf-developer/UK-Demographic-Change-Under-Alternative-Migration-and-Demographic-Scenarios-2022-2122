"""Shared configuration and path utilities."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_DIR = DATA_DIR / "metadata"
MANIFESTS_DIR = DATA_DIR / "manifests"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
ASSUMPTIONS_DIR = PROJECT_ROOT / "assumptions"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

for directory in (
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    METADATA_DIR,
    MANIFESTS_DIR,
    OUTPUTS_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)
