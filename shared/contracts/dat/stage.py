"""DAT Stage contracts - pipeline stage state machine and configuration.

Per ADR-0004: Stage IDs are deterministic (hash of inputs + config).
Per ADR-0008: All timestamps are ISO-8601 UTC (no microseconds).
Per ADR-0014: Cancellation preserves partial artifacts.
Per ADR-0006: Table availability tracked per stage.

This module defines the state machine for DAT's three-stage pipeline:
  Parse → Aggregate → Export

Each stage is idempotent: re-running with same inputs produces same outputs.
Domain-specific logic is injected via ExtractionProfile, not hardcoded here.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


class DATStageType(str, Enum):
    """The three stages of the DAT pipeline."""

    PARSE = "parse"
    AGGREGATE = "aggregate"
    EXPORT = "export"


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
    the ExtractionProfile, not from this config.
    """

    profile_id: str = Field(
        ...,
        description="ExtractionProfile ID defining parsing rules",
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


class AggregateStageConfig(BaseModel):
    """Configuration for the Aggregate stage.

    The Aggregate stage combines parsed data according to aggregation rules
    defined in the ExtractionProfile. This config specifies which parsed
    outputs to aggregate and any runtime overrides.
    """

    profile_id: str = Field(
        ...,
        description="ExtractionProfile ID defining aggregation rules",
    )
    input_stage_id: str = Field(
        ...,
        description="Stage ID of completed Parse stage to aggregate",
    )
    aggregation_levels: list[str] | None = Field(
        None,
        description="Override profile's default aggregation hierarchy",
    )
    include_columns: list[str] | None = Field(
        None,
        description="Whitelist of columns to include (None = all)",
    )
    exclude_columns: list[str] | None = Field(
        None,
        description="Blacklist of columns to exclude",
    )
    deterministic_seed: int = Field(
        42,
        description="Seed for any randomized operations (per ADR-0004)",
    )

    @model_validator(mode="after")
    def validate_column_filters(self) -> "AggregateStageConfig":
        """Ensure include and exclude lists don't overlap."""
        if self.include_columns and self.exclude_columns:
            overlap = set(self.include_columns) & set(self.exclude_columns)
            if overlap:
                raise ValueError(f"Columns in both include and exclude: {overlap}")
        return self


class ExportStageConfig(BaseModel):
    """Configuration for the Export stage.

    The Export stage writes aggregated data to output formats.
    Supports multiple output formats in a single export.
    """

    input_stage_id: str = Field(
        ...,
        description="Stage ID of completed Aggregate stage to export",
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

    Exactly one of parse_config, aggregate_config, or export_config must be set.
    """

    stage_type: DATStageType
    parse_config: ParseStageConfig | None = None
    aggregate_config: AggregateStageConfig | None = None
    export_config: ExportStageConfig | None = None

    @model_validator(mode="after")
    def validate_config_matches_type(self) -> "DATStageConfig":
        """Ensure the config matches the stage type."""
        config_map = {
            DATStageType.PARSE: self.parse_config,
            DATStageType.AGGREGATE: self.aggregate_config,
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
