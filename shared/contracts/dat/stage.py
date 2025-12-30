"""DAT Stage contracts - pipeline stage state machine and configuration.

Per ADR-0001-DAT: 8-stage pipeline with lockable artifacts.
Per ADR-0003: Context and Preview are optional stages.
Per ADR-0004-DAT: Stage IDs are deterministic (hash of inputs + config).
Per ADR-0008: All timestamps are ISO-8601 UTC (no microseconds).
Per ADR-0013: Cancellation preserves completed/checkpointed artifacts.
Per ADR-0006: Table availability tracked per stage.

This module defines the state machine for DAT's 8-stage pipeline:
  Discovery → Selection → Context → Table Availability →
  Table Selection → Preview → Parse → Export

Each stage is idempotent: re-running with same inputs produces same outputs.
Domain-specific logic is injected via DATProfile, not hardcoded here.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "1.0.0"


class DATStageType(str, Enum):
    """The eight stages of the DAT pipeline.

    Per ADR-0001-DAT: 8-stage pipeline with lockable artifacts.
    Per ADR-0003: Context and Preview are optional stages.

    Stage order:
        1. DISCOVERY - Automatic file system scan (implicit)
        2. SELECTION - User selects files to include
        3. CONTEXT - Optional context hints and metadata
        4. TABLE_AVAILABILITY - Detect available tables in files
        5. TABLE_SELECTION - User selects tables to extract
        6. PREVIEW - Optional preview of extraction results
        7. PARSE - Execute full extraction
        8. EXPORT - Generate deliverables from parse artifacts
    """

    DISCOVERY = "discovery"
    SELECTION = "selection"
    CONTEXT = "context"
    TABLE_AVAILABILITY = "table_availability"
    TABLE_SELECTION = "table_selection"
    PREVIEW = "preview"
    PARSE = "parse"
    EXPORT = "export"

    @classmethod
    def optional_stages(cls) -> set["DATStageType"]:
        """Return stages that can be skipped per ADR-0003."""
        return {cls.CONTEXT, cls.PREVIEW}

    @classmethod
    def is_optional(cls, stage: "DATStageType") -> bool:
        """Check if a stage is optional."""
        return stage in cls.optional_stages()

    @classmethod
    def get_order(cls) -> list["DATStageType"]:
        """Return stages in pipeline order."""
        return [
            cls.DISCOVERY,
            cls.SELECTION,
            cls.CONTEXT,
            cls.TABLE_AVAILABILITY,
            cls.TABLE_SELECTION,
            cls.PREVIEW,
            cls.PARSE,
            cls.EXPORT,
        ]


class DATStageState(str, Enum):
    """State machine for a DAT stage.

    State transitions:
        pending → running → completed
        pending → running → failed
        pending → running → cancelled
        completed → locked
        locked → unlocked → running (re-run)

    Per ADR-0002: Unlocking preserves previous artifacts with timestamp suffix.
    Per ADR-0014: Cancellation preserves partial outputs.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LOCKED = "locked"
    UNLOCKED = "unlocked"

    @classmethod
    def terminal_states(cls) -> set["DATStageState"]:
        """States from which no automatic transitions occur."""
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED, cls.LOCKED}

    @classmethod
    def can_transition_to(cls, from_state: "DATStageState", to_state: "DATStageState") -> bool:
        """Validate state transition is allowed."""
        allowed = {
            cls.PENDING: {cls.RUNNING},
            cls.RUNNING: {cls.COMPLETED, cls.FAILED, cls.CANCELLED},
            cls.COMPLETED: {cls.LOCKED},
            cls.FAILED: {cls.PENDING},  # Allow retry
            cls.CANCELLED: {cls.PENDING},  # Allow retry
            cls.LOCKED: {cls.UNLOCKED},
            cls.UNLOCKED: {cls.RUNNING, cls.LOCKED},
        }
        return to_state in allowed.get(from_state, set())


class ParseStageConfig(BaseModel):
    """Configuration for the Parse stage.

    The Parse stage reads raw files and extracts structured data.
    All domain-specific logic (file patterns, column mappings) comes from
    the DATProfile, not from this config.
    """

    profile_id: str = Field(
        ...,
        description="DATProfile ID defining parsing rules",
    )
    source_paths: list[str] = Field(
        ...,
        min_length=1,
        description="Relative paths to source files/directories to parse",
    )
    recursive: bool = Field(
        True,
        description="Recursively search directories for matching files",
    )
    max_files: int | None = Field(
        None,
        ge=1,
        description="Maximum number of files to parse (None = no limit)",
    )
    fail_fast: bool = Field(
        False,
        description="Stop on first file error vs collect all errors",
    )
    encoding: str = Field(
        "utf-8",
        description="Default file encoding (profile can override per-pattern)",
    )

    @field_validator("source_paths")
    @classmethod
    def validate_relative_paths(cls, v: list[str]) -> list[str]:
        """Ensure all paths are relative (per ADR-0017 path-safety)."""
        for path in v:
            if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
                raise ValueError(f"Absolute paths not allowed: {path}")
            if ".." in path.split("/"):
                raise ValueError(f"Path traversal not allowed: {path}")
        return v


class DiscoveryStageConfig(BaseModel):
    """Configuration for the Discovery stage.

    Per ADR-0001-DAT: Discovery is the first stage, performing file system scan.
    Automatically discovers files matching patterns in the specified paths.
    """

    root_paths: list[str] = Field(
        ...,
        min_length=1,
        description="Relative paths to scan for files",
    )
    recursive: bool = Field(
        True,
        description="Recursively search directories",
    )
    include_patterns: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Glob patterns for files to include",
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Glob patterns for files to exclude",
    )
    max_files: int | None = Field(
        None,
        ge=1,
        description="Maximum files to discover (None = no limit)",
    )

    @field_validator("root_paths")
    @classmethod
    def validate_relative_paths(cls, v: list[str]) -> list[str]:
        """Ensure all paths are relative (per ADR-0017 path-safety)."""
        for path in v:
            if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
                raise ValueError(f"Absolute paths not allowed: {path}")
            if ".." in path.split("/"):
                raise ValueError(f"Path traversal not allowed: {path}")
        return v


class SelectionStageConfig(BaseModel):
    """Configuration for the Selection stage.

    Per ADR-0001-DAT: User selects which discovered files to include.
    """

    discovery_stage_id: str = Field(
        ...,
        description="Stage ID of completed Discovery stage",
    )
    selected_files: list[str] = Field(
        ...,
        min_length=1,
        description="Relative paths of files selected for processing",
    )
    deselected_files: list[str] = Field(
        default_factory=list,
        description="Files explicitly excluded by user",
    )


class ContextStageConfig(BaseModel):
    """Configuration for the Context stage.

    Per ADR-0003: Context is optional, providing hints and metadata.
    Skipping uses lazy initialization with defaults.
    """

    selection_stage_id: str = Field(
        ...,
        description="Stage ID of completed Selection stage",
    )
    context_hints: dict[str, Any] = Field(
        default_factory=dict,
        description="User-provided context hints for extraction",
    )
    metadata_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Override auto-detected metadata values",
    )
    profile_id: str | None = Field(
        None,
        description="Optional profile ID to use (None = auto-detect)",
    )


class TableAvailabilityStageConfig(BaseModel):
    """Configuration for the Table Availability stage.

    Per ADR-0006: Probes files to detect available tables.
    Status check must complete in < 1 second per table.
    """

    selection_stage_id: str = Field(
        ...,
        description="Stage ID of completed Selection stage",
    )
    profile_id: str = Field(
        ...,
        description="Profile defining expected table structures",
    )
    probe_row_limit: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Max rows to probe for schema detection",
    )
    timeout_ms: int = Field(
        5000,
        ge=100,
        description="Timeout per file probe in milliseconds",
    )


class TableSelectionStageConfig(BaseModel):
    """Configuration for the Table Selection stage.

    Per ADR-0001-DAT: User selects which detected tables to extract.
    """

    table_availability_stage_id: str = Field(
        ...,
        description="Stage ID of completed Table Availability stage",
    )
    selected_tables: list[str] = Field(
        ...,
        min_length=1,
        description="Table identifiers selected for extraction",
    )
    column_selections: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Per-table column selections (empty = all columns)",
    )


class PreviewStageConfig(BaseModel):
    """Configuration for the Preview stage.

    Per ADR-0003: Preview is optional, showing sample extraction results.
    Per ADR-0040: Uses sampled preview for large files.
    """

    table_selection_stage_id: str = Field(
        ...,
        description="Stage ID of completed Table Selection stage",
    )
    preview_row_limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Max rows to preview per table",
    )
    include_statistics: bool = Field(
        True,
        description="Include column statistics in preview",
    )


class ExportStageConfig(BaseModel):
    """Configuration for the Export stage.

    Per ADR-0014: Export writes parsed data to user-selected formats.
    Supports multiple output formats in a single export.
    """

    parse_stage_id: str = Field(
        ...,
        description="Stage ID of completed Parse stage to export",
    )
    output_formats: list[Literal["parquet", "csv", "excel", "json"]] = Field(
        default=["parquet"],
        min_length=1,
        description="Output format(s) to generate",
    )
    output_path: str = Field(
        ...,
        description="Relative path for output file (extension auto-added)",
    )
    compression: Literal["none", "gzip", "snappy", "zstd"] | None = Field(
        "snappy",
        description="Compression for Parquet output",
    )
    csv_delimiter: str = Field(
        ",",
        max_length=1,
        description="Delimiter for CSV output",
    )
    excel_sheet_name: str = Field(
        "Data",
        max_length=31,
        description="Sheet name for Excel output",
    )
    include_manifest: bool = Field(
        True,
        description="Generate manifest.json alongside data files",
    )

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, v: str) -> str:
        """Ensure output path is relative and safe."""
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"Absolute paths not allowed: {v}")
        if ".." in v.split("/"):
            raise ValueError(f"Path traversal not allowed: {v}")
        return v


class DATStageConfig(BaseModel):
    """Union config for any DAT stage type.

    Per ADR-0001-DAT: Exactly one stage-specific config must be set.
    """

    stage_type: DATStageType
    discovery_config: DiscoveryStageConfig | None = None
    selection_config: SelectionStageConfig | None = None
    context_config: ContextStageConfig | None = None
    table_availability_config: TableAvailabilityStageConfig | None = None
    table_selection_config: TableSelectionStageConfig | None = None
    preview_config: PreviewStageConfig | None = None
    parse_config: ParseStageConfig | None = None
    export_config: ExportStageConfig | None = None

    @model_validator(mode="after")
    def validate_config_matches_type(self) -> "DATStageConfig":
        """Ensure the config matches the stage type."""
        config_map = {
            DATStageType.DISCOVERY: self.discovery_config,
            DATStageType.SELECTION: self.selection_config,
            DATStageType.CONTEXT: self.context_config,
            DATStageType.TABLE_AVAILABILITY: self.table_availability_config,
            DATStageType.TABLE_SELECTION: self.table_selection_config,
            DATStageType.PREVIEW: self.preview_config,
            DATStageType.PARSE: self.parse_config,
            DATStageType.EXPORT: self.export_config,
        }
        expected_config = config_map[self.stage_type]
        if expected_config is None:
            raise ValueError(f"Missing config for stage type {self.stage_type}")

        # Ensure other configs are None
        for st, cfg in config_map.items():
            if st != self.stage_type and cfg is not None:
                raise ValueError(f"Unexpected {st} config for {self.stage_type} stage")

        return self


class StageMetrics(BaseModel):
    """Performance and quality metrics for a completed stage."""

    duration_ms: float = Field(..., ge=0)
    input_file_count: int = Field(0, ge=0)
    output_row_count: int = Field(0, ge=0)
    output_column_count: int = Field(0, ge=0)
    output_size_bytes: int = Field(0, ge=0)
    error_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)
    skipped_file_count: int = Field(0, ge=0)


class StageError(BaseModel):
    """Detailed error information for a failed stage."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    file_path: str | None = Field(None, description="File that caused error, if applicable")
    line_number: int | None = Field(None, description="Line number, if applicable")
    details: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = Field(
        False,
        description="True if error can be recovered by retrying",
    )


class DATStageResult(BaseModel):
    """Result of executing a DAT stage.

    Contains state, timing, metrics, and output references.
    Per ADR-0004: stage_id is deterministic hash of inputs + config.
    """

    # Identity
    stage_id: str = Field(
        ...,
        description="Deterministic hash of stage inputs + config",
    )
    stage_type: DATStageType
    job_id: str = Field(
        ...,
        description="Parent job ID this stage belongs to",
    )

    # State
    state: DATStageState = DATStageState.PENDING

    # Timestamps (per ADR-0008)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None
    cancelled_at: datetime | None = None

    # Configuration (immutable after creation)
    config: DATStageConfig

    # Outputs (populated on completion)
    output_dataset_id: str | None = Field(
        None,
        description="DataSet ID produced by this stage",
    )
    output_paths: list[str] = Field(
        default_factory=list,
        description="Relative paths to output files",
    )

    # Metrics and errors
    metrics: StageMetrics | None = None
    errors: list[StageError] = Field(default_factory=list)

    # Progress (for long-running stages)
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    progress_message: str | None = None

    # Lineage
    input_stage_ids: list[str] = Field(
        default_factory=list,
        description="Stage IDs this stage depends on",
    )

    def can_start(self) -> bool:
        """Check if stage can transition to RUNNING."""
        return self.state in {DATStageState.PENDING, DATStageState.UNLOCKED}

    def can_lock(self) -> bool:
        """Check if stage can be locked."""
        return self.state == DATStageState.COMPLETED

    def can_unlock(self) -> bool:
        """Check if stage can be unlocked."""
        return self.state == DATStageState.LOCKED

    def is_terminal(self) -> bool:
        """Check if stage is in a terminal state."""
        return self.state in DATStageState.terminal_states()


class DATStageRef(BaseModel):
    """Lightweight reference to a DAT stage for list responses."""

    stage_id: str
    stage_type: DATStageType
    job_id: str
    state: DATStageState
    progress_pct: float
    created_at: datetime
    completed_at: datetime | None = None
    error_count: int = 0
