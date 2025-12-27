"""ANOVA analysis implementation.

Provides one-way and multi-way ANOVA with variance component estimation.
"""
from dataclasses import dataclass
from typing import Literal

import numpy as np
import polars as pl
from scipy import stats


@dataclass
class ANOVAConfig:
    """Configuration for ANOVA analysis."""
    factors: list[str]
    response_columns: list[str]
    alpha: float = 0.05
    anova_type: Literal["one-way", "two-way", "n-way"] = "one-way"


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


@dataclass
class ANOVAResult:
    """Complete ANOVA result for a response variable."""
    response_column: str
    rows: list[ANOVAResultRow]
    total_variance: float
    r_squared: float
    factors: list[str]


async def run_anova_analysis(
    data: pl.DataFrame,
    config: ANOVAConfig,
) -> list[ANOVAResult]:
    """Run ANOVA analysis on data.
    
    Args:
        data: Input DataFrame
        config: ANOVA configuration
        
    Returns:
        List of ANOVAResult for each response column
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
) -> ANOVAResult:
    """Perform n-way ANOVA (simplified - main effects only)."""
    response = data[response_col].to_numpy()
    grand_mean = np.mean(response)
    n_total = len(data)
    ss_total = np.sum((response - grand_mean) ** 2)
    
    rows: list[ANOVAResultRow] = []
    ss_explained = 0.0
    df_explained = 0
    
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
    
    # Residual
    ss_residual = ss_total - ss_explained
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
