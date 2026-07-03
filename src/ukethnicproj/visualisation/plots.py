"""Publication-quality visualisation for projection outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ukethnicproj import REPORT_YEARS, WATERMARK
from ukethnicproj.projection.engine import ProjectionResult


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
        }
    )


def plot_ethnic_shares_trajectory(
    result: ProjectionResult,
    *,
    nation_idx: int = 0,
    output_path: Path,
    model_version: str = "A-deterministic-v0.1",
) -> Path:
    """Plot ethnic population shares over time with counts annotation."""
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

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for e_idx, ethnic in enumerate(ethnic_groups):
        ax1.plot(years, shares[:, e_idx] * 100, label=ethnic.replace("_", " ").title())

    ax1.set_ylabel("Population share (%)")
    ax1.set_title(
        f"Ethnic composition trajectory — {result.scenario_name}\n"
        f"Nation: {result.trajectory[0].nations[nation_idx]} | "
        f"Model: {model_version}"
    )
    ax1.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax1.set_ylim(0, None)
    ax1.grid(True, alpha=0.3)

    for e_idx, ethnic in enumerate(ethnic_groups):
        ax2.plot(years, counts[:, e_idx], label=ethnic.replace("_", " ").title())

    ax2.set_xlabel("Year")
    ax2.set_ylabel("Population (persons)")
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )
    ax2.grid(True, alpha=0.3)

    # Report year markers
    for yr in REPORT_YEARS:
        if years[0] <= yr <= years[-1]:
            ax1.axvline(yr, color="gray", linestyle=":", alpha=0.5)
            ax2.axvline(yr, color="gray", linestyle=":", alpha=0.5)

    fig.text(
        0.5,
        0.01,
        f"{result.watermark or WATERMARK} | Source: ukethnicproj | "
        f"Uncertainty: deterministic scenario (not probabilistic)",
        ha="center",
        fontsize=7,
        style="italic",
        color="red",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_age_pyramid(
    state: "PopulationState",
    *,
    nation_idx: int = 0,
    ethnic_idx: int | None = None,
    output_path: Path,
    scenario_name: str = "",
    model_version: str = "A-deterministic-v0.1",
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

    fig, ax = plt.subplots(figsize=(8, 10))
    ax.barh(ages, -pop[:, f_idx, :].sum(axis=0), color="#4C72B0", label="Female", height=0.8)
    ax.barh(ages, pop[:, m_idx, :].sum(axis=0), color="#DD8452", label="Male", height=0.8)
    ax.set_xlabel("Population count")
    ax.set_ylabel("Age")
    ax.set_title(
        f"Age-sex pyramid — {title_suffix}\n"
        f"Year: {state.year} | Scenario: {scenario_name} | Model: {model_version}"
    )
    ax.legend()
    ax.axvline(0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3)

    fig.text(
        0.5,
        0.01,
        f"{WATERMARK} | Source: ukethnicproj | Model: {model_version}",
        ha="center",
        fontsize=7,
        style="italic",
        color="red",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
