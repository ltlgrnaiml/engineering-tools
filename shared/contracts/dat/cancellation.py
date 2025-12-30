"""DAT Cancellation semantics contracts.

Per ADR-0014: Cancellation Semantics for Parse & Export.

This module defines contracts for cancellation behavior including:
- Soft cancellation with artifact preservation
- Checkpointing for data integrity
- Explicit cleanup operations
- Audit trail for cancellation events
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


# =============================================================================
# Cancellation States and Types
# =============================================================================


class CancellationReason(str, Enum):
    """Reasons for cancellation."""

    USER_REQUESTED = "user_requested"
    TIMEOUT = "timeout"
    SYSTEM_ERROR = "system_error"
    VALIDATION_FAILED = "validation_failed"
    DEPENDENCY_FAILED = "dependency_failed"
    RESOURCE_EXHAUSTED = "resource_exhausted"


class CancellationState(str, Enum):
    """State of a cancellation operation."""

    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CleanupState(str, Enum):
    """State of cleanup operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# =============================================================================
# Checkpoint Contracts (Per ADR-0014: No partial data)
# =============================================================================


class CheckpointType(str, Enum):
    """Types of checkpoints during processing."""

    TABLE_COMPLETE = "table_complete"
    ROW_BATCH_COMPLETE = "row_batch_complete"
    STAGE_COMPLETE = "stage_complete"
    VALIDATION_COMPLETE = "validation_complete"


class Checkpoint(BaseModel):
    """A checkpoint marking completed work.

    Per ADR-0014: Only fully completed work is persisted.
    Checkpoints mark safe points where data integrity is guaranteed.
    """

    checkpoint_id: str
    checkpoint_type: CheckpointType
    stage_id: str
    created_at: datetime
    data_hash: str = Field(
        ...,
        description="Hash of data at this checkpoint for verification",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Progress tracking
    items_completed: int = Field(0, ge=0)
    items_total: int | None = None
    progress_percent: float | None = Field(None, ge=0.0, le=100.0)


class CheckpointRegistry(BaseModel):
    """Registry of checkpoints for a stage.

    Used to track progress and determine safe cancellation points.
    """

    stage_id: str
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    last_checkpoint_at: datetime | None = None

    @property
    def last_checkpoint(self) -> Checkpoint | None:
        """Get the most recent checkpoint."""
        if not self.checkpoints:
            return None
        return max(self.checkpoints, key=lambda c: c.created_at)

    @property
    def is_at_safe_point(self) -> bool:
        """Check if we're at a safe cancellation point."""
        last = self.last_checkpoint
        if not last:
            return True  # No work done yet, safe to cancel
        return last.checkpoint_type in [
            CheckpointType.TABLE_COMPLETE,
            CheckpointType.STAGE_COMPLETE,
        ]


# =============================================================================
# Cancellation Request/Response
# =============================================================================


class CancellationRequest(BaseModel):
    """Request to cancel an operation.

    Per ADR-0014: Cancellation preserves completed artifacts.
    """

    job_id: str = Field(..., description="ID of the job to cancel")
    stage_id: str | None = Field(
        None,
        description="Specific stage to cancel (None = cancel entire job)",
    )
    reason: CancellationReason = CancellationReason.USER_REQUESTED
    force: bool = Field(
        False,
        description="If True, cancel immediately without waiting for checkpoint",
    )
    cleanup_temp_files: bool = Field(
        False,
        description="If True, also cleanup temporary files (explicit cleanup)",
    )
    actor: str = Field("user", description="Who initiated the cancellation")


class CancellationResult(BaseModel):
    """Result of a cancellation operation.

    Per ADR-0014: No partial data persisted after cancellation.
    """

    job_id: str
    stage_id: str | None
    state: CancellationState
    reason: CancellationReason

    # What was preserved
    preserved_artifacts: list[str] = Field(
        default_factory=list,
        description="IDs of artifacts that were preserved (completed work)",
    )
    preserved_checkpoints: list[str] = Field(
        default_factory=list,
        description="IDs of checkpoints that mark preserved work",
    )

    # What was discarded
    discarded_partial_data: bool = Field(
        False,
        description="Whether partial/incomplete data was discarded",
    )
    discarded_items_count: int = Field(
        0,
        description="Number of partial items discarded",
    )

    # Cleanup status
    cleanup_performed: bool = False
    cleanup_state: CleanupState = CleanupState.PENDING
    temp_files_removed: int = 0

    # Timing
    requested_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Audit
    message: str = ""
    actor: str = "system"


# =============================================================================
# Cleanup Contracts (Per ADR-0014: Explicit cleanup)
# =============================================================================


class CleanupTarget(str, Enum):
    """Types of items that can be cleaned up."""

    TEMP_FILES = "temp_files"
    PARTIAL_ARTIFACTS = "partial_artifacts"
    ORPHANED_CHECKPOINTS = "orphaned_checkpoints"
    STALE_LOCKS = "stale_locks"
    ALL = "all"


class CleanupRequest(BaseModel):
    """Request for explicit cleanup of temporary/orphaned data.

    Per ADR-0014: Cleanup is explicit and user-initiated.
    """

    job_id: str | None = Field(
        None,
        description="Specific job to cleanup (None = cleanup all)",
    )
    targets: list[CleanupTarget] = Field(
        default=[CleanupTarget.TEMP_FILES],
        description="Types of items to cleanup",
    )
    dry_run: bool = Field(
        True,
        description="If True, report what would be cleaned without actually cleaning",
    )
    actor: str = "user"


class CleanupItem(BaseModel):
    """An item that was or would be cleaned up."""

    item_type: CleanupTarget
    path: str | None = None
    item_id: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = None
    reason: str = ""


class CleanupResult(BaseModel):
    """Result of a cleanup operation."""

    state: CleanupState
    dry_run: bool

    # Items affected
    items_found: list[CleanupItem] = Field(default_factory=list)
    items_cleaned: list[CleanupItem] = Field(default_factory=list)
    items_failed: list[CleanupItem] = Field(default_factory=list)

    # Summary
    total_items: int = 0
    cleaned_count: int = 0
    failed_count: int = 0
    bytes_freed: int = 0

    # Timing
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Audit
    actor: str = "system"
    message: str = ""


# =============================================================================
# Progress Tracking During Cancellable Operations
# =============================================================================


class CancellableOperationState(str, Enum):
    """State of a cancellable long-running operation."""

    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINTING = "checkpointing"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class CancellableOperation(BaseModel):
    """Tracks a cancellable operation with checkpointing.

    Per ADR-0014: Operations support soft cancellation with
    checkpoint-based data integrity guarantees.
    """

    operation_id: str
    job_id: str
    stage_id: str
    operation_type: str = Field(
        ...,
        description="Type of operation (e.g., 'parse', 'export')",
    )

    # State
    state: CancellableOperationState = CancellableOperationState.PENDING
    cancel_requested: bool = False
    cancel_request_at: datetime | None = None

    # Progress
    checkpoint_registry: CheckpointRegistry | None = None
    current_item: str | None = Field(
        None,
        description="Currently processing item (table name, etc.)",
    )
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)

    # Timing
    started_at: datetime | None = None
    last_activity_at: datetime | None = None

    def can_cancel_safely(self) -> bool:
        """Check if operation can be cancelled at current point."""
        if self.state in [
            CancellableOperationState.PENDING,
            CancellableOperationState.COMPLETED,
            CancellableOperationState.FAILED,
            CancellableOperationState.CANCELLED,
        ]:
            return True

        if self.checkpoint_registry:
            return self.checkpoint_registry.is_at_safe_point

        return False


# =============================================================================
# Audit Trail for Cancellation (Per ADR-0009, ADR-0014)
# =============================================================================


class CancellationAuditEntry(BaseModel):
    """Audit trail entry for cancellation events.

    Per ADR-0009: ISO-8601 UTC timestamps for all lifecycle events.
    Per ADR-0014: All cancellation events must be logged and auditable.
    """

    event_id: str
    event_type: Literal[
        "cancel_requested",
        "cancel_started",
        "checkpoint_reached",
        "partial_data_discarded",
        "artifacts_preserved",
        "cancel_completed",
        "cancel_failed",
        "cleanup_requested",
        "cleanup_completed",
    ]
    timestamp: datetime = Field(
        ...,
        description="ISO-8601 UTC timestamp (no microseconds)",
    )
    job_id: str
    stage_id: str | None = None
    actor: str
    details: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class CancellationAuditLog(BaseModel):
    """Complete audit log for cancellation operations."""

    job_id: str
    entries: list[CancellationAuditEntry] = Field(default_factory=list)

    def add_entry(
        self,
        event_type: str,
        actor: str,
        stage_id: str | None = None,
        details: dict[str, Any] | None = None,
        message: str = "",
    ) -> "CancellationAuditLog":
        """Add a new audit entry (returns new instance for immutability)."""
        from datetime import timezone

        new_entry = CancellationAuditEntry(
            event_id=f"{self.job_id}_{len(self.entries)}",
            event_type=event_type,  # type: ignore
            timestamp=datetime.now(timezone.utc).replace(microsecond=0),
            job_id=self.job_id,
            stage_id=stage_id,
            actor=actor,
            details=details or {},
            message=message,
        )
        return CancellationAuditLog(
            job_id=self.job_id,
            entries=[*self.entries, new_entry],
        )
