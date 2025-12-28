"""DAT (Data Aggregation Tool) contracts.

This package contains Pydantic models for DAT-specific data structures:
- Stage contracts for the 8-stage pipeline (per ADR-0001-DAT)
- Extraction profiles for domain-agnostic configuration
- Table availability status tracking
- Cancellation and cleanup semantics

All contracts are domain-agnostic; user-specific knowledge (column mappings,
aggregation rules, file patterns) is injected via profiles and configs.
"""

from shared.contracts.dat.profile import (
    AggregationRule,
    ColumnMapping,
    ExtractionProfile,
    ExtractionProfileRef,
    FilePattern,
    ProfileValidationResult,
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
    # Stage contracts
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
    # Profile contracts
    "ExtractionProfile",
    "ExtractionProfileRef",
    "ColumnMapping",
    "AggregationRule",
    "FilePattern",
    "ProfileValidationResult",
    # Table status contracts
    "TableAvailability",
    "TableAvailabilityStatus",
    "TableStatusReport",
    "TableHealthCheck",
    # Cancellation contracts
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
