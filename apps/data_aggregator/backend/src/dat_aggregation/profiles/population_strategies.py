"""Population and sampling strategies for data filtering.

Per DESIGN §3: Supports various population strategies including
all, valid_only, outliers_excluded, and sample.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


@dataclass
class PopulationStrategy:
    """Base population strategy configuration."""
    name: str
    description: str = ""


@dataclass
class ValidOnlyStrategy(PopulationStrategy):
    """Exclude records with validation errors."""
    exclude_rules: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class OutliersExcludedStrategy(PopulationStrategy):
    """Exclude statistical outliers."""
    method: str = "iqr"  # iqr, zscore, percentile
    threshold: float = 1.5
    apply_to: list[str] = field(default_factory=list)


@dataclass
class SampleStrategy(PopulationStrategy):
    """Random sampling strategy."""
    method: str = "random"  # random, first_n, stratified
    size: int = 1000
    seed: int | None = 42


class PopulationFilter:
    """Applies population strategies to DataFrames per DESIGN §3."""
    
    def apply_strategy(
        self,
        df: pl.DataFrame,
        strategy_name: str,
        strategy_config: dict[str, Any],
    ) -> pl.DataFrame:
        """Apply a population strategy to DataFrame.
        
        Args:
            df: DataFrame to filter
            strategy_name: Name of strategy to apply
            strategy_config: Strategy configuration
            
        Returns:
            Filtered DataFrame
        """
        if df.is_empty():
            return df
        
        if strategy_name == "all":
            return df
        elif strategy_name == "valid_only":
            return self._apply_valid_only(df, strategy_config)
        elif strategy_name == "outliers_excluded":
            return self._apply_outliers_excluded(df, strategy_config)
        elif strategy_name == "sample":
            return self._apply_sample(df, strategy_config)
        else:
            logger.warning(f"Unknown population strategy: {strategy_name}")
            return df
    
    def _apply_valid_only(
        self,
        df: pl.DataFrame,
        config: dict[str, Any],
    ) -> pl.DataFrame:
        """Apply valid_only strategy - exclude records matching exclude rules.
        
        Args:
            df: DataFrame to filter
            config: Strategy configuration with exclude_rules
            
        Returns:
            Filtered DataFrame with invalid records excluded
        """
        exclude_rules = config.get("exclude_rules", [])
        
        for rule in exclude_rules:
            col = rule.get("column")
            if not col or col not in df.columns:
                continue
            
            condition = rule.get("condition", "equals")
            value = rule.get("value")
            
            if condition == "equals":
                df = df.filter(pl.col(col) != value)
            elif condition == "not_equals":
                df = df.filter(pl.col(col) == value)
            elif condition == "is_null":
                df = df.filter(pl.col(col).is_not_null())
            elif condition == "contains":
                df = df.filter(~pl.col(col).cast(pl.Utf8).str.contains(str(value)))
        
        return df
    
    def _apply_outliers_excluded(
        self,
        df: pl.DataFrame,
        config: dict[str, Any],
    ) -> pl.DataFrame:
        """Apply outliers_excluded strategy - remove statistical outliers.
        
        Args:
            df: DataFrame to filter
            config: Strategy configuration with method, threshold, apply_to
            
        Returns:
            DataFrame with outliers removed
        """
        method = config.get("method", "iqr")
        threshold = config.get("threshold", 1.5)
        apply_to = config.get("apply_to", [])
        
        if not apply_to:
            # Apply to all numeric columns
            apply_to = [
                col for col in df.columns
                if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]
            ]
        
        for col in apply_to:
            if col not in df.columns:
                continue
            
            if method == "iqr":
                df = self._exclude_iqr_outliers(df, col, threshold)
            elif method == "zscore":
                df = self._exclude_zscore_outliers(df, col, threshold)
            elif method == "percentile":
                df = self._exclude_percentile_outliers(df, col, threshold)
        
        return df
    
    def _exclude_iqr_outliers(
        self,
        df: pl.DataFrame,
        col: str,
        threshold: float,
    ) -> pl.DataFrame:
        """Exclude outliers using IQR method."""
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        
        if q1 is None or q3 is None:
            return df
        
        iqr = q3 - q1
        lower_bound = q1 - (threshold * iqr)
        upper_bound = q3 + (threshold * iqr)
        
        return df.filter(
            (pl.col(col) >= lower_bound) & (pl.col(col) <= upper_bound)
        )
    
    def _exclude_zscore_outliers(
        self,
        df: pl.DataFrame,
        col: str,
        threshold: float,
    ) -> pl.DataFrame:
        """Exclude outliers using Z-score method."""
        mean = df[col].mean()
        std = df[col].std()
        
        if mean is None or std is None or std == 0:
            return df
        
        # Keep rows where |z-score| <= threshold
        return df.filter(
            ((pl.col(col) - mean) / std).abs() <= threshold
        )
    
    def _exclude_percentile_outliers(
        self,
        df: pl.DataFrame,
        col: str,
        threshold: float,
    ) -> pl.DataFrame:
        """Exclude outliers using percentile method."""
        # threshold is interpreted as percentile cutoff (e.g., 5 = exclude top/bottom 5%)
        lower_pct = threshold / 100
        upper_pct = 1 - lower_pct
        
        lower_bound = df[col].quantile(lower_pct)
        upper_bound = df[col].quantile(upper_pct)
        
        if lower_bound is None or upper_bound is None:
            return df
        
        return df.filter(
            (pl.col(col) >= lower_bound) & (pl.col(col) <= upper_bound)
        )
    
    def _apply_sample(
        self,
        df: pl.DataFrame,
        config: dict[str, Any],
    ) -> pl.DataFrame:
        """Apply sample strategy - random sampling.
        
        Args:
            df: DataFrame to sample
            config: Strategy configuration with method, size, seed
            
        Returns:
            Sampled DataFrame
        """
        method = config.get("method", "random")
        size = config.get("size", 1000)
        seed = config.get("seed", 42)
        
        if len(df) <= size:
            return df
        
        if method == "random":
            return df.sample(n=size, seed=seed)
        elif method == "first_n":
            return df.head(size)
        elif method == "stratified":
            # For stratified, we need a stratify column
            stratify_col = config.get("stratify_by")
            if stratify_col and stratify_col in df.columns:
                return self._stratified_sample(df, stratify_col, size, seed)
            else:
                return df.sample(n=size, seed=seed)
        else:
            return df.sample(n=size, seed=seed)
    
    def _stratified_sample(
        self,
        df: pl.DataFrame,
        stratify_col: str,
        size: int,
        seed: int,
    ) -> pl.DataFrame:
        """Perform stratified sampling."""
        # Calculate proportional sample size per stratum
        value_counts = df[stratify_col].value_counts()
        total = len(df)
        
        samples = []
        for row in value_counts.iter_rows():
            value, count = row[0], row[1]
            stratum_size = max(1, int((count / total) * size))
            stratum_df = df.filter(pl.col(stratify_col) == value)
            if len(stratum_df) > stratum_size:
                stratum_df = stratum_df.sample(n=stratum_size, seed=seed)
            samples.append(stratum_df)
        
        if samples:
            return pl.concat(samples)
        return df


def apply_population_strategy(
    df: pl.DataFrame,
    strategy_name: str,
    strategy_config: dict[str, Any] | None = None,
) -> pl.DataFrame:
    """Convenience function for applying population strategy.
    
    Args:
        df: DataFrame to filter
        strategy_name: Name of strategy
        strategy_config: Optional strategy configuration
        
    Returns:
        Filtered DataFrame
    """
    filter_instance = PopulationFilter()
    return filter_instance.apply_strategy(df, strategy_name, strategy_config or {})
