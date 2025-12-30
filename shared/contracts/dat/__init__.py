"""DAT (Data Aggregation Tool) contracts.

Per ADR-0004: 8-stage pipeline with lockable artifacts.
Per ADR-0012: Profile-driven extraction with AdapterFactory pattern.
Per ADR-0014: Cancellation semantics with checkpoint preservation.
Per ADR-0041: Large file streaming with 10MB threshold.

This package contains Pydantic models for DAT-specific data structures:
- Stage contracts for the 8-stage pipeline (per ADR-0004)
- Adapter contracts for extensible file parsing (per ADR-0012)
- Extraction profiles for domain-agnostic configuration
- Table availability status tracking (per ADR-0008)
- Cancellation and cleanup semantics (per ADR-0014)
- Background job contracts for large files (per ADR-0041)

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
    AggregationConfig,
    ContextConfig,
    ContextDefaults,
    DATProfile,
    GovernanceConfig,
    JoinOutputConfig,
    LevelConfig,
    OutputConfig,
    ProfileValidationResult,
    RepeatOverConfig,
    SelectConfig,
    StrategyType,
    TableConfig,
    UIConfig,
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
from shared.contracts.dat.stage_graph import (
    CascadeRule,
    GatingRule,
    StageDefinition,
    StageGraphConfig,
)

__version__ = "1.0.0"

__all__ = [
    # Adapter contracts (per ADR-0012, ADR-0041)
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
    # Jobs contracts (per ADR-0041)
    "BackgroundJob",
    "JobListResponse",
    "JobProgress",
    "JobQueueStatus",
    "JobResult",
    "JobStatus",
    "JobSubmission",
    "JobType",
    # Stage contracts (per ADR-0004)
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
    # Profile contracts (per ADR-0012)
    "AggregationConfig",
    "ContextConfig",
    "ContextDefaults",
    "DATProfile",
    "GovernanceConfig",
    "JoinOutputConfig",
    "LevelConfig",
    "OutputConfig",
    "ProfileValidationResult",
    "RepeatOverConfig",
    "SelectConfig",
    "StrategyType",
    "TableConfig",
    "UIConfig",
    # Table status contracts (per ADR-0008)
    "TableAvailability",
    "TableAvailabilityStatus",
    "TableStatusReport",
    "TableHealthCheck",
    # Cancellation contracts (per ADR-0014)
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
    # Stage graph contracts (per ADR-0004)
    "CascadeRule",
    "GatingRule",
    "StageDefinition",
    "StageGraphConfig",
]
