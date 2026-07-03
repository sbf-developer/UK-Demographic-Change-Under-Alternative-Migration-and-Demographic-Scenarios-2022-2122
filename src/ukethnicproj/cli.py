"""Command-line interface for ukethnicproj."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ukethnicproj import REPORT_YEARS, WATERMARK, __version__
from ukethnicproj.config import OUTPUTS_DIR, REPORTS_DIR, SCENARIOS_DIR
from ukethnicproj.data_sources.ingest import discover_datasets, fetch_all_data, validate_data
from ukethnicproj.harmonisation.schema import save_mapping_table
from ukethnicproj.projection.engine import CohortComponentEngine
from ukethnicproj.projection.scenarios import (
    create_placeholder_initial_state,
    create_placeholder_parameters,
    load_scenario,
)
from ukethnicproj.visualisation.plots import plot_age_pyramid, plot_ethnic_shares_trajectory

console = Console()


@click.group()
@click.version_option(__version__)
def main() -> None:
    """UK ethnic demographic projection system."""


@main.group()
def data() -> None:
    """Data discovery, fetch and validation."""


@data.command("discover")
def data_discover() -> None:
    """Discover available datasets from official APIs."""
    discover_datasets()


@data.command("fetch")
def data_fetch() -> None:
    """Fetch datasets from ONS and Nomis APIs."""
    fetch_all_data()


@data.command("validate")
def data_validate() -> None:
    """Validate downloaded data integrity."""
    valid = validate_data()
    if not valid:
        raise SystemExit(1)


@main.command("build-base-population")
def build_base_population() -> None:
    """Build harmonised mid-2022 base population (Phase 2)."""
    save_mapping_table()
    console.print("[yellow]Phase 1: harmonisation schema created.[/yellow]")
    console.print(
        "[yellow]Full mid-2022 base population requires Census data processing (Phase 2).[/yellow]"
    )


@main.command("calibrate")
def calibrate() -> None:
    """Calibrate model parameters from historical data (Phase 4)."""
    console.print("[yellow]Calibration not yet implemented (Phase 4).[/yellow]")


@main.command("simulate")
@click.option("--scenario", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--end-year", default=2050, type=int, help="Projection end year")
def simulate(scenario: Path, end_year: int) -> None:
    """Run projection for a specified scenario."""
    config = load_scenario(scenario)
    console.print(f"[bold]Scenario:[/bold] {config.name}")
    console.print(f"[red italic]{config.watermark}[/red italic]")

    initial = create_placeholder_initial_state(config)
    params = create_placeholder_parameters(config)
    engine = CohortComponentEngine(params)

    result = engine.project(
        initial,
        end_year=min(end_year, config.end_year),
        scenario_name=config.name,
        watermark=config.watermark,
    )

    # Save trajectory summary
    output_dir = OUTPUTS_DIR / config.name
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_lines = [
        f"# Projection summary: {config.name}",
        f"",
        f"**{config.watermark}**",
        f"",
        f"Model version: A-deterministic-v0.1",
        f"Base year: {config.base_year}",
        f"End year: {min(end_year, config.end_year)}",
        f"Placeholder parameters: {config.placeholder}",
        f"",
        f"> Under the specified assumptions, the model projects conditional trajectories.",
        f"> This is not a prediction of future population composition.",
        f"",
        "## Population totals at report years",
        "",
        "| Year | Total population |",
        "|------|-----------------|",
    ]
    for state in result.trajectory:
        if state.year in REPORT_YEARS or state.year == result.trajectory[-1].year:
            summary_lines.append(f"| {state.year} | {state.total_population:,.0f} |")

    summary_lines.extend(["", "## Ethnic shares (England only; nation index 0)", ""])
    for state in result.trajectory:
        if state.year in REPORT_YEARS:
            shares = state.ethnic_shares(nation_idx=0)
            share_str = ", ".join(f"{k}: {v:.1%}" for k, v in shares.items())
            summary_lines.append(f"- **{state.year}**: {share_str}")

    summary_path = output_dir / "projection_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    console.print(f"[green]Summary written to {summary_path}[/green]")

    # Plots
    plot_ethnic_shares_trajectory(
        result,
        nation_idx=0,
        output_path=output_dir / "ethnic_shares_trajectory.png",
    )
    plot_age_pyramid(
        result.trajectory[-1],
        nation_idx=0,
        output_path=output_dir / "age_pyramid_end.png",
        scenario_name=config.name,
    )
    console.print(f"[green]Figures saved to {output_dir}[/green]")


@main.command("validate-model")
def validate_model() -> None:
    """Run model validation checks (Phase 4)."""
    console.print("[yellow]Historical validation not yet implemented (Phase 4).[/yellow]")


@main.command("report")
def report() -> None:
    """Generate data availability and methodological reports."""
    save_mapping_table()
    console.print(f"[green]Reports available in {REPORTS_DIR}[/green]")
    console.print(f"[green]Run 'make pdf' to compile LaTeX report[/green]")


if __name__ == "__main__":
    main()
