"""Command-line interface for ukethnicproj."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ukethnicproj import REPORT_YEARS, WATERMARK, __version__
from ukethnicproj.config import OUTPUTS_DIR, REPORTS_DIR, SCENARIOS_DIR
from ukethnicproj.base_population.builder import build_base_population
from ukethnicproj.data_sources.ingest import discover_datasets, fetch_all_data, validate_data
from ukethnicproj.harmonisation.schema import save_mapping_table
from ukethnicproj.projection.engine import CohortComponentEngine
from ukethnicproj.projection.scenarios import (
    create_scenario_parameters,
    load_initial_state,
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
@click.option("--nation", multiple=True, type=click.Choice(["england", "wales"]))
def build_base_population_cmd(nation: tuple[str, ...]) -> None:
    """Build harmonised mid-2022 base population from Census 2021 RM032 + MYE."""
    save_mapping_table()
    nations = tuple(nation) if nation else ("england", "wales")
    console.print(f"[bold]Building base population for:[/bold] {', '.join(nations)}")

    state, report = build_base_population(nations=nations, base_year=2022)

    console.print(f"[green]Total population: {state.total_population:,.0f}[/green]")
    for n in nations:
        console.print(
            f"  {n}: census {report.census_totals[n]:,.0f} -> "
            f"MYE mid-2022 {report.mye_totals[n]:,.0f}"
        )
        shares = report.ethnic_shares[n]
        share_str = ", ".join(f"{k} {v:.1%}" for k, v in shares.items())
        console.print(f"    Ethnic shares: {share_str}")
    console.print(f"[green]Saved to {report.output_path}[/green]")
    console.print(f"[yellow]{report.generation_note}[/yellow]")


@main.command("calibrate")
def calibrate() -> None:
    """Fetch and cache official datasets for empirical parameter calibration."""
    from ukethnicproj.calibration.fetch import fetch_all_calibration_data

    console.print("[bold]Fetching calibration datasets...[/bold]")
    fetched = fetch_all_calibration_data(force=False)
    for name, path in fetched.items():
        console.print(f"[green]{name}:[/green] {path}")
    console.print("[green]Calibration data ready.[/green]")


@main.command("simulate")
@click.option("--scenario", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--end-year", default=2050, type=int, help="Projection end year")
def simulate(scenario: Path, end_year: int) -> None:
    """Run projection for a specified scenario."""
    config = load_scenario(scenario)
    console.print(f"[bold]Scenario:[/bold] {config.name}")
    console.print(f"[red italic]{config.watermark}[/red italic]")

    initial = load_initial_state(config)
    params = create_scenario_parameters(config, state=initial)
    engine = CohortComponentEngine(params)

    console.print(
        f"[bold]Initial population:[/bold] {initial.total_population:,.0f} "
        f"({'Census 2021 + MYE 2022' if not config.placeholder else 'placeholder'})"
    )

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
        f"Census base population: {not config.placeholder or config.use_census_base}",
        f"Migration variant: {getattr(config, 'migration_variant', 'n/a')}",
        f"Fertility variant: {getattr(config, 'fertility_variant', 'n/a')}",
        f"Mortality: ONS National Life Tables 2020-2022",
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
