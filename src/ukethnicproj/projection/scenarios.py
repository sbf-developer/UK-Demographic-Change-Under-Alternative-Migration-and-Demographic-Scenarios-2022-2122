"""Scenario configuration loading and placeholder parameter generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml
from pydantic import BaseModel, Field

from ukethnicproj import (
    AGE_MAX,
    AGE_MIN,
    BROAD_ETHNIC_GROUPS,
    GENERATIONS,
    NATIONS,
    SEXES,
    WATERMARK,
)
from ukethnicproj.projection.state import PopulationState, ProjectionParameters


class MigrationScenario(BaseModel):
    annual_immigration: float = 0.0
    annual_emigration: float = 0.0
    composition: dict[str, float] = Field(default_factory=dict)


class FertilityScenario(BaseModel):
    convergence: str = "moderate"
    kappa: dict[str, float] = Field(default_factory=dict)
    uk_tfr: float = 1.49  # ONS 2022-based interim national projection assumption


class IdentityScenario(BaseModel):
    mode: str = "fixed"
    switching_rate: float = 0.0


class ScenarioConfig(BaseModel):
    name: str
    description: str
    base_year: int = 2022
    end_year: int = 2122
    watermark: str = WATERMARK
    nations: list[str] = Field(default_factory=lambda: list(NATIONS))
    ethnic_groups: list[str] = Field(default_factory=lambda: list(BROAD_ETHNIC_GROUPS))
    migration: MigrationScenario = Field(default_factory=MigrationScenario)
    fertility: FertilityScenario = Field(default_factory=FertilityScenario)
    identity: IdentityScenario = Field(default_factory=IdentityScenario)
    mortality: str = "common"
    seed: int = 42
    placeholder: bool = True
    use_census_base: bool = False
    migration_variant: str = "principal"  # zero, low, principal, high (ONS 2022-based NPP)
    fertility_variant: str = "principal"  # low, principal, high (ONS 2022-based NPP)


def load_initial_state(config: ScenarioConfig) -> PopulationState:
    """Load initial population from Census base or placeholder generator."""
    if config.use_census_base or not config.placeholder:
        from ukethnicproj.base_population.builder import (
            base_population_available,
            build_base_population,
            load_base_population,
        )

        nations = tuple(config.nations)
        if not base_population_available():
            build_base_population(nations=nations, base_year=config.base_year)
        return load_base_population(nations=nations)
    return create_placeholder_initial_state(config)


def create_scenario_parameters(
    config: ScenarioConfig,
    state: PopulationState | None = None,
) -> ProjectionParameters:
    """Create projection parameters from official data or placeholders."""
    if config.use_census_base or not config.placeholder:
        from ukethnicproj.calibration.parameters import build_empirical_parameters

        pop = state or load_initial_state(config)
        return build_empirical_parameters(config, pop)
    return create_placeholder_parameters(config)


def load_scenario(path: Path) -> ScenarioConfig:
    """Load scenario from YAML file."""
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ScenarioConfig.model_validate(data)


def create_placeholder_initial_state(
    config: ScenarioConfig,
    total_population: float = 1_000_000.0,
) -> PopulationState:
    """
    Create a small illustrative initial population.

    NOT empirical — for methodological demonstration only.
    """
    state = PopulationState.zeros(year=config.base_year, nations=tuple(config.nations))
    rng = np.random.default_rng(config.seed)

    # Distribute across broad ethnic groups using approximate England shares
    # Source: Census 2021 RM032 broad aggregation (illustrative only)
    ethnic_shares = np.array([0.81, 0.03, 0.09, 0.04, 0.03])
    ethnic_shares = ethnic_shares / ethnic_shares.sum()

    n_nations = len(config.nations)
    nation_shares = np.ones(n_nations) / n_nations

    for n_idx in range(n_nations):
        nation_pop = total_population * nation_shares[n_idx]
        for e_idx, share in enumerate(ethnic_shares):
            group_pop = nation_pop * share
            # Assign mostly to UK-born two UK-born parents, generation 4
            g_idx = GENERATIONS.index("ukborn_two_ukborn_parents")
            # Spread across ages using a rough stable-ish structure
            age_weights = rng.dirichlet(np.ones(state.n_ages))
            for s_idx in range(len(SEXES)):
                sex_share = 0.5
                for a_idx in range(state.n_ages):
                    state.array[n_idx, e_idx, g_idx, s_idx, a_idx] = (
                        group_pop * sex_share * age_weights[a_idx]
                    )

    return state


def create_placeholder_parameters(config: ScenarioConfig) -> ProjectionParameters:
    """
    Generate clearly labelled placeholder projection parameters.

    These are NOT calibrated to UK data. They exist solely to demonstrate
    the projection machinery.
    """
    n_nations = len(config.nations)
    n_ethnic = len(config.ethnic_groups)
    n_gen = len(GENERATIONS)
    n_sex = len(SEXES)
    n_ages = AGE_MAX - AGE_MIN + 1

    rng = np.random.default_rng(config.seed)

    # Mortality: approximate UK life table survival (placeholder)
    # Based on ONS 2020-2022 national life tables order of magnitude
    ages = np.arange(n_ages)
    survival = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))
    for s_idx in range(n_sex):
        # Female mortality lower than male (illustrative)
        base_hazard = 0.0005 + 0.0001 * (ages ** 2.5) / (100 ** 2.5)
        if s_idx == 1:  # male
            base_hazard *= 1.15
        surv_probs = np.exp(-base_hazard)
        for n in range(n_nations):
            for e in range(n_ethnic):
                for g in range(n_gen):
                    survival[n, e, g, s_idx, :] = surv_probs

    # Fertility: age-specific fertility rates (placeholder)
    # Peak around ages 30-34, zero outside reproductive ages
    fertility = np.zeros((n_nations, n_ethnic, n_gen, n_ages))
    reproductive = (ages >= 15) & (ages <= 49)
    age_profile = np.exp(-0.5 * ((ages - 30) / 8) ** 2)
    age_profile = age_profile / age_profile[reproductive].sum()
    base_tfr = config.fertility.uk_tfr
    for n in range(n_nations):
        for e in range(n_ethnic):
            for g in range(n_gen):
                fertility[n, e, g, reproductive] = base_tfr * age_profile[reproductive]

    # Migration (placeholder constant flows)
    immigration = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))
    emigration = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))
    if config.migration.annual_immigration > 0:
        comp = config.migration.composition or {
            e: 1.0 / n_ethnic for e in config.ethnic_groups
        }
        total = sum(comp.values())
        for n in range(n_nations):
            nation_imm = config.migration.annual_immigration / n_nations
            for e_idx, e_name in enumerate(config.ethnic_groups):
                share = comp.get(e_name, 0) / total
                # Immigrants predominantly working age, foreign-born adult
                g_idx = GENERATIONS.index("foreign_born_adult")
                for a_idx in range(20, 45):
                    for s_idx in range(n_sex):
                        immigration[n, e_idx, g_idx, s_idx, a_idx] = (
                            nation_imm * share / (25 * n_sex)
                        )

    if config.migration.annual_emigration > 0:
        for n in range(n_nations):
            emig_rate = config.migration.annual_emigration / (
                n_nations * n_ethnic * n_gen * n_sex * n_ages
            )
            emigration[n] = emig_rate

    # Internal migration: zero net at UK level (placeholder)
    internal = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))

    # Identity transition: mostly fixed (diagonal)
    identity = np.eye(n_ethnic)
    if config.identity.mode != "fixed" and config.identity.switching_rate > 0:
        off_diag = config.identity.switching_rate / (n_ethnic - 1)
        identity = identity * (1 - config.identity.switching_rate)
        identity += off_diag * (1 - np.eye(n_ethnic))

    # Child ethnicity: mostly same as mother (placeholder)
    child_probs = np.zeros((n_ethnic, n_ethnic, n_ethnic))
    for e_m in range(n_ethnic):
        for e_p in range(n_ethnic):
            if e_m == e_p:
                child_probs[e_m, e_p, e_m] = 0.85
                # Distribute remainder to mixed
                mixed_idx = config.ethnic_groups.index("mixed")
                child_probs[e_m, e_p, mixed_idx] = 0.15
            else:
                mixed_idx = config.ethnic_groups.index("mixed")
                child_probs[e_m, e_p, mixed_idx] = 0.60
                child_probs[e_m, e_p, e_m] = 0.20
                child_probs[e_m, e_p, e_p] = 0.20

    # Partnership: mostly within-group (placeholder)
    partnership = np.zeros((n_ethnic, n_gen, n_ethnic, n_gen))
    for e in range(n_ethnic):
        for g in range(n_gen):
            partnership[e, g, e, g] = 0.70
            remainder = 0.30 / (n_ethnic * n_gen - 1)
            for e2 in range(n_ethnic):
                for g2 in range(n_gen):
                    if e2 != e or g2 != g:
                        partnership[e, g, e2, g2] = remainder

    return ProjectionParameters(
        survival=survival,
        fertility_asfr=fertility,
        immigration=immigration,
        emigration=emigration,
        internal_migration=internal,
        identity_transition=identity,
        child_ethnicity_probs=child_probs,
        partnership_probs=partnership,
        fertility_convergence_kappa=config.fertility.kappa,
        seed=config.seed,
    )
