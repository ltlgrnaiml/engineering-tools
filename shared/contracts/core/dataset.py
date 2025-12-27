"""DataSet contracts - universal data currency between tools.

A DataSet is a standardized artifact bundle (Parquet + JSON manifest) that
flows between tools. All tools produce and consume DataSets, enabling
seamless data piping workflows.

Per ADR-0004: DataSet IDs are deterministic (SHA-256 hash of inputs).
Per ADR-0008: All timestamps are ISO-8601 UTC (no microseconds).
Per ADR-0014: Data stored as Parquet, metadata as JSON.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class ColumnMeta(BaseModel):
    """Metadata for a single column in a DataSet."""

    name: str
    dtype: str  # "int64", "float64", "string", "datetime64[ns]", "bool"
    nullable: bool = True
    description: str | None = None
    source_tool: Literal["dat", "sov", "pptx", "manual"] | None = None
    unit: str | None = None  # e.g., "nm", "um", "%"


class DataSetManifest(BaseModel):
    """Provenance, schema, and lineage for a DataSet.

    This is stored as manifest.json alongside data.parquet in the
    workspace/datasets/{dataset_id}/ directory.
    """

    # Identity (per ADR-0004: deterministic hash)
    dataset_id: str = Field(
        ...,
        description="Deterministic SHA-256 hash (first 16 chars) of inputs",
    )
    name: str = Field(..., description="Human-readable name for display")

    # Timestamps (per ADR-0008: ISO-8601 UTC, no microseconds)
    created_at: datetime
    updated_at: datetime | None = None
    locked_at: datetime | None = None

    # Origin
    created_by_tool: Literal["dat", "sov", "pptx", "manual"]

    # Schema
    columns: list[ColumnMeta]
    row_count: int
    size_bytes: int | None = None

    # Lineage (for cross-tool piping)
    parent_dataset_ids: list[str] = Field(
        default_factory=list,
        description="IDs of parent DataSets this was derived from",
    )
    pipeline_id: str | None = Field(
        None,
        description="Pipeline ID if created as part of a pipeline execution",
    )
    pipeline_step: int | None = None

    # DAT-specific metadata
    aggregation_levels: list[str] | None = Field(
        None,
        description="Aggregation hierarchy, e.g., ['wafer', 'lot', 'product']",
    )
    source_files: list[str] = Field(
        default_factory=list,
        description="Original source file paths (relative)",
    )
    profile_id: str | None = Field(
        None,
        description="DAT extraction profile ID used",
    )

    # SOV-specific metadata
    analysis_type: str | None = Field(
        None,
        description="Type of analysis, e.g., 'anova', 'variance_components'",
    )
    factors: list[str] | None = Field(
        None,
        description="Factor columns used in SOV analysis",
    )
    response_columns: list[str] | None = Field(
        None,
        description="Response columns analyzed",
    )


class DataSetRef(BaseModel):
    """Lightweight reference to a DataSet for API list responses.

    Used when returning lists of DataSets without full manifest details.
    """

    dataset_id: str
    name: str
    created_at: datetime
    created_by_tool: Literal["dat", "sov", "pptx", "manual"]
    row_count: int
    column_count: int
    parent_count: int = Field(
        0,
        description="Number of parent datasets (0 = root/source data)",
    )
    size_bytes: int | None = None


class DataSetPreview(BaseModel):
    """Preview of DataSet contents for UI display."""

    dataset_id: str
    columns: list[str]
    rows: list[dict]  # First N rows as dicts
    total_rows: int
    preview_rows: int
