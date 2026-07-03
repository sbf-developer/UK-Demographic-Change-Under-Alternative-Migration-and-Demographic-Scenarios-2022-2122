"""Population state representation for cohort-component projection."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ukethnicproj import (
    AGE_MAX,
    AGE_MIN,
    BROAD_ETHNIC_GROUPS,
    GENERATIONS,
    NATIONS,
    SEXES,
)


@dataclass
class PopulationState:
    """
    Multistate population array N[nation, ethnic, generation, sex, age].

    Dimensions are indexed by position in the corresponding tuples defined
    in ukethnicproj.__init__.
    """

    array: np.ndarray
    year: int
    nations: tuple[str, ...] = NATIONS
    ethnic_groups: tuple[str, ...] = BROAD_ETHNIC_GROUPS
    generations: tuple[str, ...] = GENERATIONS
    sexes: tuple[str, ...] = SEXES
    age_min: int = AGE_MIN
    age_max: int = AGE_MAX

    @classmethod
    def zeros(cls, year: int, **kwargs: object) -> PopulationState:
        nations = kwargs.get("nations", NATIONS)
        ethnic = kwargs.get("ethnic_groups", BROAD_ETHNIC_GROUPS)
        generations = kwargs.get("generations", GENERATIONS)
        sexes = kwargs.get("sexes", SEXES)
        n_ages = AGE_MAX - AGE_MIN + 1
        shape = (len(nations), len(ethnic), len(generations), len(sexes), n_ages)
        return cls(
            array=np.zeros(shape, dtype=np.float64),
            year=year,
            nations=tuple(nations),  # type: ignore[arg-type]
            ethnic_groups=tuple(ethnic),  # type: ignore[arg-type]
            generations=tuple(generations),  # type: ignore[arg-type]
            sexes=tuple(sexes),  # type: ignore[arg-type]
        )

    @property
    def n_ages(self) -> int:
        return self.age_max - self.age_min + 1

    @property
    def total_population(self) -> float:
        return float(self.array.sum())

    def nation_total(self, nation_idx: int) -> float:
        return float(self.array[nation_idx].sum())

    def ethnic_shares(self, nation_idx: int = 0) -> dict[str, float]:
        nation_pop = self.array[nation_idx]
        totals_by_ethnic = nation_pop.sum(axis=(1, 2, 3))
        total = totals_by_ethnic.sum()
        if total == 0:
            return {e: 0.0 for e in self.ethnic_groups}
        return {
            e: float(totals_by_ethnic[i] / total)
            for i, e in enumerate(self.ethnic_groups)
        }

    def validate(self) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        errors: list[str] = []
        if np.any(self.array < 0):
            errors.append("Negative population counts detected")
        if np.any(np.isnan(self.array)):
            errors.append("NaN values in population array")
        return errors

    def copy(self) -> PopulationState:
        return PopulationState(
            array=self.array.copy(),
            year=self.year,
            nations=self.nations,
            ethnic_groups=self.ethnic_groups,
            generations=self.generations,
            sexes=self.sexes,
            age_min=self.age_min,
            age_max=self.age_max,
        )


@dataclass
class ProjectionParameters:
    """Container for projection parameters (scenario-driven)."""

    survival: np.ndarray  # [nation, ethnic, gen, sex, age]
    fertility_asfr: np.ndarray  # [nation, ethnic, gen, age] maternal
    immigration: np.ndarray  # [nation, ethnic, gen, sex, age]
    emigration: np.ndarray  # [nation, ethnic, gen, sex, age]
    internal_migration: np.ndarray  # [nation, ethnic, gen, sex, age] signed
    identity_transition: np.ndarray  # [ethnic_from, ethnic_to]
    child_ethnicity_probs: np.ndarray  # [e_m, e_p, e_child]
    partnership_probs: np.ndarray  # [e_m, g_m, e_p, g_p]
    fertility_convergence_kappa: dict[str, float] = field(default_factory=dict)
    seed: int = 42

    def validate_probabilities(self) -> list[str]:
        errors: list[str] = []
        row_sums = self.identity_transition.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-6):
            errors.append("Identity transition rows do not sum to 1")
        if np.any(self.survival < 0) or np.any(self.survival > 1):
            errors.append("Survival probabilities outside [0, 1]")
        return errors
