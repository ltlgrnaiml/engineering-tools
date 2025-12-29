"""TransformPipeline - Normalization and column transformations.

Per ADR-0011: Profiles define normalization rules and transforms.
Applies NaN handling, type coercion, renames, and calculated columns.
"""

import logging
from dataclasses import dataclass
from typing import Any

import polars as pl

from .profile_loader import DATProfile

logger = logging.getLogger(__name__)


@dataclass
class ColumnTransform:
    """Column transformation definition."""
    source: str
    target: str
    transform: str
    args: dict[str, Any] | None = None


# Default unit mappings per DESIGN §6
DEFAULT_UNIT_MAPPINGS: dict[str, dict[str, Any]] = {
    "nm": {"canonical": "nm", "factor": 1},
    "um": {"canonical": "nm", "factor": 1000},
    "μm": {"canonical": "nm", "factor": 1000},
    "mm": {"canonical": "nm", "factor": 1_000_000},
    "m": {"canonical": "nm", "factor": 1_000_000_000},
    "angstrom": {"canonical": "nm", "factor": 0.1},
    "Å": {"canonical": "nm", "factor": 0.1},
}


class TransformPipeline:
    """Applies normalization and column transformations.
    
    Per ADR-0011: Profiles define how data is normalized and transformed
    after extraction and before output.
    """
    
    def __init__(
        self,
        unit_mappings: dict[str, dict[str, Any]] | None = None,
    ):
        """Initialize TransformPipeline.
        
        Args:
            unit_mappings: Custom unit mappings (merged with defaults)
        """
        self.unit_mappings = {**DEFAULT_UNIT_MAPPINGS}
        if unit_mappings:
            self.unit_mappings.update(unit_mappings)
    
    def apply_normalization(
        self,
        df: pl.DataFrame,
        profile: DATProfile,
    ) -> pl.DataFrame:
        """Apply normalization rules from profile.
        
        Args:
            df: DataFrame to normalize
            profile: Profile with normalization rules
            
        Returns:
            Normalized DataFrame
        """
        if df.is_empty():
            return df
        
        # 1. Replace NaN values with null
        if profile.nan_values:
            df = self._replace_nan_values(df, profile.nan_values)
        
        # 2. Numeric coercion
        if profile.numeric_coercion:
            df = self._coerce_numeric(df)
        
        # 3. Apply row filters if defined at profile level
        if profile.row_filters:
            df = self.apply_row_filters(df, profile.row_filters)
        
        # 4. Per DESIGN §6: Apply unit normalization based on units_policy
        if profile.units_policy and profile.units_policy != "preserve":
            df = self.normalize_units_by_policy(df, profile.units_policy)
        
        return df
    
    def apply_unit_normalization(
        self,
        df: pl.DataFrame,
        column: str,
        from_unit: str,
        to_unit: str | None = None,
    ) -> pl.DataFrame:
        """Normalize column units per DESIGN §6.
        
        Args:
            df: DataFrame with column to normalize
            column: Column name to normalize
            from_unit: Source unit (e.g., "um", "μm")
            to_unit: Target unit (default: canonical unit from mapping)
            
        Returns:
            DataFrame with normalized column
        """
        if column not in df.columns:
            logger.warning(f"Column {column} not found for unit normalization")
            return df
        
        from_mapping = self.unit_mappings.get(from_unit)
        if not from_mapping:
            logger.warning(f"Unknown source unit: {from_unit}")
            return df
        
        # Get target unit (canonical if not specified)
        canonical = from_mapping.get("canonical", from_unit)
        target_unit = to_unit or canonical
        
        to_mapping = self.unit_mappings.get(target_unit)
        if not to_mapping:
            logger.warning(f"Unknown target unit: {target_unit}")
            return df
        
        # Calculate conversion factor
        from_factor = from_mapping.get("factor", 1)
        to_factor = to_mapping.get("factor", 1)
        conversion_factor = from_factor / to_factor
        
        # Apply conversion
        return df.with_columns(
            (pl.col(column) * conversion_factor).alias(column)
        )
    
    def normalize_units_by_policy(
        self,
        df: pl.DataFrame,
        units_policy: str,
        column_units: dict[str, str] | None = None,
    ) -> pl.DataFrame:
        """Apply units policy to DataFrame per DESIGN §6.
        
        Args:
            df: DataFrame to normalize
            units_policy: Policy - "preserve", "normalize", "strip"
            column_units: Optional mapping of column -> current unit
            
        Returns:
            DataFrame with units policy applied
        """
        if units_policy == "preserve":
            return df
        
        if not column_units:
            return df
        
        if units_policy == "normalize":
            # Normalize all columns to canonical units
            for col, unit in column_units.items():
                if col in df.columns:
                    df = self.apply_unit_normalization(df, col, unit)
        elif units_policy == "strip":
            # Just mark that units are stripped (no numeric change)
            pass
        
        return df
    
    def apply_column_renames(
        self,
        df: pl.DataFrame,
        renames: dict[str, str],
    ) -> pl.DataFrame:
        """Apply column renames.
        
        Args:
            df: DataFrame to rename columns
            renames: Dict of old_name -> new_name
            
        Returns:
            DataFrame with renamed columns
        """
        if not renames:
            return df
        
        # Only rename columns that exist
        valid_renames = {k: v for k, v in renames.items() if k in df.columns}
        if valid_renames:
            df = df.rename(valid_renames)
        
        return df
    
    def apply_pii_masking(
        self,
        df: pl.DataFrame,
        pii_columns: list[str],
        mask_in_preview: list[str] | None = None,
        mask_char: str = "*",
        preserve_length: bool = True,
    ) -> pl.DataFrame:
        """Apply PII column masking per DESIGN §10.
        
        Args:
            df: DataFrame to mask
            pii_columns: List of columns containing PII
            mask_in_preview: Additional columns to mask in preview
            mask_char: Character to use for masking
            preserve_length: If True, mask maintains original length
            
        Returns:
            DataFrame with PII columns masked
        """
        columns_to_mask = set(pii_columns)
        if mask_in_preview:
            columns_to_mask.update(mask_in_preview)
        
        for col in columns_to_mask:
            if col not in df.columns:
                continue
            
            try:
                if preserve_length:
                    # Replace each character with mask_char
                    df = df.with_columns(
                        pl.col(col).cast(pl.Utf8).str.replace_all(r".", mask_char).alias(col)
                    )
                else:
                    # Replace entire value with fixed mask
                    df = df.with_columns(
                        pl.when(pl.col(col).is_not_null())
                        .then(pl.lit(mask_char * 8))
                        .otherwise(None)
                        .alias(col)
                    )
                logger.debug(f"Masked PII column: {col}")
            except Exception as e:
                logger.error(f"PII masking error for {col}: {e}")
        
        return df
    
    def apply_type_coercion(
        self,
        df: pl.DataFrame,
        coercions: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Apply type coercion per DESIGN §6.
        
        Args:
            df: DataFrame to transform
            coercions: List of coercion definitions with column, to_type, format, etc.
            
        Returns:
            DataFrame with type-coerced columns
        """
        for coercion in coercions:
            col = coercion.get("column")
            to_type = coercion.get("to_type")
            
            if not col or col not in df.columns:
                continue
            
            try:
                if to_type == "datetime":
                    fmt = coercion.get("format", "%Y-%m-%d %H:%M:%S")
                    df = df.with_columns(
                        pl.col(col).str.strptime(pl.Datetime, fmt).alias(col)
                    )
                elif to_type == "date":
                    fmt = coercion.get("format", "%Y-%m-%d")
                    df = df.with_columns(
                        pl.col(col).str.strptime(pl.Date, fmt).alias(col)
                    )
                elif to_type == "string":
                    df = df.with_columns(pl.col(col).cast(pl.Utf8).alias(col))
                    if coercion.get("strip"):
                        df = df.with_columns(pl.col(col).str.strip_chars().alias(col))
                    if coercion.get("uppercase"):
                        df = df.with_columns(pl.col(col).str.to_uppercase().alias(col))
                    if coercion.get("lowercase"):
                        df = df.with_columns(pl.col(col).str.to_lowercase().alias(col))
                elif to_type == "float":
                    df = df.with_columns(pl.col(col).cast(pl.Float64).alias(col))
                elif to_type == "int":
                    df = df.with_columns(pl.col(col).cast(pl.Int64).alias(col))
                elif to_type == "bool":
                    df = df.with_columns(pl.col(col).cast(pl.Boolean).alias(col))
                else:
                    logger.warning(f"Unknown type coercion target: {to_type}")
            except Exception as e:
                logger.error(f"Type coercion error for {col} to {to_type}: {e}")
        
        return df
    
    def apply_column_transforms(
        self,
        df: pl.DataFrame,
        transforms: list[ColumnTransform],
    ) -> pl.DataFrame:
        """Apply column-level transformations.
        
        Args:
            df: DataFrame to transform
            transforms: List of transforms to apply
            
        Returns:
            Transformed DataFrame
        """
        for transform in transforms:
            if transform.source not in df.columns:
                logger.warning(f"Transform source column not found: {transform.source}")
                continue
            
            try:
                df = self._apply_single_transform(df, transform)
            except Exception as e:
                logger.error(f"Transform error for {transform.source}: {e}")
        
        return df
    
    def apply_row_filters(
        self,
        df: pl.DataFrame,
        filters: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Apply row filters per DESIGN §6.
        
        Args:
            df: DataFrame to filter
            filters: List of filter definitions
            
        Returns:
            Filtered DataFrame
        """
        if df.is_empty():
            return df
        
        for filter_def in filters:
            col = filter_def.get("column")
            if not col or col not in df.columns:
                continue
            
            op = filter_def.get("op", "equals")
            value = filter_def.get("value")
            
            try:
                if op == "equals":
                    df = df.filter(pl.col(col) == value)
                elif op == "not_equals":
                    df = df.filter(pl.col(col) != value)
                elif op == "gt":
                    df = df.filter(pl.col(col) > value)
                elif op == "gte":
                    df = df.filter(pl.col(col) >= value)
                elif op == "lt":
                    df = df.filter(pl.col(col) < value)
                elif op == "lte":
                    df = df.filter(pl.col(col) <= value)
                elif op == "between":
                    min_val = filter_def.get("min")
                    max_val = filter_def.get("max")
                    if min_val is not None and max_val is not None:
                        df = df.filter(
                            (pl.col(col) >= min_val) & (pl.col(col) <= max_val)
                        )
                elif op == "in":
                    values = filter_def.get("values", [])
                    df = df.filter(pl.col(col).is_in(values))
                elif op == "not_in":
                    values = filter_def.get("values", [])
                    df = df.filter(~pl.col(col).is_in(values))
                elif op == "is_null":
                    df = df.filter(pl.col(col).is_null())
                elif op == "is_not_null":
                    df = df.filter(pl.col(col).is_not_null())
                elif op == "contains":
                    df = df.filter(pl.col(col).cast(pl.Utf8).str.contains(str(value)))
                elif op == "startswith":
                    df = df.filter(pl.col(col).cast(pl.Utf8).str.starts_with(str(value)))
                elif op == "endswith":
                    df = df.filter(pl.col(col).cast(pl.Utf8).str.ends_with(str(value)))
                else:
                    logger.warning(f"Unknown filter op: {op}")
            except Exception as e:
                logger.error(f"Row filter error for {col}: {e}")
        
        return df
    
    def apply_calculated_columns(
        self,
        df: pl.DataFrame,
        calculations: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Apply calculated column definitions.
        
        Args:
            df: DataFrame to add columns to
            calculations: List of calculation definitions
            
        Returns:
            DataFrame with calculated columns added
        """
        for calc in calculations:
            name = calc.get("name")
            expression = calc.get("expression")
            
            if not name or not expression:
                continue
            
            try:
                # Parse simple arithmetic expressions
                # Format: "col1 + col2", "col1 * 100", etc.
                df = self._evaluate_expression(df, name, expression)
                
                # Apply rounding if specified
                round_to = calc.get("round_to")
                if round_to is not None and name in df.columns:
                    df = df.with_columns(
                        pl.col(name).round(round_to).alias(name)
                    )
            except Exception as e:
                logger.error(f"Calculated column error for {name}: {e}")
        
        return df
    
    def _replace_nan_values(
        self,
        df: pl.DataFrame,
        nan_values: list[str],
    ) -> pl.DataFrame:
        """Replace NaN string values with null."""
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                df = df.with_columns(
                    pl.when(pl.col(col).is_in(nan_values))
                    .then(None)
                    .otherwise(pl.col(col))
                    .alias(col)
                )
        return df
    
    def _coerce_numeric(self, df: pl.DataFrame) -> pl.DataFrame:
        """Attempt to coerce string columns to numeric."""
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                # Check if column looks numeric
                sample = df[col].head(10).drop_nulls()
                if len(sample) == 0:
                    continue
                
                # Try to cast
                try:
                    test_cast = sample.cast(pl.Float64, strict=False)
                    null_count = test_cast.null_count()
                    
                    # If most values convert successfully, apply
                    if null_count < len(sample) * 0.5:
                        df = df.with_columns(
                            pl.col(col).cast(pl.Float64, strict=False).alias(col)
                        )
                except Exception:
                    pass  # Keep as string
        
        return df
    
    def _apply_single_transform(
        self,
        df: pl.DataFrame,
        transform: ColumnTransform,
    ) -> pl.DataFrame:
        """Apply a single column transform."""
        args = transform.args or {}
        
        if transform.transform == "rename":
            return df.rename({transform.source: transform.target})
        
        elif transform.transform == "unit_convert":
            factor = args.get("factor", 1)
            return df.with_columns(
                (pl.col(transform.source) * factor).alias(transform.target)
            )
        
        elif transform.transform == "uppercase":
            return df.with_columns(
                pl.col(transform.source).str.to_uppercase().alias(transform.target)
            )
        
        elif transform.transform == "lowercase":
            return df.with_columns(
                pl.col(transform.source).str.to_lowercase().alias(transform.target)
            )
        
        elif transform.transform == "strip":
            return df.with_columns(
                pl.col(transform.source).str.strip_chars().alias(transform.target)
            )
        
        elif transform.transform == "round":
            decimals = args.get("decimals", 2)
            return df.with_columns(
                pl.col(transform.source).round(decimals).alias(transform.target)
            )
        
        else:
            logger.warning(f"Unknown transform type: {transform.transform}")
            return df
    
    def _evaluate_expression(
        self,
        df: pl.DataFrame,
        name: str,
        expression: str,
    ) -> pl.DataFrame:
        """Evaluate simple arithmetic expression.
        
        Supports: +, -, *, /, column references
        """
        
        # Parse expression: "col1 + col2", "col1 * 100", etc.
        # This is a simple parser - extend as needed
        
        # Check for binary operations
        for op, pl_method in [("+", "__add__"), ("-", "__sub__"), 
                               ("*", "__mul__"), ("/", "__truediv__")]:
            if op in expression:
                parts = expression.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # Determine if operands are columns or literals
                    left_expr = self._get_operand_expr(left, df)
                    right_expr = self._get_operand_expr(right, df)
                    
                    if left_expr is not None and right_expr is not None:
                        if op == "+":
                            result = left_expr + right_expr
                        elif op == "-":
                            result = left_expr - right_expr
                        elif op == "*":
                            result = left_expr * right_expr
                        elif op == "/":
                            result = left_expr / right_expr
                        else:
                            return df
                        
                        return df.with_columns(result.alias(name))
        
        return df
    
    def _get_operand_expr(self, operand: str, df: pl.DataFrame) -> pl.Expr | None:
        """Get polars expression for operand (column or literal)."""
        # Check if it's a column reference
        if operand in df.columns:
            return pl.col(operand)
        
        # Try to parse as number
        try:
            value = float(operand)
            return pl.lit(value)
        except ValueError:
            pass
        
        return None


def apply_transforms(
    df: pl.DataFrame,
    profile: DATProfile,
    renames: dict[str, str] | None = None,
    transforms: list[ColumnTransform] | None = None,
    calculations: list[dict[str, Any]] | None = None,
) -> pl.DataFrame:
    """Convenience function for applying all transforms.
    
    Args:
        df: DataFrame to transform
        profile: Profile with normalization rules
        renames: Column renames
        transforms: Column transforms
        calculations: Calculated columns
        
    Returns:
        Transformed DataFrame
    """
    pipeline = TransformPipeline()
    
    df = pipeline.apply_normalization(df, profile)
    
    if renames:
        df = pipeline.apply_column_renames(df, renames)
    
    if transforms:
        df = pipeline.apply_column_transforms(df, transforms)
    
    if calculations:
        df = pipeline.apply_calculated_columns(df, calculations)
    
    return df
