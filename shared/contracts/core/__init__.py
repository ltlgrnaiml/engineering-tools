"""Core contracts shared across all tools.

Per ADR-0010: Pydantic contracts are Tier 0, single source of truth.

This package exports all core platform contracts used across tools.
"""

from shared.contracts.core.artifact_registry import (
    ArtifactQuery,
    ArtifactRecord,
    ArtifactState,
    ArtifactStats,
    ArtifactType,
)
from shared.contracts.core.audit import (
    AuditTimestamp,
    AuditTrail,
    LifecycleEvent,
    TimestampMixin,
    now_utc,
    to_iso8601,
)
from shared.contracts.core.concurrency import (
    BatchResult,
    ConcurrencyConfig,
    ConcurrencyTier,
    OSType,
    PlatformInfo,
    ShellType,
    TaskResult,
    get_platform_info,
)
from shared.contracts.core.dataset import (
    ColumnMeta,
    DataSetManifest,
    DataSetPreview,
    DataSetRef,
)
from shared.contracts.core.frontend_logging import (
    DebugPanelConfig,
    FrontendAPICall,
    FrontendDebugExport,
    FrontendLogCategory,
    FrontendLogEntry,
    FrontendLogLevel,
    FrontendStateTransition,
)
from shared.contracts.core.id_generator import (
    AggregateStageInputs,
    ArtifactIDRequest,
    ArtifactIDResult,
    ContextStageInputs,
    ExportStageInputs,
    IDAlgorithm,
    IDConfig,
    IDGenerationRequest,
    IDGenerationResult,
    IDValidationRequest,
    IDValidationResult,
    ParseStageInputs,
    PreviewStageInputs,
    StageIDInputs,
    TransformStageInputs,
    UploadStageInputs,
    ValidateStageInputs,
    compute_content_hash,
    compute_deterministic_id,
    verify_id_determinism,
)
from shared.contracts.core.logging import (
    ArtifactLog,
    FSMTransitionLog,
    LogEvent,
    LogLevel,
    RequestContext,
    StateSnapshot,
    TraceQuery,
    TraceResult,
)
from shared.contracts.core.path_safety import (
    PathSafetyConfig,
    PathValidationError,
    RelativePath,
    WorkspacePath,
    is_safe_relative_path,
    make_relative,
    normalize_path,
)
from shared.contracts.core.pipeline import (
    CreatePipelineRequest,
    Pipeline,
    PipelineRef,
    PipelineStep,
    PipelineStepState,
    PipelineStepType,
)
from shared.contracts.core.rendering import (
    ChartSpec,
    ChartType,
    ColorPalette,
    DataSeries,
    ImageSpec,
    OutputFormat,
    OutputTarget,
    RenderRequest,
    RenderResult,
    RenderSpec,
    RenderState,
    RenderStyle,
    TableSpec,
    TextSpec,
)

__version__ = "0.1.0"

__all__ = [
    # Artifact Registry
    "ArtifactRecord",
    "ArtifactType",
    "ArtifactQuery",
    "ArtifactState",
    "ArtifactStats",
    # Audit Trail
    "AuditTimestamp",
    "AuditTrail",
    "LifecycleEvent",
    "TimestampMixin",
    "now_utc",
    "to_iso8601",
    # Concurrency
    "ConcurrencyConfig",
    "ConcurrencyTier",
    "OSType",
    "PlatformInfo",
    "ShellType",
    "TaskResult",
    "BatchResult",
    "get_platform_info",
    # DataSet
    "ColumnMeta",
    "DataSetManifest",
    "DataSetRef",
    "DataSetPreview",
    # ID Generator
    "IDAlgorithm",
    "IDConfig",
    "IDGenerationRequest",
    "IDGenerationResult",
    "StageIDInputs",
    "UploadStageInputs",
    "ContextStageInputs",
    "PreviewStageInputs",
    "ParseStageInputs",
    "AggregateStageInputs",
    "TransformStageInputs",
    "ValidateStageInputs",
    "ExportStageInputs",
    "ArtifactIDRequest",
    "ArtifactIDResult",
    "IDValidationRequest",
    "IDValidationResult",
    "compute_deterministic_id",
    "compute_content_hash",
    "verify_id_determinism",
    # Path Safety
    "PathValidationError",
    "RelativePath",
    "WorkspacePath",
    "PathSafetyConfig",
    "normalize_path",
    "is_safe_relative_path",
    "make_relative",
    # Pipeline
    "Pipeline",
    "PipelineStep",
    "PipelineStepState",
    "PipelineStepType",
    "PipelineRef",
    "CreatePipelineRequest",
    # Rendering
    "ChartSpec",
    "ChartType",
    "ColorPalette",
    "DataSeries",
    "OutputFormat",
    "OutputTarget",
    "RenderRequest",
    "RenderResult",
    "RenderSpec",
    "RenderState",
    "RenderStyle",
    "TableSpec",
    "TextSpec",
    "ImageSpec",
    # Logging (Backend)
    "LogLevel",
    "RequestContext",
    "LogEvent",
    "StateSnapshot",
    "FSMTransitionLog",
    "ArtifactLog",
    "TraceQuery",
    "TraceResult",
    # Frontend Logging
    "FrontendLogLevel",
    "FrontendLogCategory",
    "FrontendLogEntry",
    "FrontendAPICall",
    "FrontendStateTransition",
    "FrontendDebugExport",
    "DebugPanelConfig",
]
