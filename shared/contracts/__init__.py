"""Tier 0: Pydantic contracts - single source of truth for all data structures.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0016: 3-Tier Document Model (Contracts are Tier 0).

Contracts defined here are:
- The canonical schema for all API payloads
- Auto-exported to JSON Schema via tools/gen_json_schema.py
- Used to generate OpenAPI specs via FastAPI
- Never duplicated in ADRs, Specs, or Guides (reference only)

Package Structure:
- core/: Platform-wide contracts (datasets, pipelines, audit, etc.)
- dat/: Data Aggregator Tool contracts
- pptx/: PowerPoint Generator contracts
- sov/: SOV Analyzer contracts
- messages/: Message catalog contracts
- devtools/: Developer utilities contracts
"""

__version__ = "0.1.0"

# Core contracts - most commonly used
from shared.contracts.core.dataset import (
    ColumnMeta,
    DataSetManifest,
    DataSetRef,
    DataSetPreview,
)
from shared.contracts.core.pipeline import (
    Pipeline,
    PipelineStep,
    PipelineStepState,
    PipelineStepType,
    PipelineRef,
    CreatePipelineRequest,
)
from shared.contracts.core.artifact_registry import (
    ArtifactRecord,
    ArtifactType,
    ArtifactState,
    ArtifactQuery,
)
from shared.contracts.core.audit import (
    AuditTimestamp,
    AuditTrail,
    LifecycleEvent,
    TimestampMixin,
)
from shared.contracts.core.id_generator import (
    compute_deterministic_id,
    compute_content_hash,
    verify_id_determinism,
    IDConfig,
)
from shared.contracts.core.idempotency import (
    IdempotencyKey,
    IdempotencyRecord,
    IdempotencyStatus,
    IdempotencyConfig,
    IdempotencyCheck,
    IdempotencyConflict,
)
from shared.contracts.core.logging import (
    LogEvent,
    LogLevel,
    RequestContext,
    StateSnapshot,
    FSMTransitionLog,
    ArtifactLog,
    TraceQuery,
    TraceResult,
)
from shared.contracts.core.dataset import (
    VersionRecord,
    LineageRecord,
    LineageGraph,
)

__all__ = [
    # Version
    "__version__",
    # Dataset
    "ColumnMeta",
    "DataSetManifest",
    "DataSetRef",
    "DataSetPreview",
    "VersionRecord",
    "LineageRecord",
    "LineageGraph",
    # Pipeline
    "Pipeline",
    "PipelineStep",
    "PipelineStepState",
    "PipelineStepType",
    "PipelineRef",
    "CreatePipelineRequest",
    # Registry
    "ArtifactRecord",
    "ArtifactType",
    "ArtifactState",
    "ArtifactQuery",
    # Audit
    "AuditTimestamp",
    "AuditTrail",
    "LifecycleEvent",
    "TimestampMixin",
    # ID Generation
    "compute_deterministic_id",
    "compute_content_hash",
    "verify_id_determinism",
    "IDConfig",
    # Idempotency
    "IdempotencyKey",
    "IdempotencyRecord",
    "IdempotencyStatus",
    "IdempotencyConfig",
    "IdempotencyCheck",
    "IdempotencyConflict",
    # Logging/Observability
    "LogEvent",
    "LogLevel",
    "RequestContext",
    "StateSnapshot",
    "FSMTransitionLog",
    "ArtifactLog",
    "TraceQuery",
    "TraceResult",
]
