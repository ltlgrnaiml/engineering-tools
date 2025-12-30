"""SOV DataSet I/O contracts - data loading and output management.

Per ADR-0024: SOV integrates with platform DataSet infrastructure.
Per ADR-0026: DataSets have lineage tracking with version_id and parent_version_id.
Per ADR-0015: Data stored as Parquet, metadata as JSON.
Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).

This module defines contracts for:
- DataSet loading and validation
- Column metadata with SOV annotations
- Output DataSet creation with lineage
- Result serialization contracts

SOV consumes DataSets from DAT and produces DataSets for PPTX.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


# =============================================================================
# Column Annotation Types
# =============================================================================


class SOVColumnRole(str, Enum):
    """Role of a column in SOV analysis."""

    FACTOR = "factor"  # Categorical factor column
    RESPONSE = "response"  # Numeric response column
    COVARIATE = "covariate"  # Numeric covariate
    IDENTIFIER = "identifier"  # Row identifier (excluded from analysis)
    TIMESTAMP = "timestamp"  # Time-related column
    EXCLUDED = "excluded"  # Explicitly excluded from analysis
    UNKNOWN = "unknown"  # Role not determined


class SOVFactorType(str, Enum):
    """Type of factor in the statistical model."""

    FIXED = "fixed"  # Fixed effect
    RANDOM = "random"  # Random effect
    NESTED = "nested"  # Nested within another factor
    BLOCKING = "blocking"  # Blocking factor
    REPEATED = "repeated"  # Repeated measures factor


class SignificanceLevel(str, Enum):
    """Statistical significance classification."""

    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.001
    SIGNIFICANT = "significant"  # p < 0.05
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.1
    NOT_SIGNIFICANT = "not_significant"  # p >= 0.1


# =============================================================================
# Column Metadata Contracts
# =============================================================================


class SOVColumnMeta(BaseModel):
    """Extended column metadata with SOV-specific annotations.

    Per ADR-0024: Column metadata from input is preserved and extended.
    """

    # Base column info (from DataSetManifest.ColumnMeta)
    name: str
    dtype: str  # "int64", "float64", "string", "datetime64[ns]", "bool"
    nullable: bool = True
    description: str | None = None
    source_tool: Literal["dat", "sov", "pptx", "manual"] | None = None
    unit: str | None = None

    # SOV-specific annotations
    role: SOVColumnRole = SOVColumnRole.UNKNOWN
    factor_type: SOVFactorType | None = Field(
        None,
        description="Factor type (only for FACTOR role)",
    )
    nested_within: str | None = Field(
        None,
        description="Parent factor name (only for NESTED factor_type)",
    )

    # Factor statistics (populated after analysis)
    level_count: int | None = Field(None, ge=0, description="Number of unique levels")
    levels: list[str] | None = Field(
        None,
        description="Unique level values (for categorical)",
    )

    # Response statistics (populated after analysis)
    mean: float | None = None
    std: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    null_count: int | None = Field(None, ge=0)

    # Significance (for factors after ANOVA)
    p_value: float | None = Field(None, ge=0, le=1)
    significance: SignificanceLevel | None = None
    variance_contribution_pct: float | None = Field(None, ge=0, le=100)
    effect_size: float | None = Field(None, ge=0)

    @classmethod
    def from_base_column(
        cls,
        name: str,
        dtype: str,
        nullable: bool = True,
        description: str | None = None,
        source_tool: str | None = None,
        unit: str | None = None,
    ) -> "SOVColumnMeta":
        """Create SOVColumnMeta from base column info.

        Args:
            name: Column name.
            dtype: Data type string.
            nullable: Whether column allows nulls.
            description: Column description.
            source_tool: Tool that created the column.
            unit: Unit of measurement.

        Returns:
            New SOVColumnMeta with base info populated.
        """
        return cls(
            name=name,
            dtype=dtype,
            nullable=nullable,
            description=description,
            source_tool=source_tool,  # type: ignore
            unit=unit,
        )


# =============================================================================
# DataSet Loading Contracts
# =============================================================================


class DataSetLoadRequest(BaseModel):
    """Request to load a DataSet for SOV analysis."""

    dataset_id: str = Field(..., description="DataSet ID to load")
    columns: list[str] | None = Field(
        None,
        description="Specific columns to load (None = all)",
    )
    filter_expression: str | None = Field(
        None,
        description="Filter expression (pandas query syntax)",
    )
    sample_fraction: float | None = Field(
        None,
        gt=0,
        le=1,
        description="Fraction of rows to sample",
    )
    sample_n: int | None = Field(
        None,
        ge=1,
        description="Exact number of rows to sample",
    )
    random_seed: int = Field(42, description="Seed for sampling")
    validate_schema: bool = Field(
        True,
        description="Validate dataset schema before loading",
    )


class DataSetLoadResult(BaseModel):
    """Result of loading a DataSet."""

    dataset_id: str
    dataset_name: str
    source_tool: Literal["dat", "sov", "pptx", "manual"]

    # Load statistics
    rows_loaded: int = Field(..., ge=0)
    columns_loaded: int = Field(..., ge=0)
    bytes_loaded: int = Field(..., ge=0)
    load_duration_ms: float = Field(..., ge=0)

    # Filtering/sampling statistics
    rows_before_filter: int = Field(..., ge=0)
    rows_after_filter: int = Field(..., ge=0)
    was_sampled: bool = False

    # Column metadata
    columns: list[SOVColumnMeta] = Field(default_factory=list)

    # Lineage info
    parent_dataset_ids: list[str] = Field(default_factory=list)
    version_id: str | None = Field(
        None,
        description="SHA-256 hash of loaded data (per ADR-0026)",
    )

    # Validation
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if load was successful with no errors."""
        return len(self.validation_errors) == 0


class DataSetValidationResult(BaseModel):
    """Result of validating a DataSet for SOV analysis."""

    dataset_id: str
    valid: bool

    # Required columns check
    missing_required_columns: list[str] = Field(default_factory=list)
    invalid_column_types: dict[str, str] = Field(
        default_factory=dict,
        description="Column -> expected type for mismatched columns",
    )

    # Data quality checks
    insufficient_rows: bool = False
    min_rows_required: int = Field(10, ge=1)
    actual_rows: int = Field(0, ge=0)

    insufficient_factor_levels: dict[str, int] = Field(
        default_factory=dict,
        description="Factor -> level count for factors with too few levels",
    )
    min_levels_required: int = Field(2, ge=2)

    excessive_null_columns: list[str] = Field(
        default_factory=list,
        description="Columns with > 50% null values",
    )

    # Errors and warnings
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    validation_duration_ms: float = Field(0.0, ge=0.0)


# =============================================================================
# DataSet Output Contracts
# =============================================================================


class OutputColumn(BaseModel):
    """Column definition for output DataSet."""

    name: str
    dtype: str
    description: str | None = None
    unit: str | None = None

    # SOV-specific output annotations
    is_derived: bool = Field(
        False,
        description="Whether column was computed by SOV",
    )
    source_columns: list[str] = Field(
        default_factory=list,
        description="Input columns this was derived from",
    )
    computation: str | None = Field(
        None,
        description="Computation description (e.g., 'variance contribution %')",
    )


class DataSetOutputConfig(BaseModel):
    """Configuration for creating output DataSet.

    Per ADR-0024: Output includes parent_ref for lineage.
    """

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None

    # Output format
    format: Literal["parquet", "csv"] = Field(
        "parquet",
        description="Output format (per ADR-0015: prefer Parquet)",
    )
    compression: Literal["snappy", "gzip", "zstd", "none"] = "snappy"

    # Lineage
    parent_dataset_id: str = Field(
        ...,
        description="Input DataSet ID for lineage tracking",
    )
    parent_version_id: str | None = Field(
        None,
        description="Specific version of parent (per ADR-0026)",
    )

    # Content selection
    include_anova_table: bool = Field(True, description="Include ANOVA results table")
    include_variance_components: bool = Field(True, description="Include variance components")
    include_post_hoc: bool = Field(True, description="Include post-hoc comparisons")
    include_group_means: bool = Field(True, description="Include group means")
    include_residuals: bool = Field(False, description="Include residual values")
    include_visualization_specs: bool = Field(
        True,
        description="Include visualization contracts in manifest",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list)
    owner: str | None = None


class DataSetOutputResult(BaseModel):
    """Result of creating output DataSet.

    Per ADR-0024: Output includes lineage information.
    """

    # Identity
    dataset_id: str = Field(
        ...,
        description="ID of created DataSet",
    )
    name: str
    version_id: str = Field(
        ...,
        description="SHA-256 hash of output data (per ADR-0026)",
    )

    # Lineage
    parent_dataset_id: str
    parent_version_id: str | None = None
    lineage_relationship: Literal["derived", "analyzed", "transformed"] = "analyzed"

    # Output statistics
    rows_written: int = Field(..., ge=0)
    columns_written: int = Field(..., ge=0)
    bytes_written: int = Field(..., ge=0)
    write_duration_ms: float = Field(..., ge=0)

    # Paths (relative, per ADR-0018)
    data_path: str = Field(..., description="Relative path to data file")
    manifest_path: str = Field(..., description="Relative path to manifest.json")

    # Timestamps
    created_at: datetime

    @field_validator("data_path", "manifest_path")
    @classmethod
    def validate_relative_path(cls, v: str) -> str:
        """Ensure paths are relative (per ADR-0018 path-safety)."""
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"Absolute paths not allowed: {v}")
        return v


# =============================================================================
# Result Serialization Contracts
# =============================================================================


class ANOVATableRow(BaseModel):
    """Single row in the ANOVA table output."""

    source: str = Field(..., description="Source of variation (factor name or interaction)")
    sum_of_squares: float = Field(..., ge=0)
    degrees_of_freedom: int = Field(..., ge=0)
    mean_square: float = Field(..., ge=0)
    f_statistic: float | None = Field(None, ge=0)
    p_value: float | None = Field(None, ge=0, le=1)
    significance: str = Field(
        "",
        description="Significance indicator (*, **, ***)",
    )
    variance_pct: float | None = Field(None, ge=0, le=100)
    is_significant: bool = False


class ANOVATableOutput(BaseModel):
    """Complete ANOVA table for output."""

    rows: list[ANOVATableRow] = Field(default_factory=list)
    total_ss: float = Field(..., ge=0)
    total_df: int = Field(..., ge=0)
    model_ss: float = Field(..., ge=0)
    model_df: int = Field(..., ge=0)
    error_ss: float = Field(..., ge=0)
    error_df: int = Field(..., ge=0)
    r_squared: float = Field(..., ge=0, le=1)
    adjusted_r_squared: float | None = None
    alpha: float = Field(0.05, gt=0, lt=1)


class PostHocTableRow(BaseModel):
    """Single row in post-hoc comparison table."""

    factor: str
    group_1: str
    group_2: str
    mean_diff: float
    std_error: float = Field(..., ge=0)
    p_value: float = Field(..., ge=0, le=1)
    p_adjusted: float = Field(..., ge=0, le=1)
    ci_lower: float | None = None
    ci_upper: float | None = None
    is_significant: bool = False


class PostHocTableOutput(BaseModel):
    """Complete post-hoc comparison table."""

    method: str = Field(..., description="Post-hoc method name")
    alpha: float = Field(0.05, gt=0, lt=1)
    rows: list[PostHocTableRow] = Field(default_factory=list)
    significant_comparisons: int = Field(0, ge=0)
    total_comparisons: int = Field(0, ge=0)


class GroupMeansRow(BaseModel):
    """Single row in group means table."""

    factor: str
    level: str
    count: int = Field(..., ge=0)
    mean: float
    std: float = Field(..., ge=0)
    se: float = Field(..., ge=0, description="Standard error")
    ci_lower: float
    ci_upper: float


class GroupMeansOutput(BaseModel):
    """Complete group means table."""

    rows: list[GroupMeansRow] = Field(default_factory=list)
    confidence_level: float = Field(0.95, gt=0, lt=1)
    grand_mean: float
    grand_std: float = Field(..., ge=0)
    total_n: int = Field(..., ge=0)


class VarianceComponentRow(BaseModel):
    """Single row in variance components table."""

    component: str
    variance_estimate: float = Field(..., ge=0)
    variance_pct: float = Field(..., ge=0, le=100)
    std_error: float | None = Field(None, ge=0)
    ci_lower: float | None = Field(None, ge=0)
    ci_upper: float | None = None


class VarianceComponentsOutput(BaseModel):
    """Complete variance components table."""

    rows: list[VarianceComponentRow] = Field(default_factory=list)
    total_variance: float = Field(..., ge=0)
    method: str = Field("anova", description="Estimation method")


class SOVResultsBundle(BaseModel):
    """Complete bundle of SOV analysis results for output.

    Contains all result tables in serializable format.
    """

    # Analysis metadata
    analysis_id: str
    analysis_type: Literal["anova", "variance_components"]
    input_dataset_id: str
    response_column: str
    factor_columns: list[str]

    # Result tables
    anova_table: ANOVATableOutput | None = None
    variance_components: VarianceComponentsOutput | None = None
    post_hoc_tables: list[PostHocTableOutput] = Field(default_factory=list)
    group_means: GroupMeansOutput | None = None

    # Column metadata (with SOV annotations)
    column_metadata: list[SOVColumnMeta] = Field(default_factory=list)

    # Visualization specs (IDs reference visualization contracts)
    visualization_spec_ids: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    analysis_duration_ms: float = Field(0.0, ge=0.0)


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "SOVColumnRole",
    "SOVFactorType",
    "SignificanceLevel",
    # Column metadata
    "SOVColumnMeta",
    # Loading
    "DataSetLoadRequest",
    "DataSetLoadResult",
    "DataSetValidationResult",
    # Output
    "OutputColumn",
    "DataSetOutputConfig",
    "DataSetOutputResult",
    # Result tables
    "ANOVATableRow",
    "ANOVATableOutput",
    "PostHocTableRow",
    "PostHocTableOutput",
    "GroupMeansRow",
    "GroupMeansOutput",
    "VarianceComponentRow",
    "VarianceComponentsOutput",
    "SOVResultsBundle",
]
