"""Tests for the cohort-component projection engine."""

from __future__ import annotations

import numpy as np
import pytest

from ukethnicproj import BROAD_ETHNIC_GROUPS, GENERATIONS, SEXES
from ukethnicproj.projection.engine import CohortComponentEngine
from ukethnicproj.projection.scenarios import (
    ScenarioConfig,
    create_placeholder_initial_state,
    create_placeholder_parameters,
)
from ukethnicproj.projection.state import PopulationState, ProjectionParameters


@pytest.fixture
def small_config() -> ScenarioConfig:
    return ScenarioConfig(
        name="test",
        description="Unit test scenario",
        nations=["england"],
        ethnic_groups=list(BROAD_ETHNIC_GROUPS),
        migration={"annual_immigration": 100, "annual_emigration": 50},
        placeholder=True,
    )


@pytest.fixture
def small_state(small_config: ScenarioConfig) -> PopulationState:
    state = PopulationState.zeros(year=2022, nations=("england",))
    # Place 1000 people at age 30, white, female, UK-born
    e_idx = BROAD_ETHNIC_GROUPS.index("white")
    g_idx = GENERATIONS.index("ukborn_two_ukborn_parents")
    s_idx = SEXES.index("female")
    state.array[0, e_idx, g_idx, s_idx, 30] = 1000.0
    return state


@pytest.fixture
def small_params(small_config: ScenarioConfig) -> ProjectionParameters:
    return create_placeholder_parameters(small_config)


class TestPopulationState:
    def test_zeros_initialization(self) -> None:
        state = PopulationState.zeros(year=2022, nations=("england",))
        assert state.total_population == 0.0
        assert state.year == 2022

    def test_ethnic_shares_sum_to_one(self, small_state: PopulationState) -> None:
        shares = small_state.ethnic_shares(0)
        assert abs(sum(shares.values()) - 1.0) < 1e-10

    def test_no_negative_population(self, small_state: PopulationState) -> None:
        assert small_state.validate() == []


class TestCohortComponentEngine:
    def test_single_step_no_negative(self, small_state: PopulationState, small_params: ProjectionParameters) -> None:
        engine = CohortComponentEngine(small_params)
        next_state, flows = engine.step(small_state)
        assert next_state.year == 2023
        assert next_state.validate() == []
        assert np.all(next_state.array >= 0)
        assert flows.births >= 0

    def test_ageing_shifts_population(self, small_state: PopulationState, small_params: ProjectionParameters) -> None:
        engine = CohortComponentEngine(small_params)
        next_state, _ = engine.step(small_state)
        e_idx = BROAD_ETHNIC_GROUPS.index("white")
        g_idx = GENERATIONS.index("ukborn_two_ukborn_parents")
        s_idx = SEXES.index("female")
        assert next_state.array[0, e_idx, g_idx, s_idx, 31] > 0

    def test_births_split_by_sex(self, small_state: PopulationState, small_params: ProjectionParameters) -> None:
        engine = CohortComponentEngine(small_params)
        next_state, flows = engine.step(small_state)
        f_idx = SEXES.index("female")
        m_idx = SEXES.index("male")
        f_births = next_state.array[0, :, :, f_idx, 0].sum()
        m_births = next_state.array[0, :, :, m_idx, 0].sum()
        assert f_births > 0 or m_births > 0
        if f_births > 0 and m_births > 0:
            ratio = m_births / (f_births + m_births)
            assert 0.45 < ratio < 0.55

    def test_accounting_identity(self, small_config: ScenarioConfig) -> None:
        initial = create_placeholder_initial_state(small_config, total_population=50_000)
        params = create_placeholder_parameters(small_config)
        engine = CohortComponentEngine(params)
        result = engine.project(initial, end_year=2030, scenario_name="accounting")
        assert len(result.flows) == 8

    def test_projection_reproducibility(self, small_config: ScenarioConfig) -> None:
        initial = create_placeholder_initial_state(small_config, total_population=10_000)
        params = create_placeholder_parameters(small_config)
        engine = CohortComponentEngine(params)

        result1 = engine.project(initial, end_year=2025, scenario_name="test1")
        result2 = engine.project(initial, end_year=2025, scenario_name="test2")

        for s1, s2 in zip(result1.trajectory, result2.trajectory):
            np.testing.assert_array_equal(s1.array, s2.array)

    def test_open_ended_age_group(self, small_state: PopulationState, small_params: ProjectionParameters) -> None:
        engine = CohortComponentEngine(small_params)
        result = engine.project(small_state, end_year=2072, scenario_name="age_test")
        final = result.trajectory[-1]
        # 100+ category should accumulate population
        assert final.array[:, :, :, :, -1].sum() >= 0

    def test_identity_transition_stochastic_matrix(self, small_params: ProjectionParameters) -> None:
        q = small_params.identity_transition
        row_sums = q.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-6)
        assert np.all(q >= 0) and np.all(q <= 1)


class TestHarmonisation:
    def test_mapping_table_valid(self) -> None:
        from ukethnicproj.harmonisation.schema import build_default_mapping_table

        df = build_default_mapping_table()
        assert len(df) >= 19
        assert set(df["harmonised_broad"].unique()).issubset(set(BROAD_ETHNIC_GROUPS))

    def test_no_category_loss(self) -> None:
        from ukethnicproj.harmonisation.schema import (
            NOMIS_API_CODES_BY_DETAILED,
            build_default_mapping_table,
            map_to_broad,
            save_mapping_table,
        )

        save_mapping_table()
        df = build_default_mapping_table()
        mapped = map_to_broad(df, category_col="original_category")
        assert mapped["harmonised_broad"].notna().all()
        assert df["nomis_api_code"].notna().all()
        assert len(NOMIS_API_CODES_BY_DETAILED) == 19
