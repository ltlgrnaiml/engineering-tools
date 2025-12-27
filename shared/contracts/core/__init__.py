"""Core contracts shared across all tools.

Per ADR-0009: Pydantic contracts are Tier 0, single source of truth.

This package exports all core platform contracts used across tools.
"""

from shared.contracts.core.artifact_registry import (
    ArtifactRecord,
    ArtifactType,
    ArtifactQuery,
    ArtifactState,
    ArtifactStats,
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
    ConcurrencyConfig,
    ConcurrencyTier,
    OSType,
    PlatformInfo,
    ShellType,
    TaskResult,
    BatchResult,
    get_platform_info,
)
from shared.contracts.core.dataset import (
    ColumnMeta,
    DataSetManifest,
    DataSetRef,
    DataSetPreview,
)
from shared.contracts.core.id_generator import (
    IDAlgorithm,
    IDConfig,
    IDGenerationRequest,
    IDGenerationResult,
    StageIDInputs,
    UploadStageInputs,
    ContextStageInputs,
    PreviewStageInputs,
    ParseStageInputs,
    AggregateStageInputs,
    TransformStageInputs,
    ValidateStageInputs,
    ExportStageInputs,
    ArtifactIDRequest,
    ArtifactIDResult,
    IDValidationRequest,
    IDValidationResult,
    compute_deterministic_id,
    compute_content_hash,
    verify_id_determinism,
)
from shared.contracts.core.path_safety import (
    PathValidationError,
    RelativePath,
    WorkspacePath,
    PathSafetyConfig,
    normalize_path,
    is_safe_relative_path,
    make_relative,
)
from shared.contracts.core.pipeline import (
    Pipeline,
    PipelineStep,
    PipelineStepState,
    PipelineStepType,
    PipelineRef,
    CreatePipelineRequest,
)
from shared.contracts.core.rendering import (
    ChartSpec,
    ChartType,
    ColorPalette,
    DataSeries,
    OutputFormat,
    OutputTarget,
    RenderRequest,
    RenderResult,
    RenderSpec,
    RenderState,
    RenderStyle,
    TableSpec,
    TextSpec,
    ImageSpec,
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
]
