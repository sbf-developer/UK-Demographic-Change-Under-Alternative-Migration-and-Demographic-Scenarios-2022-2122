"""Assemble empirically calibrated projection parameters."""

from __future__ import annotations

import numpy as np

from ukethnicproj import BROAD_ETHNIC_GROUPS, GENERATIONS
from ukethnicproj.projection.scenarios import ScenarioConfig
from ukethnicproj.projection.state import PopulationState, ProjectionParameters
from ukethnicproj.calibration.fertility import build_fertility_array
from ukethnicproj.calibration.migration import build_migration_arrays
from ukethnicproj.calibration.mortality import build_survival_array


def _child_ethnicity_probs(n_ethnic: int, ethnic_groups: list[str]) -> np.ndarray:
    """
    Child ethnicity assignment probabilities.

    Census parental ethnicity tables (Phase 7) will replace this specification.
    Current implementation uses same-ethnicity endogamy with mixed-ethnicity
    outcomes for mixed-parent pairs, consistent with Census mixed-group prevalence.
    """
    child_probs = np.zeros((n_ethnic, n_ethnic, n_ethnic))
    mixed_idx = ethnic_groups.index("mixed")
    for e_m in range(n_ethnic):
        for e_p in range(n_ethnic):
            if e_m == e_p:
                child_probs[e_m, e_p, e_m] = 0.85
                child_probs[e_m, e_p, mixed_idx] = 0.15
            else:
                child_probs[e_m, e_p, mixed_idx] = 0.60
                child_probs[e_m, e_p, e_m] = 0.20
                child_probs[e_m, e_p, e_p] = 0.20
    return child_probs


def _partnership_probs(n_ethnic: int, n_gen: int) -> np.ndarray:
    """Within-group partnership weights (Census household tables; Phase 7)."""
    partnership = np.zeros((n_ethnic, n_gen, n_ethnic, n_gen))
    for e in range(n_ethnic):
        for g in range(n_gen):
            partnership[e, g, e, g] = 0.70
            remainder = 0.30 / (n_ethnic * n_gen - 1)
            for e2 in range(n_ethnic):
                for g2 in range(n_gen):
                    if e2 != e or g2 != g:
                        partnership[e, g, e2, g2] = remainder
    return partnership


def build_empirical_parameters(
    config: ScenarioConfig,
    state: PopulationState,
) -> ProjectionParameters:
    """
    Build projection parameters from official ONS/Nomis data and Census 2021.

    Sources:
    - Mortality: ONS National Life Tables 2020-2022 (qx)
    - Fertility: Nomis live births 2022 + Census ethnic fertility differentials
    - Migration: ONS 2022-based NPP variant volumes + Census COB age/ethnic profiles
    """
    nations = tuple(config.nations)
    n_nations = len(nations)
    n_ethnic = len(config.ethnic_groups)
    n_gen = len(GENERATIONS)

    migration_variant = getattr(config, "migration_variant", "principal")
    fertility_variant = getattr(config, "fertility_variant", "principal")

    survival = build_survival_array(n_nations, n_ethnic, n_gen)
    fertility = build_fertility_array(
        nations,
        fertility_variant=fertility_variant,
    )
    immigration, emigration = build_migration_arrays(
        state,
        nations,
        migration_variant=migration_variant,
        ethnic_composition=config.migration.composition or None,
    )

    identity = np.eye(n_ethnic)
    if config.identity.mode != "fixed" and config.identity.switching_rate > 0:
        off_diag = config.identity.switching_rate / (n_ethnic - 1)
        identity = identity * (1 - config.identity.switching_rate)
        identity += off_diag * (1 - np.eye(n_ethnic))

    return ProjectionParameters(
        survival=survival,
        fertility_asfr=fertility,
        immigration=immigration,
        emigration=emigration,
        internal_migration=np.zeros_like(immigration),
        identity_transition=identity,
        child_ethnicity_probs=_child_ethnicity_probs(n_ethnic, config.ethnic_groups),
        partnership_probs=_partnership_probs(n_ethnic, n_gen),
        fertility_convergence_kappa=config.fertility.kappa,
        seed=config.seed,
    )
