"""Preview stage - optional preview of data before full parse.

Per ADR-0003: Preview is an optional stage that does NOT cascade unlock.
Users can skip directly from Table Selection to Parse.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from shared.utils.stage_id import compute_stage_id
from .table_selection import TableSelectionResult, get_selected_file_table_map
from .context import ContextConfig, apply_context_to_dataframe


@dataclass
class PreviewConfig:
    """Configuration for preview stage."""
    max_rows_per_table: int = 100
    include_stats: bool = True


@dataclass
class TablePreview:
    """Preview of a single table."""
    file_path: str
    table_name: str
    columns: list[str]
    dtypes: list[str]
    row_count: int
    preview_rows: list[dict[str, Any]]
    stats: dict[str, Any] | None = None


@dataclass
class PreviewResult:
    """Result of preview stage."""
    preview_id: str
    table_previews: list[TablePreview]
    total_rows: int
    total_columns: int
    completed: bool = False  # Per SPEC-0044: manual_complete - user must acknowledge


async def execute_preview(
    run_id: str,
    table_selection: TableSelectionResult,
    config: PreviewConfig,
    context_config: ContextConfig | None = None,
) -> PreviewResult:
    """Execute preview stage - load sample data from selected tables.
    
    Per ADR-0003: Preview is optional and does not cascade unlock.
    
    Args:
        run_id: DAT run ID
        table_selection: Result from table selection stage
        config: Preview configuration
        context_config: Optional context configuration to apply
        
    Returns:
        PreviewResult with table previews
    """
    from dat_aggregation.adapters.factory import AdapterFactory

    file_table_map = get_selected_file_table_map(table_selection)
    previews: list[TablePreview] = []
    total_rows = 0
    all_columns: set[str] = set()

    for file_path_str, table_names in file_table_map.items():
        file_path = Path(file_path_str)
        adapter = AdapterFactory.get_adapter(file_path)

        for table_name in table_names:
            try:
                # Read the table
                df = adapter.read(file_path, sheet=table_name)

                # Apply context configuration if provided
                if context_config:
                    df = apply_context_to_dataframe(df, context_config)

                # Get preview rows
                preview_df = df.head(config.max_rows_per_table)

                # Compute stats if requested
                stats = None
                if config.include_stats:
                    stats = _compute_table_stats(df)

                previews.append(TablePreview(
                    file_path=file_path_str,
                    table_name=table_name,
                    columns=df.columns,
                    dtypes=[str(df[col].dtype) for col in df.columns],
                    row_count=len(df),
                    preview_rows=preview_df.to_dicts(),
                    stats=stats,
                ))

                total_rows += len(df)
                all_columns.update(df.columns)

            except Exception as e:
                # Include error in preview
                previews.append(TablePreview(
                    file_path=file_path_str,
                    table_name=table_name,
                    columns=[],
                    dtypes=[],
                    row_count=0,
                    preview_rows=[],
                    stats={"error": str(e)},
                ))

    # Compute deterministic ID
    preview_inputs = {
        "run_id": run_id,
        "tables": sorted([
            f"{p.file_path}:{p.table_name}"
            for p in previews
        ]),
        "max_rows": config.max_rows_per_table,
    }
    preview_id = compute_stage_id(preview_inputs, prefix="prev_")

    return PreviewResult(
        preview_id=preview_id,
        table_previews=previews,
        total_rows=total_rows,
        total_columns=len(all_columns),
        completed=True,
    )


def _compute_table_stats(df: pl.DataFrame) -> dict[str, Any]:
    """Compute basic statistics for a DataFrame."""
    stats: dict[str, Any] = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "null_counts": {},
        "numeric_summary": {},
    }

    for col in df.columns:
        # Null count
        null_count = df[col].null_count()
        if null_count > 0:
            stats["null_counts"][col] = null_count

        # Numeric summary
        if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]:
            try:
                stats["numeric_summary"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()) if len(df) > 1 else 0.0,
                }
            except Exception:
                pass

    return stats
