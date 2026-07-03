"""Mortality parameters from ONS national life tables."""

from __future__ import annotations

import numpy as np

from ukethnicproj import AGE_MAX, AGE_MIN, GENERATIONS, SEXES
from ukethnicproj.calibration.fetch import parse_life_table_qx


def build_survival_array(
    n_nations: int,
    n_ethnic: int,
    n_gen: int,
) -> np.ndarray:
    """
    Build age-sex survival probabilities from ONS National Life Tables 2020-2022.

    A common national schedule is applied to all ethnic groups and generations
    unless group-specific evidence is available (ONS Health Index; Phase 4).
    """
    qx_df = parse_life_table_qx()
    n_sex = len(SEXES)
    n_ages = AGE_MAX - AGE_MIN + 1
    survival = np.zeros((n_nations, n_ethnic, n_gen, n_sex, n_ages))

    for s_idx, sex in enumerate(SEXES):
        subset = qx_df[qx_df["sex"] == sex].set_index("age")["px"]
        px = np.array([float(subset.get(a, subset.iloc[-1])) for a in range(AGE_MIN, AGE_MAX + 1)])
        px = np.clip(px, 0.0, 1.0)
        for n in range(n_nations):
            for e in range(n_ethnic):
                for g in range(n_gen):
                    survival[n, e, g, s_idx, :] = px

    return survival
