"""DAT (Data Aggregation Tool) contracts.

Per ADR-0001-DAT: 8-stage pipeline with lockable artifacts.
Per ADR-0011: Profile-driven extraction with AdapterFactory pattern.
Per ADR-0013: Cancellation semantics with checkpoint preservation.
Per ADR-0040: Large file streaming with 10MB threshold.

This package contains Pydantic models for DAT-specific data structures:
- Stage contracts for the 8-stage pipeline (per ADR-0001-DAT)
- Adapter contracts for extensible file parsing (per ADR-0011)
- Extraction profiles for domain-agnostic configuration
- Table availability status tracking (per ADR-0006)
- Cancellation and cleanup semantics (per ADR-0013)
- Background job contracts for large files (per ADR-0040)

All contracts are domain-agnostic; user-specific knowledge (column mappings,
aggregation rules, file patterns) is injected via profiles and configs.
"""

from shared.contracts.dat.adapter import (
    AdapterCapabilities,
    AdapterError,
    AdapterErrorCode,
    AdapterMetadata,
    AdapterRegistryEntry,
    AdapterRegistryState,
    BaseFileAdapter,
    ColumnInfo,
    CompressionType,
    FileValidationResult,
    InferredDataType,
    ReadOptions,
    ReadResult,
    SchemaProbeResult,
    SheetInfo,
    StreamChunk,
    StreamOptions,
    ValidationIssue,
    ValidationSeverity,
)
from shared.contracts.dat.jobs import (
    BackgroundJob,
    JobListResponse,
    JobProgress,
    JobQueueStatus,
    JobResult,
    JobStatus,
    JobSubmission,
    JobType,
)
from shared.contracts.dat.profile import (
    AggregationFunction,
    AggregationLevel,
    AggregationRule,
    ColumnDataType,
    ColumnMapping,
    CreateProfileRequest,
    ExtractionProfile,
    ExtractionProfileRef,
    FilePattern,
    FilePatternType,
    ProfileValidationResult,
    UpdateProfileRequest,
    ValidationRule,
    ValidationSeverity as ProfileValidationSeverity,
)
from shared.contracts.dat.stage import (
    DATStageConfig,
    DATStageResult,
    DATStageState,
    DATStageType,
    DiscoveryStageConfig,
    SelectionStageConfig,
    ContextStageConfig,
    TableAvailabilityStageConfig,
    TableSelectionStageConfig,
    PreviewStageConfig,
    ParseStageConfig,
    ExportStageConfig,
)
from shared.contracts.dat.table_status import (
    TableAvailability,
    TableAvailabilityStatus,
    TableStatusReport,
    TableHealthCheck,
)
from shared.contracts.dat.cancellation import (
    CancellationReason,
    CancellationState,
    CancellationRequest,
    CancellationResult,
    CleanupState,
    CleanupTarget,
    CleanupRequest,
    CleanupResult,
    Checkpoint,
    CheckpointType,
    CheckpointRegistry,
    CancellableOperation,
    CancellableOperationState,
    CancellationAuditEntry,
    CancellationAuditLog,
)

__version__ = "1.0.0"

__all__ = [
    # Adapter contracts (per ADR-0011, ADR-0040)
    "AdapterCapabilities",
    "AdapterError",
    "AdapterErrorCode",
    "AdapterMetadata",
    "AdapterRegistryEntry",
    "AdapterRegistryState",
    "BaseFileAdapter",
    "ColumnInfo",
    "CompressionType",
    "FileValidationResult",
    "InferredDataType",
    "ReadOptions",
    "ReadResult",
    "SchemaProbeResult",
    "SheetInfo",
    "StreamChunk",
    "StreamOptions",
    "ValidationIssue",
    "ValidationSeverity",
    # Jobs contracts (per ADR-0040)
    "BackgroundJob",
    "JobListResponse",
    "JobProgress",
    "JobQueueStatus",
    "JobResult",
    "JobStatus",
    "JobSubmission",
    "JobType",
    # Stage contracts (per ADR-0001-DAT)
    "DATStageType",
    "DATStageState",
    "DATStageConfig",
    "DATStageResult",
    "DiscoveryStageConfig",
    "SelectionStageConfig",
    "ContextStageConfig",
    "TableAvailabilityStageConfig",
    "TableSelectionStageConfig",
    "PreviewStageConfig",
    "ParseStageConfig",
    "ExportStageConfig",
    # Profile contracts (per ADR-0011)
    "AggregationFunction",
    "AggregationLevel",
    "AggregationRule",
    "ColumnDataType",
    "ColumnMapping",
    "CreateProfileRequest",
    "ExtractionProfile",
    "ExtractionProfileRef",
    "FilePattern",
    "FilePatternType",
    "ProfileValidationResult",
    "ProfileValidationSeverity",
    "UpdateProfileRequest",
    "ValidationRule",
    # Table status contracts (per ADR-0006)
    "TableAvailability",
    "TableAvailabilityStatus",
    "TableStatusReport",
    "TableHealthCheck",
    # Cancellation contracts (per ADR-0013)
    "CancellationReason",
    "CancellationState",
    "CancellationRequest",
    "CancellationResult",
    "CleanupState",
    "CleanupTarget",
    "CleanupRequest",
    "CleanupResult",
    "Checkpoint",
    "CheckpointType",
    "CheckpointRegistry",
    "CancellableOperation",
    "CancellableOperationState",
    "CancellationAuditEntry",
    "CancellationAuditLog",
]
