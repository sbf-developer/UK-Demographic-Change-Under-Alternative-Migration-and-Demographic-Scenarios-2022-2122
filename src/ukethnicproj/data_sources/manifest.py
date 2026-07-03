"""Data manifest and provenance tracking."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DataManifestEntry(BaseModel):
    """Provenance record for a downloaded or processed dataset."""

    source_organisation: str
    dataset_title: str
    dataset_identifier: str
    source_location: str
    retrieval_timestamp: str
    reference_period: str
    geographical_coverage: str
    variable_definitions: str
    licence: str
    sha256_checksum: str
    raw_filename: str
    processing_script: str
    known_limitations: str
    status: str = "retrieved"
    notes: str = ""


class ManifestRegistry:
    """Append-only manifest registry stored as JSON lines."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def compute_sha256(self, filepath: Path) -> str:
        digest = hashlib.sha256()
        with filepath.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def register(
        self,
        *,
        filepath: Path,
        source_organisation: str,
        dataset_title: str,
        dataset_identifier: str,
        source_location: str,
        reference_period: str,
        geographical_coverage: str,
        variable_definitions: str,
        licence: str,
        processing_script: str,
        known_limitations: str,
        status: str = "retrieved",
        notes: str = "",
    ) -> DataManifestEntry:
        entry = DataManifestEntry(
            source_organisation=source_organisation,
            dataset_title=dataset_title,
            dataset_identifier=dataset_identifier,
            source_location=source_location,
            retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
            reference_period=reference_period,
            geographical_coverage=geographical_coverage,
            variable_definitions=variable_definitions,
            licence=licence,
            sha256_checksum=self.compute_sha256(filepath),
            raw_filename=str(filepath.name),
            processing_script=processing_script,
            known_limitations=known_limitations,
            status=status,
            notes=notes,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(entry.model_dump_json() + "\n")
        return entry

    def load_all(self) -> list[DataManifestEntry]:
        if not self.path.exists():
            return []
        entries: list[DataManifestEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(DataManifestEntry.model_validate_json(line))
        return entries

    def to_dataframe(self) -> Any:
        import pandas as pd

        records = [entry.model_dump() for entry in self.load_all()]
        return pd.DataFrame(records)

    def write_summary(self, output_path: Path) -> None:
        entries = self.load_all()
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(entries),
            "entries": [entry.model_dump() for entry in entries],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
