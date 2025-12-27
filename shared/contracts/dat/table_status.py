"""DAT Table Availability Status contracts.

Per ADR-0006: Track table availability status for each DAT job.
Per ADR-0008: All timestamps are ISO-8601 UTC (no microseconds).

Table availability tracking provides:
- Real-time status of which tables are available
- Health metrics for data quality monitoring
- Historical tracking for audit trails

This is the hand-off contract between DAT's parse stage and
consumers (frontend, SOV, PPTX).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


class TableAvailabilityStatus(str, Enum):
    """Status of a table's availability.

    State progression:
        pending → parsing → available
        pending → parsing → partial (some rows failed)
        pending → parsing → failed
        available → stale (source updated)
    """

    PENDING = "pending"  # Not yet processed
    PARSING = "parsing"  # Currently being parsed
    AVAILABLE = "available"  # Successfully parsed, all data available
    PARTIAL = "partial"  # Parsed with errors, partial data available
    FAILED = "failed"  # Parse failed, no data available
    STALE = "stale"  # Source data changed since last parse


class TableHealthLevel(str, Enum):
    """Health level based on data quality metrics."""

    HEALTHY = "healthy"  # All quality checks pass
    WARNING = "warning"  # Minor issues detected
    CRITICAL = "critical"  # Major issues detected
    UNKNOWN = "unknown"  # Not enough data to assess


class ColumnHealth(BaseModel):
    """Health metrics for a single column."""

    column_name: str
    non_null_count: int = Field(..., ge=0)
    null_count: int = Field(0, ge=0)
    null_percentage: float = Field(0.0, ge=0.0, le=100.0)
    distinct_count: int | None = Field(None, ge=0)
    min_value: Any = None
    max_value: Any = None
    mean_value: float | None = None
    std_value: float | None = None
    out_of_range_count: int = Field(0, ge=0)
    invalid_format_count: int = Field(0, ge=0)

    @property
    def health_level(self) -> TableHealthLevel:
        """Calculate health level based on metrics."""
        if self.null_percentage > 50:
            return TableHealthLevel.CRITICAL
        if self.null_percentage > 20 or self.out_of_range_count > 0:
            return TableHealthLevel.WARNING
        return TableHealthLevel.HEALTHY


class TableHealth(BaseModel):
    """Overall health metrics for a table."""

    row_count: int = Field(..., ge=0)
    column_count: int = Field(..., ge=0)
    size_bytes: int = Field(0, ge=0)
    column_health: list[ColumnHealth] = Field(default_factory=list)
    validation_passed: int = Field(0, ge=0)
    validation_failed: int = Field(0, ge=0)
    validation_warnings: int = Field(0, ge=0)

    @property
    def health_level(self) -> TableHealthLevel:
        """Calculate overall health level."""
        if not self.column_health:
            return TableHealthLevel.UNKNOWN
        if self.validation_failed > 0:
            return TableHealthLevel.CRITICAL
        if self.validation_warnings > 0:
            return TableHealthLevel.WARNING
        column_levels = [ch.health_level for ch in self.column_health]
        if TableHealthLevel.CRITICAL in column_levels:
            return TableHealthLevel.CRITICAL
        if TableHealthLevel.WARNING in column_levels:
            return TableHealthLevel.WARNING
        return TableHealthLevel.HEALTHY


class TableParseError(BaseModel):
    """Error encountered while parsing a table."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    row_number: int | None = Field(None, ge=0)
    column_name: str | None = None
    source_file: str | None = None
    recoverable: bool = Field(
        False,
        description="True if partial data is still available",
    )


class TableAvailability(BaseModel):
    """Availability status and metadata for a single table.

    This is the primary contract for communicating table status
    from DAT to other tools and the frontend.
    """

    # Identity
    table_id: str = Field(
        ...,
        description="Unique identifier for this table instance",
    )
    table_name: str = Field(..., description="Human-readable table name")
    job_id: str = Field(..., description="Parent DAT job ID")
    stage_id: str = Field(..., description="Parse stage ID that produced this")

    # Status
    status: TableAvailabilityStatus = TableAvailabilityStatus.PENDING
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    progress_message: str | None = None

    # Timestamps (per ADR-0008)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_accessed_at: datetime | None = None

    # Source info
    source_files: list[str] = Field(
        default_factory=list,
        description="Relative paths to source files",
    )
    source_file_count: int = Field(0, ge=0)
    source_total_bytes: int = Field(0, ge=0)

    # Output info
    output_path: str | None = Field(
        None,
        description="Relative path to parsed output (e.g., data.parquet)",
    )
    row_count: int | None = Field(None, ge=0)
    column_count: int | None = Field(None, ge=0)
    columns: list[str] = Field(default_factory=list)

    # Health metrics
    health: TableHealth | None = None

    # Errors
    errors: list[TableParseError] = Field(default_factory=list)
    error_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)

    # Profile info
    profile_id: str | None = None
    profile_name: str | None = None

    @property
    def is_available(self) -> bool:
        """Check if table data is available (even partially)."""
        return self.status in {
            TableAvailabilityStatus.AVAILABLE,
            TableAvailabilityStatus.PARTIAL,
        }

    @property
    def health_level(self) -> TableHealthLevel:
        """Get health level from health metrics or status."""
        if self.health:
            return self.health.health_level
        if self.status == TableAvailabilityStatus.FAILED:
            return TableHealthLevel.CRITICAL
        if self.status == TableAvailabilityStatus.PARTIAL:
            return TableHealthLevel.WARNING
        if self.status == TableAvailabilityStatus.AVAILABLE:
            return TableHealthLevel.HEALTHY
        return TableHealthLevel.UNKNOWN


class TableAvailabilityRef(BaseModel):
    """Lightweight reference for table list responses."""

    table_id: str
    table_name: str
    status: TableAvailabilityStatus
    health_level: TableHealthLevel
    row_count: int | None = None
    column_count: int | None = None
    error_count: int = 0
    completed_at: datetime | None = None


class TableStatusReport(BaseModel):
    """Complete status report for all tables in a job.

    This is the top-level contract for the table availability API endpoint.
    """

    job_id: str
    stage_id: str
    report_generated_at: datetime
    tables: list[TableAvailability] = Field(default_factory=list)

    # Summary stats
    total_tables: int = Field(0, ge=0)
    tables_available: int = Field(0, ge=0)
    tables_partial: int = Field(0, ge=0)
    tables_failed: int = Field(0, ge=0)
    tables_pending: int = Field(0, ge=0)
    tables_parsing: int = Field(0, ge=0)

    # Overall metrics
    total_rows: int = Field(0, ge=0)
    total_columns: int = Field(0, ge=0)
    total_errors: int = Field(0, ge=0)
    total_warnings: int = Field(0, ge=0)

    @property
    def overall_health(self) -> TableHealthLevel:
        """Calculate overall health across all tables."""
        if self.tables_failed > 0:
            return TableHealthLevel.CRITICAL
        if self.tables_partial > 0 or self.total_warnings > 0:
            return TableHealthLevel.WARNING
        if self.tables_available == self.total_tables and self.total_tables > 0:
            return TableHealthLevel.HEALTHY
        return TableHealthLevel.UNKNOWN

    @property
    def completion_pct(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_tables == 0:
            return 0.0
        completed = self.tables_available + self.tables_partial + self.tables_failed
        return (completed / self.total_tables) * 100


class TableHealthCheck(BaseModel):
    """Request/response for a table health check.

    Used to trigger recalculation of health metrics for specific tables.
    """

    table_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Table IDs to check",
    )
    force_refresh: bool = Field(
        False,
        description="Force recalculation even if recent check exists",
    )
    include_column_stats: bool = Field(
        True,
        description="Include detailed per-column statistics",
    )


class TableHealthCheckResult(BaseModel):
    """Result of a health check operation."""

    table_id: str
    previous_health: TableHealthLevel | None
    current_health: TableHealthLevel
    health_changed: bool
    check_duration_ms: float
    health_metrics: TableHealth | None = None
    issues_found: list[str] = Field(default_factory=list)


class TableStatusUpdateRequest(BaseModel):
    """Request to update table status (internal use by DAT)."""

    table_id: str
    status: TableAvailabilityStatus
    progress_pct: float | None = Field(None, ge=0.0, le=100.0)
    progress_message: str | None = None
    row_count: int | None = Field(None, ge=0)
    column_count: int | None = Field(None, ge=0)
    columns: list[str] | None = None
    error: TableParseError | None = None
