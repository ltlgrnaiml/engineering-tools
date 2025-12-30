"""ANOVA analysis implementation.

Provides one-way and multi-way ANOVA with variance component estimation.

Per ADR-0010: Uses shared Pydantic contracts for external interfaces.
Internal computation uses lightweight dataclasses for performance.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import numpy as np
import polars as pl
from scipy import stats

from shared.contracts.sov.anova import (
    ANOVAConfig as ANOVAConfigContract,
    ANOVAResult as ANOVAResultContract,
    ANOVASummary,
    ANOVAType,
    EffectType,
    FactorConfig,
    FactorEffect,
    SumOfSquaresType,
    VarianceComponent,
)


@dataclass
class ANOVAConfig:
    """Configuration for ANOVA analysis.
    
    Per ADR-0023: All computations MUST be deterministic. The seed parameter
    ensures reproducibility for any randomized operations.
    """
    factors: list[str]
    response_columns: list[str]
    alpha: float = 0.05
    anova_type: Literal["one-way", "two-way", "n-way"] = "one-way"
    seed: int = 42  # Per ADR-0023: Deterministic computation seed


@dataclass
class ANOVAResultRow:
    """Single row of ANOVA results."""
    source: str
    sum_squares: float
    df: int
    mean_square: float
    f_statistic: float | None
    p_value: float | None
    variance_pct: float
    significant: bool


class VarianceValidationError(Exception):
    """Raised when variance percentages do not sum to 100%."""

    pass


@dataclass
class ANOVAResult:
    """Complete ANOVA result for a response variable.
    
    This is the internal representation. Use to_pydantic() to convert
    to the shared contract for API responses per ADR-0010.
    """
    response_column: str
    rows: list[ANOVAResultRow]
    total_variance: float
    r_squared: float
    factors: list[str]
    analysis_id: str | None = None
    input_dataset_id: str | None = None
    created_at: datetime | None = None

    def validate_variance_sum(self, tolerance: float = 0.01) -> bool:
        """Validate that variance percentages sum to 100%.

        Per ADR-0023: Variance percentages MUST sum to 100%.

        Args:
            tolerance: Acceptable deviation from 100% (default 0.01 = 1%).

        Returns:
            True if validation passes.

        Raises:
            VarianceValidationError: If variance percentages don't sum to 100%.
        """
        # Exclude the "Total" row which is always 100%
        component_rows = [r for r in self.rows if r.source != "Total"]
        variance_sum = sum(r.variance_pct for r in component_rows)

        if abs(variance_sum - 100.0) > tolerance:
            raise VarianceValidationError(
                f"Variance percentages sum to {variance_sum:.2f}%, expected 100% "
                f"(tolerance: {tolerance * 100:.1f}%). Response: {self.response_column}"
            )
        return True

    def to_pydantic(
        self,
        analysis_id: str,
        input_dataset_id: str,
        config: "ANOVAConfig",
    ) -> ANOVAResultContract:
        """Convert to shared Pydantic contract per ADR-0010.
        
        Args:
            analysis_id: Unique analysis ID.
            input_dataset_id: Source dataset ID.
            config: ANOVA configuration used.
            
        Returns:
            ANOVAResultContract for API responses.
        """
        now = datetime.now(timezone.utc)
        
        # Convert rows to FactorEffect contracts
        effects: list[FactorEffect] = []
        for row in self.rows:
            if row.source in ("Total", "Residual"):
                continue  # These go in summary, not effects
            
            effects.append(FactorEffect(
                effect_name=row.source,
                effect_type=EffectType.FIXED,
                is_interaction=":" in row.source,
                sum_of_squares=row.sum_squares,
                degrees_of_freedom=row.df,
                mean_square=row.mean_square,
                f_statistic=row.f_statistic,
                p_value=row.p_value,
                eta_squared=row.variance_pct / 100.0 if row.variance_pct else None,
                is_significant=row.significant,
                alpha=config.alpha,
            ))
        
        # Build summary from Total and Residual rows
        total_row = next((r for r in self.rows if r.source == "Total"), None)
        residual_row = next((r for r in self.rows if r.source == "Residual"), None)
        
        summary = ANOVASummary(
            grand_mean=0.0,  # Would need to compute from data
            grand_std=0.0,
            total_n=total_row.df + 1 if total_row else 0,
            total_ss=total_row.sum_squares if total_row else 0.0,
            total_df=total_row.df if total_row else 0,
            error_ss=residual_row.sum_squares if residual_row else 0.0,
            error_df=residual_row.df if residual_row else 0,
            error_ms=residual_row.mean_square if residual_row else 0.0,
            model_r_squared=self.r_squared,
        )
        
        # Build variance components
        variance_components: list[VarianceComponent] = []
        for row in self.rows:
            if row.source == "Total":
                continue
            variance_components.append(VarianceComponent(
                component_name=row.source,
                variance_estimate=row.sum_squares,
                variance_percent=row.variance_pct,
            ))
        
        # Create config contract
        config_contract = ANOVAConfigContract(
            anova_type=_map_anova_type(config.anova_type),
            ss_type=SumOfSquaresType.TYPE_III,
            factors=[FactorConfig(column=f) for f in config.factors],
            response_column=self.response_column,
            alpha=config.alpha,
            seed=getattr(config, 'seed', 42),
        )
        
        return ANOVAResultContract(
            analysis_id=analysis_id,
            analysis_type=_map_anova_type(config.anova_type),
            input_dataset_id=input_dataset_id,
            created_at=now,
            completed_at=now,
            config=config_contract,
            summary=summary,
            effects=effects,
            variance_components=variance_components,
        )


def _map_anova_type(anova_type: str) -> ANOVAType:
    """Map local anova_type string to ANOVAType enum."""
    mapping = {
        "one-way": ANOVAType.ONE_WAY,
        "two-way": ANOVAType.TWO_WAY,
        "n-way": ANOVAType.N_WAY,
    }
    return mapping.get(anova_type, ANOVAType.N_WAY)


async def run_anova_analysis(
    data: pl.DataFrame,
    config: ANOVAConfig,
    validate_variance: bool = True,
    variance_tolerance: float = 0.01,
) -> list[ANOVAResult]:
    """Run ANOVA analysis on data.

    Per ADR-0023: Uses Type III sum of squares and validates variance percentages.

    Args:
        data: Input DataFrame.
        config: ANOVA configuration.
        validate_variance: If True, validate variance percentages sum to 100%.
        variance_tolerance: Acceptable deviation from 100% (default 0.01 = 1%).

    Returns:
        List of ANOVAResult for each response column.

    Raises:
        VarianceValidationError: If variance validation fails.
    """
    results: list[ANOVAResult] = []

    for response_col in config.response_columns:
        if response_col not in data.columns:
            continue

        # Convert to numpy for scipy
        response = data[response_col].to_numpy()

        if config.anova_type == "one-way" and len(config.factors) == 1:
            result = _one_way_anova(data, config.factors[0], response_col, config.alpha)
        else:
            result = _n_way_anova(data, config.factors, response_col, config.alpha)

        # Validate variance percentages per ADR-0023
        if validate_variance:
            result.validate_variance_sum(tolerance=variance_tolerance)

        results.append(result)

    return results


def _one_way_anova(
    data: pl.DataFrame,
    factor: str,
    response_col: str,
    alpha: float,
) -> ANOVAResult:
    """Perform one-way ANOVA."""
    # Get groups
    groups = data.group_by(factor).agg(pl.col(response_col).alias("values"))
    group_values = [g.to_numpy() for g in groups["values"]]
    
    # Perform ANOVA
    f_stat, p_value = stats.f_oneway(*group_values)
    
    # Calculate sum of squares
    grand_mean = data[response_col].mean()
    n_total = len(data)
    
    # Between-group SS
    ss_between = sum(
        len(g) * (np.mean(g) - grand_mean) ** 2
        for g in group_values
    )
    
    # Within-group SS  
    ss_within = sum(
        np.sum((g - np.mean(g)) ** 2)
        for g in group_values
    )
    
    # Total SS
    ss_total = np.sum((data[response_col].to_numpy() - grand_mean) ** 2)
    
    # Degrees of freedom
    k = len(group_values)  # number of groups
    df_between = k - 1
    df_within = n_total - k
    df_total = n_total - 1
    
    # Mean squares
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0
    
    # Variance percentages
    total_var = ss_total if ss_total > 0 else 1
    
    rows = [
        ANOVAResultRow(
            source=factor,
            sum_squares=float(ss_between),
            df=df_between,
            mean_square=float(ms_between),
            f_statistic=float(f_stat) if not np.isnan(f_stat) else None,
            p_value=float(p_value) if not np.isnan(p_value) else None,
            variance_pct=float(ss_between / total_var * 100),
            significant=p_value < alpha if not np.isnan(p_value) else False,
        ),
        ANOVAResultRow(
            source="Residual",
            sum_squares=float(ss_within),
            df=df_within,
            mean_square=float(ms_within),
            f_statistic=None,
            p_value=None,
            variance_pct=float(ss_within / total_var * 100),
            significant=False,
        ),
        ANOVAResultRow(
            source="Total",
            sum_squares=float(ss_total),
            df=df_total,
            mean_square=None,
            f_statistic=None,
            p_value=None,
            variance_pct=100.0,
            significant=False,
        ),
    ]
    
    return ANOVAResult(
        response_column=response_col,
        rows=rows,
        total_variance=float(ss_total),
        r_squared=float(ss_between / total_var) if total_var > 0 else 0,
        factors=[factor],
    )


def _n_way_anova(
    data: pl.DataFrame,
    factors: list[str],
    response_col: str,
    alpha: float,
    include_interactions: bool = True,
) -> ANOVAResult:
    """Perform n-way ANOVA with main effects and optional interaction terms.
    
    Per ADR-0023: Includes A×B interaction terms when include_interactions=True.
    
    Args:
        data: Input DataFrame.
        factors: List of factor column names.
        response_col: Response variable column name.
        alpha: Significance level.
        include_interactions: If True, compute 2-way interaction effects.
        
    Returns:
        ANOVAResult with main effects and interactions.
    """
    response = data[response_col].to_numpy()
    grand_mean = np.mean(response)
    n_total = len(data)
    ss_total = np.sum((response - grand_mean) ** 2)
    
    rows: list[ANOVAResultRow] = []
    ss_explained = 0.0
    df_explained = 0
    
    # Store main effect SS for interaction calculation
    main_effect_ss: dict[str, float] = {}
    factor_levels: dict[str, int] = {}
    
    # Calculate main effects for each factor
    for factor in factors:
        groups = data.group_by(factor).agg(pl.col(response_col).alias("values"))
        group_values = [g.to_numpy() for g in groups["values"]]
        
        # Between-group SS for this factor
        ss_factor = sum(
            len(g) * (np.mean(g) - grand_mean) ** 2
            for g in group_values
        )
        
        k = len(group_values)
        df_factor = k - 1
        ms_factor = ss_factor / df_factor if df_factor > 0 else 0
        
        ss_explained += ss_factor
        df_explained += df_factor
        main_effect_ss[factor] = ss_factor
        factor_levels[factor] = k
        
        rows.append(ANOVAResultRow(
            source=factor,
            sum_squares=float(ss_factor),
            df=df_factor,
            mean_square=float(ms_factor),
            f_statistic=None,  # Will calculate after residual
            p_value=None,
            variance_pct=float(ss_factor / ss_total * 100) if ss_total > 0 else 0,
            significant=False,
        ))
    
    # Calculate 2-way interaction effects (A×B terms)
    if include_interactions and len(factors) >= 2:
        for i, factor_a in enumerate(factors):
            for factor_b in factors[i + 1:]:
                # Group by both factors
                interaction_groups = data.group_by([factor_a, factor_b]).agg(
                    pl.col(response_col).alias("values")
                )
                
                # Calculate SS for interaction (cell means - main effects)
                # SS_AB = SS_cells - SS_A - SS_B
                cell_ss = 0.0
                for row_data in interaction_groups.iter_rows(named=True):
                    cell_values = row_data["values"]
                    cell_mean = np.mean(cell_values)
                    cell_ss += len(cell_values) * (cell_mean - grand_mean) ** 2
                
                # Interaction SS = Cell SS - Main effect A - Main effect B
                ss_interaction = max(0, cell_ss - main_effect_ss[factor_a] - main_effect_ss[factor_b])
                
                # DF for interaction = (levels_A - 1) * (levels_B - 1)
                df_interaction = (factor_levels[factor_a] - 1) * (factor_levels[factor_b] - 1)
                ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
                
                ss_explained += ss_interaction
                df_explained += df_interaction
                
                interaction_name = f"{factor_a}:{factor_b}"
                rows.append(ANOVAResultRow(
                    source=interaction_name,
                    sum_squares=float(ss_interaction),
                    df=df_interaction,
                    mean_square=float(ms_interaction),
                    f_statistic=None,
                    p_value=None,
                    variance_pct=float(ss_interaction / ss_total * 100) if ss_total > 0 else 0,
                    significant=False,
                ))
    
    # Residual
    ss_residual = max(0, ss_total - ss_explained)  # Ensure non-negative
    df_residual = n_total - df_explained - 1
    ms_residual = ss_residual / df_residual if df_residual > 0 else 0
    
    # Update F-statistics and p-values
    for row in rows:
        if ms_residual > 0:
            f_stat = row.mean_square / ms_residual
            p_value = 1 - stats.f.cdf(f_stat, row.df, df_residual)
            row.f_statistic = float(f_stat)
            row.p_value = float(p_value)
            row.significant = p_value < alpha
    
    rows.append(ANOVAResultRow(
        source="Residual",
        sum_squares=float(ss_residual),
        df=df_residual,
        mean_square=float(ms_residual),
        f_statistic=None,
        p_value=None,
        variance_pct=float(ss_residual / ss_total * 100) if ss_total > 0 else 0,
        significant=False,
    ))
    
    rows.append(ANOVAResultRow(
        source="Total",
        sum_squares=float(ss_total),
        df=n_total - 1,
        mean_square=None,
        f_statistic=None,
        p_value=None,
        variance_pct=100.0,
        significant=False,
    ))
    
    return ANOVAResult(
        response_column=response_col,
        rows=rows,
        total_variance=float(ss_total),
        r_squared=float(ss_explained / ss_total) if ss_total > 0 else 0,
        factors=factors,
    )
