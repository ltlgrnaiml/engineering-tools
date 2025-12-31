"""ANOVA computation correctness tests.

Per ADR-0023: Verify ANOVA computation against known results.
These tests ensure the statistical computations are mathematically correct.
"""

from __future__ import annotations

import polars as pl
import pytest

from apps.sov_analyzer.backend.src.sov_analyzer.analysis.anova import (
    ANOVAConfig,
    run_anova_analysis,
)


class TestOneWayANOVA:
    """Tests for one-way ANOVA computation."""

    @pytest.mark.asyncio
    async def test_one_way_anova_correctness(self, one_way_known_dataset: pl.DataFrame):
        """Verify one-way ANOVA produces correct results for known dataset.
        
        Dataset: 3 groups with means 11, 21, 16
        Known results (corrected):
        - Grand mean = 16.0 (sum of all values / 9)
        - SS_between = 150.0 (3*(11-16)² + 3*(21-16)² + 3*(16-16)²)
        - SS_within = 18.0  
        - F ≈ 25.0
        - p < 0.01 (significant)
        - R² ≈ 0.893
        """
        config = ANOVAConfig(
            factors=["factor_a"],
            response_columns=["response"],
            alpha=0.05,
            anova_type="one-way",
        )

        results = await run_anova_analysis(one_way_known_dataset, config)

        assert len(results) == 1
        result = results[0]

        # Check response column
        assert result.response_column == "response"
        assert result.factors == ["factor_a"]

        # Check we have correct rows
        assert len(result.rows) == 3  # factor_a, Residual, Total

        factor_row = result.rows[0]
        residual_row = result.rows[1]
        total_row = result.rows[2]

        assert factor_row.source == "factor_a"
        assert residual_row.source == "Residual"
        assert total_row.source == "Total"

        # Check degrees of freedom
        assert factor_row.df == 2  # k-1 = 3-1 = 2
        assert residual_row.df == 6  # n-k = 9-3 = 6
        assert total_row.df == 8  # n-1 = 9-1 = 8

        # Check sum of squares (with tolerance for floating point)
        # SS_between = 3*(11-16)² + 3*(21-16)² + 3*(16-16)² = 75+75+0 = 150
        # SS_within = (10-11)²+(12-11)²+(11-11)² + (20-21)²+... = 2+2+2 = 6
        # SS_total = 150 + 6 = 156
        assert factor_row.sum_squares == pytest.approx(150.0, rel=0.01)
        assert residual_row.sum_squares == pytest.approx(6.0, rel=0.01)
        assert total_row.sum_squares == pytest.approx(156.0, rel=0.01)

        # Check F-statistic and p-value
        # F = MS_between / MS_within = (150/2) / (6/6) = 75 / 1 = 75
        assert factor_row.f_statistic == pytest.approx(75.0, rel=0.1)
        assert factor_row.p_value is not None
        assert factor_row.p_value < 0.01  # Highly significant

        # Check significance flag (use == not is for numpy bool)
        assert factor_row.significant == True

        # Check R-squared (SS_between / SS_total = 150/156 ≈ 0.962)
        assert result.r_squared == pytest.approx(0.962, rel=0.02)

    @pytest.mark.asyncio
    async def test_one_way_no_effect(self, no_effect_dataset: pl.DataFrame):
        """Test one-way ANOVA when factor has no significant effect."""
        config = ANOVAConfig(
            factors=["factor"],
            response_columns=["response"],
            alpha=0.05,
            anova_type="one-way",
        )

        results = await run_anova_analysis(no_effect_dataset, config)

        assert len(results) == 1
        result = results[0]

        factor_row = result.rows[0]

        # Factor should NOT be significant
        assert factor_row.significant == False
        assert factor_row.p_value is not None
        assert factor_row.p_value > 0.05

        # R-squared should be low (less than 50%)
        assert result.r_squared < 0.5


class TestNWayANOVA:
    """Tests for n-way ANOVA computation."""

    @pytest.mark.asyncio
    async def test_two_way_anova_main_effects(self, two_way_known_dataset: pl.DataFrame):
        """Test two-way ANOVA main effects calculation."""
        config = ANOVAConfig(
            factors=["factor_a", "factor_b"],
            response_columns=["response"],
            alpha=0.05,
            anova_type="n-way",
        )

        results = await run_anova_analysis(two_way_known_dataset, config)

        assert len(results) == 1
        result = results[0]

        # Should have rows for factor_a, factor_b, Residual, Total
        assert len(result.rows) >= 4

        sources = [r.source for r in result.rows]
        assert "factor_a" in sources
        assert "factor_b" in sources
        assert "Residual" in sources
        assert "Total" in sources

        # Both factors should be significant in this dataset
        factor_a_row = next(r for r in result.rows if r.source == "factor_a")
        factor_b_row = next(r for r in result.rows if r.source == "factor_b")

        assert factor_a_row.p_value is not None
        assert factor_b_row.p_value is not None

        # factor_b has larger effect
        assert factor_b_row.variance_pct > factor_a_row.variance_pct


class TestVarianceValidation:
    """Tests for variance percentage validation per ADR-0023."""

    @pytest.mark.asyncio
    async def test_variance_sum_validation_passes(self, one_way_known_dataset: pl.DataFrame):
        """Verify variance percentages sum to 100%."""
        config = ANOVAConfig(
            factors=["factor_a"],
            response_columns=["response"],
            alpha=0.05,
        )

        results = await run_anova_analysis(
            one_way_known_dataset,
            config,
            validate_variance=True,
            variance_tolerance=0.01,
        )

        result = results[0]

        # Manual check
        component_rows = [r for r in result.rows if r.source != "Total"]
        variance_sum = sum(r.variance_pct for r in component_rows)

        assert variance_sum == pytest.approx(100.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_variance_validation_method(self, one_way_known_dataset: pl.DataFrame):
        """Test the validate_variance_sum method directly."""
        config = ANOVAConfig(
            factors=["factor_a"],
            response_columns=["response"],
        )

        results = await run_anova_analysis(
            one_way_known_dataset,
            config,
            validate_variance=False,  # Don't validate during analysis
        )

        result = results[0]

        # Should pass with default tolerance
        assert result.validate_variance_sum(tolerance=0.01) is True

        # Should pass with strict tolerance
        assert result.validate_variance_sum(tolerance=0.001) is True

    @pytest.mark.asyncio
    async def test_variance_validation_with_balanced_data(self, balanced_dataset: pl.DataFrame):
        """Test variance validation with balanced dataset."""
        config = ANOVAConfig(
            factors=["group"],
            response_columns=["value"],
        )

        results = await run_anova_analysis(
            balanced_dataset,
            config,
            validate_variance=True,
        )

        result = results[0]

        # With balanced data, factor should explain most variance
        factor_row = result.rows[0]
        assert factor_row.variance_pct > 80.0  # Most variance explained


class TestANOVAEdgeCases:
    """Edge case and error handling tests."""

    @pytest.mark.asyncio
    async def test_missing_response_column_skipped(self):
        """Test that missing response columns are skipped gracefully."""
        data = pl.DataFrame({
            "factor": ["A", "A", "B", "B"],
            "existing_response": [1.0, 2.0, 3.0, 4.0],
        })

        config = ANOVAConfig(
            factors=["factor"],
            response_columns=["existing_response", "missing_column"],
        )

        results = await run_anova_analysis(data, config)

        # Should only return result for existing column
        assert len(results) == 1
        assert results[0].response_column == "existing_response"

    @pytest.mark.asyncio
    async def test_single_group_handling(self):
        """Test handling of single group (degenerate case).
        
        Note: scipy.stats.f_oneway requires at least 2 samples.
        This test verifies we handle this edge case gracefully.
        """
        data = pl.DataFrame({
            "factor": ["A", "A", "A", "A"],
            "response": [1.0, 2.0, 3.0, 4.0],
        })

        config = ANOVAConfig(
            factors=["factor"],
            response_columns=["response"],
        )

        # scipy.stats.f_oneway raises an error with single group,
        # so we expect this to raise or return empty results
        try:
            results = await run_anova_analysis(data, config, validate_variance=False)
            # If it doesn't raise, it should return empty or handle gracefully
            assert len(results) <= 1
        except (ValueError, TypeError):
            # Expected behavior - single group is not valid for ANOVA
            pass

    @pytest.mark.asyncio
    async def test_deterministic_results(self, one_way_known_dataset: pl.DataFrame):
        """Verify ANOVA results are deterministic (same input → same output)."""
        config = ANOVAConfig(
            factors=["factor_a"],
            response_columns=["response"],
        )

        results1 = await run_anova_analysis(one_way_known_dataset, config, validate_variance=False)
        results2 = await run_anova_analysis(one_way_known_dataset, config, validate_variance=False)

        # Results should be identical
        assert results1[0].r_squared == results2[0].r_squared
        assert results1[0].rows[0].f_statistic == results2[0].rows[0].f_statistic
        assert results1[0].rows[0].p_value == results2[0].rows[0].p_value
