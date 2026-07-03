"""Publication-quality visualisation for projection outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib.pyplot as plt
import numpy as np

from ukethnicproj import REPORT_YEARS, WATERMARK
from ukethnicproj.projection.engine import ProjectionResult

# Consistent palette across all figures (colorblind-friendly)
ETHNIC_COLORS = {
    "white": "#4C72B0",
    "mixed": "#DD8452",
    "asian": "#55A868",
    "black": "#C44E52",
    "other": "#8172B3",
}

SCENARIO_COLORS = {
    "zero": "#636363",
    "low": "#3182bd",
    "principal": "#31a354",
    "high": "#de2d26",
}

MIGRATION_VARIANT_LABELS = {
    "zero": "Zero net migration",
    "low": "Low migration (+120k net UK/yr)",
    "principal": "Principal migration (+340k net UK/yr)",
    "low_2022npp": "Low migration (+120k net UK/yr)",
    "high": "High migration (+525k net UK/yr)",
    "high_2022npp": "High migration (+525k net UK/yr)",
}


def scenario_display_label(
    scenario_name: str,
    *,
    migration_variant: str | None = None,
) -> str:
    """Human-readable scenario label for titles and legends."""
    if migration_variant and migration_variant in MIGRATION_VARIANT_LABELS:
        return MIGRATION_VARIANT_LABELS[migration_variant]
    aliases = {
        "census_2021_mid2022_baseline": MIGRATION_VARIANT_LABELS["principal"],
        "migration_low_2022npp": MIGRATION_VARIANT_LABELS["low"],
        "migration_high_2022npp": MIGRATION_VARIANT_LABELS["high"],
        "migration_zero": MIGRATION_VARIANT_LABELS["zero"],
    }
    return aliases.get(scenario_name, scenario_name.replace("_", " ").title())


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _ethnic_color(ethnic: str) -> str:
    return ETHNIC_COLORS.get(ethnic, "#333333")


def _scenario_color(migration_variant: str | None, scenario_name: str) -> str:
    variant = migration_variant or scenario_name
    for key, color in SCENARIO_COLORS.items():
        if key in variant:
            return color
    return "#333333"


def _add_report_year_markers(ax: plt.Axes, years: list[int]) -> None:
    for yr in REPORT_YEARS:
        if years[0] <= yr <= years[-1]:
            ax.axvline(yr, color="gray", linestyle=":", alpha=0.45, linewidth=0.8)
            if yr in (2050, 2122):
                ax.text(
                    yr,
                    ax.get_ylim()[1],
                    str(yr),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color="gray",
                )


def _add_watermark(fig: plt.Figure, watermark: str | None = None) -> None:
    fig.text(
        0.5,
        0.01,
        f"{watermark or WATERMARK} | Source: ukethnicproj | "
        "Uncertainty: deterministic scenario (not probabilistic)",
        ha="center",
        fontsize=7,
        style="italic",
        color="#8B0000",
    )


def plot_ethnic_shares_trajectory(
    result: ProjectionResult,
    *,
    nation_idx: int = 0,
    output_path: Path,
    model_version: str = "A-deterministic-v0.1",
    migration_variant: str | None = None,
    end_year: int | None = None,
) -> Path:
    """Plot ethnic population shares over time with counts panel."""
    _apply_style()
    ethnic_groups = result.trajectory[0].ethnic_groups
    years = [s.year for s in result.trajectory]
    shares = np.array(
        [[s.ethnic_shares(nation_idx)[e] for e in ethnic_groups] for s in result.trajectory]
    )
    counts = np.array(
        [
            [s.array[nation_idx, e_idx].sum() for e_idx in range(len(ethnic_groups))]
            for s in result.trajectory
        ]
    )

    label = scenario_display_label(result.scenario_name, migration_variant=migration_variant)
    horizon = end_year or years[-1]
    nation = result.trajectory[0].nations[nation_idx].replace("_", " ").title()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for e_idx, ethnic in enumerate(ethnic_groups):
        color = _ethnic_color(ethnic)
        ax1.plot(
            years,
            shares[:, e_idx] * 100,
            label=ethnic.replace("_", " ").title(),
            color=color,
            linewidth=2,
        )
        ax2.plot(
            years,
            counts[:, e_idx],
            label=ethnic.replace("_", " ").title(),
            color=color,
            linewidth=1.8,
        )

    ax1.set_ylabel("Population share (%)")
    ax1.set_title(
        f"Ethnic composition in {nation}, 2022–{horizon}\n{label} | Model {model_version}",
        fontsize=11,
    )
    ax1.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8, frameon=False)
    ax1.set_ylim(0, max(shares.max() * 100 * 1.05, 10))
    ax1.grid(True, alpha=0.25)
    _add_report_year_markers(ax1, years)

    ax2.set_xlabel("Year")
    ax2.set_ylabel("Population (persons)")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
    ax2.grid(True, alpha=0.25)
    _add_report_year_markers(ax2, years)

    _add_watermark(fig, result.watermark)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_scenario_comparison(
    results: Mapping[str, ProjectionResult],
    *,
    migration_variants: Mapping[str, str | None] | None = None,
    output_dir: Path,
    nation_idx: int = 0,
    model_version: str = "A-deterministic-v0.1",
) -> list[Path]:
    """Generate comparison figures across multiple scenario results."""
    _apply_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    variants = migration_variants or {}
    saved: list[Path] = []

    # --- Total population comparison ---
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, result in results.items():
        years = [s.year for s in result.trajectory]
        totals = [s.total_population for s in result.trajectory]
        variant = variants.get(name)
        ax.plot(
            years,
            totals,
            label=scenario_display_label(name, migration_variant=variant),
            color=_scenario_color(variant, name),
            linewidth=2.2,
        )
    ax.set_title(
        f"England & Wales total population by migration scenario, 2022–{years[-1]}\n"
        f"Model {model_version} | Fertility: ONS principal (TFR 1.45) | Mortality: ONS 2020–2022",
        fontsize=10,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Population (persons)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.0f}M"))
    ax.legend(loc="best", frameon=False, fontsize=9)
    ax.grid(True, alpha=0.25)
    _add_report_year_markers(ax, years)
    _add_watermark(fig)
    path = output_dir / "comparison_total_population.png"
    fig.savefig(path)
    plt.close(fig)
    saved.append(path)

    # --- White share in England comparison ---
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, result in results.items():
        years = [s.year for s in result.trajectory]
        white_idx = result.trajectory[0].ethnic_groups.index("white")
        shares = [
            s.ethnic_shares(nation_idx)[result.trajectory[0].ethnic_groups[white_idx]]
            for s in result.trajectory
        ]
        variant = variants.get(name)
        ax.plot(
            years,
            np.array(shares) * 100,
            label=scenario_display_label(name, migration_variant=variant),
            color=_scenario_color(variant, name),
            linewidth=2.2,
        )
    ax.set_title(
        f"White population share in England by migration scenario, 2022–{years[-1]}\n"
        f"Same fertility and mortality assumptions across scenarios",
        fontsize=10,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("White share (%)")
    ax.legend(loc="best", frameon=False, fontsize=9)
    ax.grid(True, alpha=0.25)
    _add_report_year_markers(ax, years)
    _add_watermark(fig)
    path = output_dir / "comparison_white_share_england.png"
    fig.savefig(path)
    plt.close(fig)
    saved.append(path)

    # --- Small multiples: ethnic shares by scenario ---
    n_scenarios = len(results)
    n_cols = 2
    n_rows = int(np.ceil(n_scenarios / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows), sharex=True, sharey=True)
    axes_flat = np.atleast_1d(axes).flatten()

    for ax_idx, (name, result) in enumerate(results.items()):
        ax = axes_flat[ax_idx]
        ethnic_groups = result.trajectory[0].ethnic_groups
        years = [s.year for s in result.trajectory]
        shares = np.array(
            [[s.ethnic_shares(nation_idx)[e] for e in ethnic_groups] for s in result.trajectory]
        )
        variant = variants.get(name)
        for e_idx, ethnic in enumerate(ethnic_groups):
            ax.plot(
                years,
                shares[:, e_idx] * 100,
                color=_ethnic_color(ethnic),
                linewidth=1.6,
                label=ethnic.replace("_", " ").title() if ax_idx == 0 else None,
            )
        ax.set_title(
            scenario_display_label(name, migration_variant=variant),
            fontsize=10,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.25)
        _add_report_year_markers(ax, years)

    for ax in axes_flat[n_scenarios:]:
        ax.set_visible(False)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=9)
    fig.suptitle(
        f"Ethnic composition in England by migration scenario (2022–{years[-1]})",
        fontsize=12,
        y=1.01,
    )
    fig.text(0.5, -0.02, WATERMARK, ha="center", fontsize=7, style="italic", color="#8B0000")
    fig.tight_layout()
    path = output_dir / "comparison_ethnic_shares_panel.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    # --- Report-year bar chart: White share at key years ---
    report_years = [yr for yr in REPORT_YEARS if yr <= years[-1]]
    fig, ax = plt.subplots(figsize=(10, 5))
    bar_width = 0.18
    x = np.arange(len(report_years))
    for i, (name, result) in enumerate(results.items()):
        variant = variants.get(name)
        white_shares = []
        for yr in report_years:
            state = next(s for s in result.trajectory if s.year == yr)
            white_shares.append(state.ethnic_shares(nation_idx)["white"] * 100)
        offset = (i - (len(results) - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            white_shares,
            width=bar_width,
            label=scenario_display_label(name, migration_variant=variant),
            color=_scenario_color(variant, name),
            alpha=0.9,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(report_years)
    ax.set_xlabel("Report year")
    ax.set_ylabel("White share in England (%)")
    ax.set_title("White share at report years across migration scenarios")
    ax.legend(loc="best", frameon=False, fontsize=8)
    ax.grid(True, axis="y", alpha=0.25)
    _add_watermark(fig)
    path = output_dir / "comparison_white_share_report_years.png"
    fig.savefig(path)
    plt.close(fig)
    saved.append(path)

    return saved


def plot_age_pyramid(
    state: "PopulationState",
    *,
    nation_idx: int = 0,
    ethnic_idx: int | None = None,
    output_path: Path,
    scenario_name: str = "",
    model_version: str = "A-deterministic-v0.1",
    migration_variant: str | None = None,
) -> Path:
    """Plot age-sex pyramid for a given state."""
    from ukethnicproj.projection.state import PopulationState

    _apply_style()
    if ethnic_idx is not None:
        pop = state.array[nation_idx, ethnic_idx]
        title_suffix = state.ethnic_groups[ethnic_idx]
    else:
        pop = state.array[nation_idx].sum(axis=0)
        title_suffix = "All ethnic groups"

    f_idx = list(state.sexes).index("female")
    m_idx = list(state.sexes).index("male")
    ages = np.arange(state.age_min, state.age_max + 1)
    label = scenario_display_label(scenario_name, migration_variant=migration_variant)

    fig, ax = plt.subplots(figsize=(8, 10))
    ax.barh(ages, -pop[:, f_idx, :].sum(axis=0), color="#4C72B0", label="Female", height=0.8)
    ax.barh(ages, pop[:, m_idx, :].sum(axis=0), color="#DD8452", label="Male", height=0.8)
    ax.set_xlabel("Population count")
    ax.set_ylabel("Age")
    ax.set_title(
        f"Age-sex pyramid — {title_suffix.replace('_', ' ').title()}\n"
        f"Year {state.year} | {label} | Model {model_version}"
    )
    ax.legend()
    ax.axvline(0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3)
    _add_watermark(fig)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
