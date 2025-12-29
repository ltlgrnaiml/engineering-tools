"""OutputBuilder - Aggregation and join outputs.

Per ADR-0011: Profiles define how extracted tables are combined
into final outputs, including aggregations and joins.
"""

import logging
from typing import Any

import polars as pl

from .profile_loader import (
    DATProfile,
    OutputConfig,
    AggregationConfig,
    JoinOutputConfig,
)

logger = logging.getLogger(__name__)


class OutputBuilder:
    """Builds final outputs from extracted tables per profile config.
    
    Per ADR-0011: Combines extracted tables according to profile
    output definitions, applies aggregations and joins.
    """
    
    def build_outputs(
        self,
        extracted_tables: dict[str, pl.DataFrame],
        profile: DATProfile,
        selected_outputs: list[str] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Build final output DataFrames.
        
        Per DESIGN §8: Processes default/optional outputs, aggregations, and joins.
        
        Args:
            extracted_tables: Dict of table_id to DataFrame
            profile: DATProfile with output definitions
            selected_outputs: Optional filter for specific outputs
            
        Returns:
            Dict of output_id to combined DataFrame
        """
        outputs: dict[str, pl.DataFrame] = {}
        
        # Process default outputs
        for output_config in profile.default_outputs:
            if selected_outputs and output_config.id not in selected_outputs:
                continue
            
            df = self._build_output(output_config, extracted_tables)
            if not df.is_empty():
                outputs[output_config.id] = df
        
        # Process optional outputs
        for output_config in profile.optional_outputs:
            if selected_outputs and output_config.id not in selected_outputs:
                continue
            
            df = self._build_output(output_config, extracted_tables)
            if not df.is_empty():
                outputs[output_config.id] = df
        
        # Per DESIGN §8: Process aggregation outputs
        for agg_config in profile.aggregations:
            if selected_outputs and agg_config.id not in selected_outputs:
                continue
            
            df = self._build_aggregation(agg_config, extracted_tables)
            if not df.is_empty():
                output_id = agg_config.output_table or agg_config.id
                outputs[output_id] = df
        
        # Per DESIGN §8: Process join outputs
        for join_config in profile.joins:
            if selected_outputs and join_config.id not in selected_outputs:
                continue
            
            df = self._build_join(join_config, extracted_tables)
            if not df.is_empty():
                outputs[join_config.id] = df
        
        return outputs
    
    def _build_aggregation(
        self,
        config: AggregationConfig,
        tables: dict[str, pl.DataFrame],
    ) -> pl.DataFrame:
        """Build aggregation output per DESIGN §8.
        
        Args:
            config: Aggregation configuration
            tables: Extracted tables
            
        Returns:
            Aggregated DataFrame
        """
        if config.from_table not in tables:
            logger.warning(f"Table {config.from_table} not found for aggregation")
            return pl.DataFrame()
        
        df = tables[config.from_table]
        return self.apply_aggregation(df, config.group_by, config.aggregations)
    
    def _build_join(
        self,
        config: JoinOutputConfig,
        tables: dict[str, pl.DataFrame],
    ) -> pl.DataFrame:
        """Build join output per DESIGN §8.
        
        Args:
            config: Join configuration
            tables: Extracted tables
            
        Returns:
            Joined DataFrame
        """
        if config.left_table not in tables:
            logger.warning(f"Left table {config.left_table} not found for join")
            return pl.DataFrame()
        
        if config.right_table not in tables:
            logger.warning(f"Right table {config.right_table} not found for join")
            return tables[config.left_table]
        
        return self.apply_join(
            tables[config.left_table],
            tables[config.right_table],
            config.on,
            config.how,
        )
    
    def _build_output(
        self,
        config: OutputConfig,
        tables: dict[str, pl.DataFrame],
    ) -> pl.DataFrame:
        """Build single output by combining specified tables.
        
        Args:
            config: Output configuration
            tables: Extracted tables
            
        Returns:
            Combined DataFrame
        """
        dfs: list[pl.DataFrame] = []
        
        for table_id in config.from_tables:
            if table_id in tables:
                dfs.append(tables[table_id])
            else:
                logger.debug(f"Table {table_id} not found for output {config.id}")
        
        if not dfs:
            return pl.DataFrame()
        
        # Concatenate tables diagonally (union of columns)
        return pl.concat(dfs, how="diagonal")
    
    def apply_aggregation(
        self,
        df: pl.DataFrame,
        group_by: list[str],
        aggregations: dict[str, str],
    ) -> pl.DataFrame:
        """Apply aggregation to DataFrame.
        
        Args:
            df: DataFrame to aggregate
            group_by: Columns to group by
            aggregations: Dict of column -> agg_function
            
        Returns:
            Aggregated DataFrame
        """
        if df.is_empty():
            return df
        
        # Validate columns exist
        valid_group_by = [c for c in group_by if c in df.columns]
        if not valid_group_by:
            logger.warning("No valid group_by columns found")
            return df
        
        # Build aggregation expressions
        agg_exprs = []
        for col, func in aggregations.items():
            if col not in df.columns:
                continue
            
            expr = self._get_agg_expr(col, func)
            if expr is not None:
                agg_exprs.append(expr)
        
        if not agg_exprs:
            logger.warning("No valid aggregations found")
            return df
        
        return df.group_by(valid_group_by).agg(agg_exprs)
    
    def apply_join(
        self,
        left_df: pl.DataFrame,
        right_df: pl.DataFrame,
        on: list[str],
        how: str = "left",
    ) -> pl.DataFrame:
        """Apply join between two DataFrames.
        
        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            on: Join columns
            how: Join type (left, right, inner, outer)
            
        Returns:
            Joined DataFrame
        """
        if left_df.is_empty():
            return left_df
        
        if right_df.is_empty():
            return left_df
        
        # Validate join columns
        valid_on = [c for c in on if c in left_df.columns and c in right_df.columns]
        if not valid_on:
            logger.warning("No valid join columns found")
            return left_df
        
        return left_df.join(right_df, on=valid_on, how=how)  # type: ignore
    
    def _get_agg_expr(self, col: str, func: str) -> pl.Expr | None:
        """Get polars aggregation expression."""
        func_lower = func.lower()
        
        if func_lower == "mean":
            return pl.col(col).mean().alias(f"{col}_mean")
        elif func_lower == "sum":
            return pl.col(col).sum().alias(f"{col}_sum")
        elif func_lower == "min":
            return pl.col(col).min().alias(f"{col}_min")
        elif func_lower == "max":
            return pl.col(col).max().alias(f"{col}_max")
        elif func_lower == "count":
            return pl.col(col).count().alias(f"{col}_count")
        elif func_lower == "std":
            return pl.col(col).std().alias(f"{col}_std")
        elif func_lower == "first":
            return pl.col(col).first().alias(col)
        elif func_lower == "last":
            return pl.col(col).last().alias(col)
        else:
            logger.warning(f"Unknown aggregation function: {func}")
            return None
    
    def combine_all_tables(
        self,
        extracted_tables: dict[str, pl.DataFrame],
        context: dict[str, Any] | None = None,
    ) -> pl.DataFrame:
        """Combine all extracted tables into single DataFrame.
        
        Args:
            extracted_tables: Dict of table_id to DataFrame
            context: Optional context to add as columns
            
        Returns:
            Combined DataFrame with table_id column
        """
        if not extracted_tables:
            return pl.DataFrame()
        
        dfs: list[pl.DataFrame] = []
        
        for table_id, df in extracted_tables.items():
            if df.is_empty():
                continue
            
            # Add table_id column
            df = df.with_columns(pl.lit(table_id).alias("__table_id__"))
            
            # Add context columns if provided
            if context:
                for key, value in context.items():
                    if key not in df.columns:
                        df = df.with_columns(pl.lit(value).alias(key))
            
            dfs.append(df)
        
        if not dfs:
            return pl.DataFrame()
        
        return pl.concat(dfs, how="diagonal")
    
    def generate_output_filename(
        self,
        profile: DATProfile,
        context: dict[str, Any],
        output_id: str = "",
    ) -> str:
        """Generate output filename using profile template per DESIGN §8.
        
        Args:
            profile: DATProfile with file_naming configuration
            context: Context dict with values to substitute
            output_id: Optional output identifier
            
        Returns:
            Generated filename (without extension)
        """
        import re
        from datetime import datetime
        
        template = getattr(profile, 'file_naming_template', '{profile_id}_{timestamp}')
        timestamp_format = getattr(profile, 'file_naming_timestamp_format', '%Y%m%d_%H%M%S')
        sanitize = getattr(profile, 'file_naming_sanitize', True)
        
        # Build substitution dict
        subs = {
            'profile_id': profile.profile_id,
            'profile_title': profile.title,
            'timestamp': datetime.now().strftime(timestamp_format),
            'output_id': output_id,
            **context,
        }
        
        # Substitute template variables
        filename = template
        for key, value in subs.items():
            filename = filename.replace(f'{{{key}}}', str(value) if value else '')
        
        # Sanitize filename if requested
        if sanitize:
            # Remove invalid characters
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            # Remove multiple underscores
            filename = re.sub(r'_+', '_', filename)
            # Strip leading/trailing underscores
            filename = filename.strip('_')
        
        return filename


def build_outputs(
    extracted_tables: dict[str, pl.DataFrame],
    profile: DATProfile,
    selected_outputs: list[str] | None = None,
) -> dict[str, pl.DataFrame]:
    """Convenience function for building outputs.
    
    Args:
        extracted_tables: Dict of table_id to DataFrame
        profile: DATProfile with output definitions
        selected_outputs: Optional filter
        
    Returns:
        Dict of output_id to DataFrame
    """
    builder = OutputBuilder()
    return builder.build_outputs(extracted_tables, profile, selected_outputs)
