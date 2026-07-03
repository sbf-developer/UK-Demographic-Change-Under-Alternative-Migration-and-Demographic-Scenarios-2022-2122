"""Tests for empirical parameter calibration."""

from __future__ import annotations

import numpy as np
import pytest

from ukethnicproj.calibration.fetch import fetch_life_tables, parse_births_by_mother_age, parse_life_table_qx
from ukethnicproj.calibration.fertility import compute_ethnic_fertility_scalars, compute_national_asfr
from ukethnicproj.calibration.migration import migration_volumes
from ukethnicproj.calibration.mortality import build_survival_array
from ukethnicproj.calibration.parameters import build_empirical_parameters
from ukethnicproj.projection.scenarios import ScenarioConfig, load_initial_state


@pytest.fixture(scope="module")
def ensure_calibration_data() -> None:
    fetch_life_tables()


class TestCalibration:
    def test_life_table_qx_valid(self, ensure_calibration_data: None) -> None:
        qx = parse_life_table_qx()
        assert len(qx) >= 180
        assert qx["qx"].between(0, 1).all()
        assert qx["px"].between(0, 1).all()

    def test_national_asfr_tfr(self) -> None:
        asfr = compute_national_asfr(("england", "wales"), year=2022)
        tfr = asfr[15:50].sum()
        assert 1.2 < tfr < 1.8

    def test_ethnic_fertility_scalars(self) -> None:
        scalars = compute_ethnic_fertility_scalars(("england", "wales"))
        assert set(scalars) == {"white", "mixed", "asian", "black", "other"}
        assert all(v > 0 for v in scalars.values())

    def test_migration_volumes_principal(self) -> None:
        imm, emig = migration_volumes("principal", ("england", "wales"))
        net = imm - emig
        assert 250_000 < net < 350_000
        assert imm > emig

    def test_survival_array_shape(self) -> None:
        surv = build_survival_array(2, 5, 5)
        assert surv.shape == (2, 5, 5, 2, 101)
        assert np.all(surv >= 0) and np.all(surv <= 1)

    def test_empirical_parameters_build(self) -> None:
        config = ScenarioConfig(
            name="test_empirical",
            description="test",
            nations=["england", "wales"],
            placeholder=False,
            use_census_base=True,
            migration_variant="principal",
            fertility_variant="principal",
        )
        state = load_initial_state(config)
        params = build_empirical_parameters(config, state)
        assert params.survival.sum() > 0
        assert params.fertility_asfr[:, :, :, 15:50].sum() > 1.0
        assert params.immigration.sum() > 0
        assert params.emigration.sum() > 0

    def test_births_2022_total(self) -> None:
        births = parse_births_by_mother_age(year=2022)
        assert abs(births["births"].sum() - 605_342) < 5000
