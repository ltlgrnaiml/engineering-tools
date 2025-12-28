"""Context stage - optional parsing hints and column configuration.

Per ADR-0003: Context is an optional stage that does NOT cascade unlock.
Users can skip directly from Selection to Table Availability.
"""
from dataclasses import dataclass, field

from shared.utils.stage_id import compute_stage_id


@dataclass
class ColumnOverride:
    """Override configuration for a column."""
    column_name: str
    target_dtype: str | None = None  # "int64", "float64", "string", "datetime64"
    rename_to: str | None = None
    drop: bool = False


@dataclass
class ContextConfig:
    """Configuration for the context stage."""
    column_overrides: list[ColumnOverride] = field(default_factory=list)
    date_format: str | None = None  # e.g., "%Y-%m-%d"
    decimal_separator: str = "."
    thousands_separator: str | None = None
    encoding: str = "utf-8"
    skip_rows: int = 0
    header_row: int | None = None  # None = auto-detect


@dataclass
class ContextResult:
    """Result of context stage."""
    context_id: str
    config: ContextConfig
    completed: bool = True


async def execute_context(
    run_id: str,
    config: ContextConfig,
) -> ContextResult:
    """Execute context stage - save parsing configuration.
    
    Per ADR-0003: Context is optional and does not cascade unlock.
    This stage just validates and persists the configuration.
    
    Args:
        run_id: DAT run ID
        config: Context configuration
        
    Returns:
        ContextResult with computed context ID
    """
    # Compute deterministic context ID
    context_inputs = {
        "run_id": run_id,
        "column_overrides": [
            {
                "column_name": co.column_name,
                "target_dtype": co.target_dtype,
                "rename_to": co.rename_to,
                "drop": co.drop,
            }
            for co in config.column_overrides
        ],
        "date_format": config.date_format,
        "decimal_separator": config.decimal_separator,
        "encoding": config.encoding,
    }
    context_id = compute_stage_id(context_inputs, prefix="ctx_")

    return ContextResult(
        context_id=context_id,
        config=config,
        completed=True,
    )


def apply_context_to_dataframe(
    df: "pl.DataFrame",
    config: ContextConfig,
) -> "pl.DataFrame":
    """Apply context configuration to a DataFrame.
    
    Args:
        df: Input DataFrame
        config: Context configuration to apply
        
    Returns:
        Transformed DataFrame
    """
    import polars as pl

    result = df

    for override in config.column_overrides:
        if override.column_name not in result.columns:
            continue

        # Drop column if requested
        if override.drop:
            result = result.drop(override.column_name)
            continue

        # Rename column if requested
        if override.rename_to:
            result = result.rename({override.column_name: override.rename_to})
            col_name = override.rename_to
        else:
            col_name = override.column_name

        # Cast to target dtype if specified
        if override.target_dtype:
            dtype_map = {
                "int64": pl.Int64,
                "float64": pl.Float64,
                "string": pl.Utf8,
                "bool": pl.Boolean,
            }
            if override.target_dtype in dtype_map:
                result = result.with_columns(
                    pl.col(col_name).cast(dtype_map[override.target_dtype])
                )

    return result
