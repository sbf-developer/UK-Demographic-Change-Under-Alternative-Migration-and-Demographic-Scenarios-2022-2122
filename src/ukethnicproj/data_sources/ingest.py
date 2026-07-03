"""Data ingestion orchestration."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ukethnicproj.config import MANIFESTS_DIR, RAW_DIR
from ukethnicproj.data_sources.manifest import ManifestRegistry
from ukethnicproj.data_sources.nomis import NomisClient
from ukethnicproj.data_sources.ons import ONSClient

console = Console()


def discover_datasets() -> dict[str, object]:
    """Discover available datasets from ONS and Nomis APIs."""
    results: dict[str, object] = {}

    with ONSClient() as ons:
        results["ons_census_datasets"] = ons.discover_census_datasets()
        try:
            results["ons_rm032_metadata"] = ons.get_rm032_metadata()
        except Exception as exc:
            results["ons_rm032_metadata_error"] = str(exc)

    with NomisClient() as nomis:
        try:
            results["nomis_c2021rm032"] = nomis.discover_c2021rm032_dimensions()
        except Exception as exc:
            results["nomis_c2021rm032_error"] = str(exc)

    output_path = MANIFESTS_DIR / "discovery_report.json"
    import json

    output_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]Discovery report written to {output_path}[/green]")
    return results


def fetch_all_data() -> dict[str, Path | str]:
    """Fetch all Phase 1 datasets."""
    fetched: dict[str, Path | str] = {}

    with ONSClient() as ons:
        for area_code, label in [
            ("E92000001", "england"),
            ("W92000004", "wales"),
        ]:
            try:
                path = ons.fetch_rm032_json(area_code=area_code)
                fetched[f"ons_rm032_{label}"] = path
                console.print(f"[green]Fetched ONS RM032 for {label}[/green]")
            except Exception as exc:
                fetched[f"ons_rm032_{label}"] = f"FAILED: {exc}"
                console.print(f"[yellow]ONS RM032 {label} failed: {exc}[/yellow]")

    with NomisClient() as nomis:
        try:
            path = nomis.fetch_c2021rm032(geography="0")
            fetched["nomis_c2021rm032_all_regions"] = path
            console.print("[green]Fetched Nomis C2021RM032 for all TYPE480 regions[/green]")
        except Exception as exc:
            fetched["nomis_c2021rm032_all_regions"] = f"FAILED: {exc}"
            console.print(f"[yellow]Nomis C2021RM032 failed: {exc}[/yellow]")

    try:
        from ukethnicproj.calibration.fetch import fetch_all_calibration_data

        cal = fetch_all_calibration_data(force=False)
        fetched.update({f"calibration_{k}": v for k, v in cal.items()})
        console.print("[green]Fetched calibration datasets (life tables, births, COB)[/green]")
    except Exception as exc:
        fetched["calibration"] = f"FAILED: {exc}"
        console.print(f"[yellow]Calibration fetch failed: {exc}[/yellow]")

    # Consolidate manifests
    for source in ("ons", "nomis"):
        manifest_path = RAW_DIR / source / "manifest.jsonl"
        if manifest_path.exists():
            registry = ManifestRegistry(manifest_path)
            registry.write_summary(MANIFESTS_DIR / f"{source}_manifest_summary.json")

    return fetched


def validate_data() -> bool:
    """Validate downloaded data integrity via checksums."""
    all_valid = True
    for source in ("ons", "nomis"):
        manifest_path = RAW_DIR / source / "manifest.jsonl"
        if not manifest_path.exists():
            console.print(f"[yellow]No manifest for {source}[/yellow]")
            continue
        registry = ManifestRegistry(manifest_path)
        for entry in registry.load_all():
            filepath = RAW_DIR / source / entry.raw_filename
            # Search subdirectories
            matches = list(RAW_DIR.rglob(entry.raw_filename))
            if not matches:
                console.print(f"[red]Missing file: {entry.raw_filename}[/red]")
                all_valid = False
                continue
            actual = registry.compute_sha256(matches[0])
            if actual != entry.sha256_checksum:
                console.print(f"[red]Checksum mismatch: {entry.raw_filename}[/red]")
                all_valid = False
            else:
                console.print(f"[green]Valid: {entry.raw_filename}[/green]")
    return all_valid
