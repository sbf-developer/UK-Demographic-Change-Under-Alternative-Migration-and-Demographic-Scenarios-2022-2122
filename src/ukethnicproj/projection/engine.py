"""Deterministic multistate cohort-component projection engine (Model A)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ukethnicproj import AGE_MAX, GENERATIONS
from ukethnicproj.projection.state import PopulationState, ProjectionParameters

# Sex ratio at birth (male share); ONS 2022 order of magnitude
MALE_BIRTH_SHARE = 0.512


@dataclass
class StepFlows:
    """Annual demographic flow totals for accounting validation."""

    births: float
    deaths: float
    immigration: float
    emigration: float
    internal_net: float


@dataclass
class ProjectionResult:
    """Results from a projection run."""

    trajectory: list[PopulationState]
    scenario_name: str
    flows: list[StepFlows]
    model_version: str = "A-deterministic-v0.1"
    watermark: str = ""


class CohortComponentEngine:
    """
    Model A: deterministic multistate cohort-component projection.

    Implements:
        N_{n,e,g,s,a+1,t+1} = sum_{e',g'} N_{e',g',s,a,t} S Q
                               + I - O + M^{int}

    where M^{int} is net internal migration between UK nations.
    Deaths are implicit in the survival operator S.

    Phase 1 limitations (documented):
    - Fertility convergence parameters are stored but not yet applied.
    - Partnership weights do not require male partners in the population.
    - Generation assignment at birth uses simplified parent-nativity rules.
    """

    FOREIGN_BORN = frozenset({"foreign_born_adult", "foreign_born_child"})

    def __init__(self, params: ProjectionParameters) -> None:
        self.params = params
        errors = params.validate_probabilities()
        if errors:
            raise ValueError(f"Invalid parameters: {errors}")

    @classmethod
    def _child_generation(cls, g_m: int, g_p: int) -> int:
        """Assign UK-born child generation from parent generation indices."""
        g_m_name = GENERATIONS[g_m]
        g_p_name = GENERATIONS[g_p]
        fb_count = sum(1 for g in (g_m_name, g_p_name) if g in cls.FOREIGN_BORN)
        if fb_count >= 2:
            return GENERATIONS.index("ukborn_two_foreign_parents")
        if fb_count == 1:
            return GENERATIONS.index("ukborn_one_foreign_parent")
        return GENERATIONS.index("ukborn_two_ukborn_parents")

    def _compute_deaths(self, state: PopulationState) -> float:
        """Deaths implied by survival probabilities."""
        survived = state.array * self.params.survival
        return float(state.array.sum() - survived.sum())

    def _survive_and_age(self, state: PopulationState) -> np.ndarray:
        """Apply survival and age cohorts forward one year."""
        n_ages = state.array.shape[-1]
        aged = np.zeros_like(state.array)

        for age_idx in range(n_ages - 2):
            aged[:, :, :, :, age_idx + 1] = (
                state.array[:, :, :, :, age_idx]
                * self.params.survival[:, :, :, :, age_idx]
            )

        aged[:, :, :, :, -1] = (
            state.array[:, :, :, :, -2] * self.params.survival[:, :, :, :, -2]
            + state.array[:, :, :, :, -1] * self.params.survival[:, :, :, :, -1]
        )

        return aged

    def _apply_identity_transitions(self, array: np.ndarray) -> np.ndarray:
        """Apply ethnic identity transition matrix Q (broad groups only)."""
        q = self.params.identity_transition
        n_nations, n_ethnic, n_gen, n_sex, n_ages = array.shape
        result = np.zeros_like(array)

        for n in range(n_nations):
            for g in range(n_gen):
                for s in range(n_sex):
                    for a in range(n_ages):
                        vec = array[n, :, g, s, a]
                        result[n, :, g, s, a] = q.T @ vec

        return result

    def _compute_births(self, state: PopulationState) -> np.ndarray:
        """
        Compute newborn population by ethnic group, sex, and generation.

        Phase 1 placeholder: uses maternal ASFR and simplified partnership
        and child-generation assignment. Does not require male partners
        to be present in the population stock.
        """
        n_nations, n_ethnic, n_gen, n_sex, _ = state.array.shape
        f_idx = list(state.sexes).index("female")
        m_idx = list(state.sexes).index("male")
        births = np.zeros((n_nations, n_ethnic, n_gen, n_sex, 1))

        child_probs = self.params.child_ethnicity_probs
        partnership = self.params.partnership_probs

        for n in range(n_nations):
            for e_m in range(n_ethnic):
                for g_m in range(n_gen):
                    for a in range(state.n_ages):
                        mothers = state.array[n, e_m, g_m, f_idx, a]
                        if mothers <= 0:
                            continue
                        asfr = self.params.fertility_asfr[n, e_m, g_m, a]
                        expected_births = mothers * asfr

                        for e_p in range(n_ethnic):
                            for g_p in range(n_gen):
                                p_partner = partnership[e_m, g_m, e_p, g_p]
                                g_child = self._child_generation(g_m, g_p)
                                for e_child in range(n_ethnic):
                                    p_child = child_probs[e_m, e_p, e_child]
                                    n_births = expected_births * p_partner * p_child
                                    births[n, e_child, g_child, f_idx, 0] += (
                                        n_births * (1 - MALE_BIRTH_SHARE)
                                    )
                                    births[n, e_child, g_child, m_idx, 0] += (
                                        n_births * MALE_BIRTH_SHARE
                                    )

        return births

    def step(self, state: PopulationState) -> tuple[PopulationState, StepFlows]:
        """Advance population one year and return flow totals."""
        deaths = self._compute_deaths(state)
        aged = self._survive_and_age(state)
        transitioned = self._apply_identity_transitions(aged)

        immigration_total = float(self.params.immigration.sum())
        emigration_arr = np.minimum(self.params.emigration, transitioned)
        emigration_total = float(emigration_arr.sum())
        internal_net = float(self.params.internal_migration.sum())

        migrated = (
            transitioned
            + self.params.immigration
            - emigration_arr
            + self.params.internal_migration
        )

        births_array = self._compute_births(state)
        births_total = float(births_array.sum())
        migrated[:, :, :, :, 0] += births_array[:, :, :, :, 0]

        new_array = migrated
        if np.any(new_array < 0):
            raise ValueError("Negative population counts after migration and births")

        new_state = PopulationState(
            array=new_array,
            year=state.year + 1,
            nations=state.nations,
            ethnic_groups=state.ethnic_groups,
            generations=state.generations,
            sexes=state.sexes,
        )

        flows = StepFlows(
            births=births_total,
            deaths=deaths,
            immigration=immigration_total,
            emigration=emigration_total,
            internal_net=internal_net,
        )
        return new_state, flows

    def project(
        self,
        initial: PopulationState,
        end_year: int,
        scenario_name: str = "unnamed",
        watermark: str = "",
    ) -> ProjectionResult:
        """Run projection from initial state to end_year inclusive."""
        trajectory = [initial.copy()]
        flows_list: list[StepFlows] = []
        current = initial.copy()

        while current.year < end_year:
            current, flows = self.step(current)
            if not self.accounting_check(current, trajectory[-1], flows):
                raise RuntimeError(
                    f"Accounting identity failed at year {current.year}"
                )
            trajectory.append(current.copy())
            flows_list.append(flows)

        return ProjectionResult(
            trajectory=trajectory,
            scenario_name=scenario_name,
            flows=flows_list,
            watermark=watermark,
        )

    @staticmethod
    def accounting_check(
        state_t1: PopulationState,
        state_t: PopulationState,
        flows: StepFlows,
        tolerance: float = 1.0,
    ) -> bool:
        """
        Verify P_{t+1} = P_t + B - D + I - O + M^{int}.

        Tolerance is in persons (not relative) to accommodate large populations.
        """
        expected = (
            state_t.total_population
            + flows.births
            - flows.deaths
            + flows.immigration
            - flows.emigration
            + flows.internal_net
        )
        actual = state_t1.total_population
        return abs(expected - actual) < tolerance
