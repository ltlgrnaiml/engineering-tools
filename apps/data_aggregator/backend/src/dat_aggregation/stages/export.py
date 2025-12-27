"""Export stage - create DataSet from parsed data.

Per ADR-0014: Output as Parquet with JSON manifest.
"""
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.storage.artifact_store import ArtifactStore
from shared.utils.stage_id import compute_dataset_id

from .parse import ParseResult


async def execute_export(
    run_id: str,
    parse_result: ParseResult,
    name: str | None = None,
    description: str | None = None,
    aggregation_levels: list[str] | None = None,
    profile_id: str | None = None,
) -> DataSetManifest:
    """Export parsed data as a shareable DataSet.
    
    Args:
        run_id: DAT run ID
        parse_result: Result from parse stage
        name: Optional name for the DataSet
        description: Optional description
        aggregation_levels: Optional levels used for aggregation
        profile_id: Optional extraction profile ID
        
    Returns:
        DataSetManifest for the created DataSet
    """
    data = parse_result.data
    
    # Apply aggregation if levels specified
    if aggregation_levels and len(aggregation_levels) > 0:
        # Group by aggregation levels and compute summary stats
        agg_exprs = []
        for col in data.columns:
            if col not in aggregation_levels:
                dtype = data[col].dtype
                if dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int16, pl.Int8]:
                    agg_exprs.extend([
                        pl.col(col).mean().alias(f"{col}_mean"),
                        pl.col(col).std().alias(f"{col}_std"),
                        pl.col(col).count().alias(f"{col}_count"),
                    ])
        
        if agg_exprs:
            data = data.group_by(aggregation_levels).agg(agg_exprs)
    
    # Compute deterministic DataSet ID
    dataset_id = compute_dataset_id(
        run_id=run_id,
        columns=data.columns,
        row_count=len(data),
        aggregation_levels=aggregation_levels,
    )
    
    # Build manifest
    now = datetime.now(timezone.utc)
    default_name = name or f"DAT Export - {run_id[:8]}"
    
    manifest = DataSetManifest(
        dataset_id=dataset_id,
        name=default_name,
        description=description or f"Exported from DAT run {run_id}",
        created_at=now,
        created_by_tool="dat",
        columns=[
            ColumnMeta(
                name=col,
                dtype=str(data[col].dtype),
                nullable=data[col].null_count() > 0,
                source_tool="dat",
            )
            for col in data.columns
        ],
        row_count=len(data),
        aggregation_levels=aggregation_levels,
        source_files=parse_result.source_files,
        profile_id=profile_id,
        parent_ids=[],  # Could link to input datasets if applicable
    )
    
    # Write to shared storage
    store = ArtifactStore()
    await store.write_dataset(dataset_id, data, manifest)
    
    return manifest
