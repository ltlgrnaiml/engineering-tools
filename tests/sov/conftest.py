"""SOV test fixtures and configuration."""

from __future__ import annotations

import polars as pl
import pytest


@pytest.fixture
def one_way_known_dataset() -> pl.DataFrame:
    """Dataset with known one-way ANOVA results for verification.
    
    This dataset has 3 groups (A, B, C) with clear between-group differences.
    Known results computed manually:
    - Grand mean = 15.0
    - SS_between ≈ 126
    - SS_within ≈ 18
    - F ≈ 21.0
    - p < 0.01
    """
    return pl.DataFrame({
        "factor_a": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
        "response": [10.0, 12.0, 11.0, 20.0, 22.0, 21.0, 15.0, 17.0, 16.0],
    })


@pytest.fixture
def two_way_known_dataset() -> pl.DataFrame:
    """Dataset with known two-way ANOVA results.
    
    2x3 factorial design with factors A (2 levels) and B (3 levels).
    """
    return pl.DataFrame({
        "factor_a": ["A1", "A1", "A1", "A1", "A1", "A1",
                     "A2", "A2", "A2", "A2", "A2", "A2"],
        "factor_b": ["B1", "B1", "B2", "B2", "B3", "B3",
                     "B1", "B1", "B2", "B2", "B3", "B3"],
        "response": [10.0, 12.0, 15.0, 17.0, 20.0, 22.0,
                     14.0, 16.0, 19.0, 21.0, 24.0, 26.0],
    })


@pytest.fixture
def balanced_dataset() -> pl.DataFrame:
    """Balanced dataset for variance decomposition testing.
    
    Equal sample sizes per group, clear variance structure.
    """
    return pl.DataFrame({
        "group": ["G1"] * 5 + ["G2"] * 5 + ["G3"] * 5,
        "value": [
            100.0, 102.0, 98.0, 101.0, 99.0,  # G1: mean=100, var=2
            110.0, 112.0, 108.0, 111.0, 109.0,  # G2: mean=110, var=2
            105.0, 107.0, 103.0, 106.0, 104.0,  # G3: mean=105, var=2
        ],
    })


@pytest.fixture
def no_effect_dataset() -> pl.DataFrame:
    """Dataset where factor has no significant effect.
    
    All groups have similar means but different within-group variance.
    """
    return pl.DataFrame({
        "factor": ["X", "X", "X", "X", "Y", "Y", "Y", "Y", "Z", "Z", "Z", "Z"],
        "response": [50.0, 51.0, 49.0, 50.0, 50.0, 52.0, 48.0, 50.0, 49.0, 51.0, 50.0, 50.0],
    })
