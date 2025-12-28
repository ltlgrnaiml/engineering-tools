"""Checkpoint manager for cancel-safe operations.

Per ADR-0013: Cancellation preserves completed work, no partial data.

This module provides checkpoint management for long-running DAT operations
including Parse and Export stages.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.contracts.dat.cancellation import (
    CancellableOperation,
    CancellableOperationState,
    CancellationAuditEntry,
    CancellationAuditLog,
    CancellationReason,
    CancellationRequest,
    CancellationResult,
    CancellationState,
    Checkpoint,
    CheckpointRegistry,
    CheckpointType,
    CleanupState,
)

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


class CheckpointManager:
    """Manages checkpoints for cancel-safe operations per ADR-0013.

    Provides:
    - Checkpoint creation and persistence
    - Safe cancellation point detection
    - Audit logging for cancellation events
    - Resumable operation support
    """

    def __init__(self, workspace_path: Path, run_id: str, stage_id: str) -> None:
        """Initialize checkpoint manager.

        Args:
            workspace_path: Path to workspace directory.
            run_id: DAT run ID.
            stage_id: Stage identifier (e.g., "parse", "export").
        """
        self.workspace_path = workspace_path
        self.run_id = run_id
        self.stage_id = stage_id

        self._checkpoint_dir = (
            workspace_path / "tools" / "dat" / "runs" / run_id / "checkpoints"
        )
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self._registry = CheckpointRegistry(stage_id=stage_id)
        self._audit_log = CancellationAuditLog(job_id=run_id)
        self._operation: CancellableOperation | None = None

        # Load existing checkpoints if resuming
        self._load_checkpoints()

    def _load_checkpoints(self) -> None:
        """Load existing checkpoints from disk."""
        registry_path = self._checkpoint_dir / f"{self.stage_id}_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, encoding="utf-8") as f:
                    data = json.load(f)
                self._registry = CheckpointRegistry.model_validate(data)
                logger.info(
                    f"Loaded {len(self._registry.checkpoints)} existing checkpoints"
                )
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load checkpoint registry: {e}")

    def _save_registry(self) -> None:
        """Persist checkpoint registry to disk."""
        registry_path = self._checkpoint_dir / f"{self.stage_id}_registry.json"
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(self._registry.model_dump(mode="json"), f, indent=2, default=str)

    def _compute_data_hash(self, data: Any) -> str:
        """Compute hash of data for checkpoint verification."""
        if hasattr(data, "to_dict"):
            data_str = json.dumps(data.to_dict(), sort_keys=True, default=str)
        else:
            data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def start_operation(self, operation_type: str) -> CancellableOperation:
        """Start a new cancellable operation.

        Args:
            operation_type: Type of operation (e.g., "parse", "export").

        Returns:
            CancellableOperation instance for tracking.
        """
        now = datetime.now(timezone.utc)
        self._operation = CancellableOperation(
            operation_id=f"{self.run_id}_{self.stage_id}_{now.timestamp()}",
            job_id=self.run_id,
            stage_id=self.stage_id,
            operation_type=operation_type,
            state=CancellableOperationState.RUNNING,
            started_at=now,
            last_activity_at=now,
            checkpoint_registry=self._registry,
        )
        logger.info(f"Started {operation_type} operation: {self._operation.operation_id}")
        return self._operation

    def save_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        items_completed: int,
        items_total: int | None = None,
        current_item: str | None = None,
        data_for_hash: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Save a checkpoint marking completed work.

        Per ADR-0013: Checkpoints mark safe points where data integrity is guaranteed.

        Args:
            checkpoint_type: Type of checkpoint.
            items_completed: Number of items completed.
            items_total: Total number of items (optional).
            current_item: Currently processing item name.
            data_for_hash: Data to hash for verification.
            metadata: Additional checkpoint metadata.

        Returns:
            Created Checkpoint instance.
        """
        now = datetime.now(timezone.utc)
        progress_pct = None
        if items_total and items_total > 0:
            progress_pct = (items_completed / items_total) * 100

        data_hash = self._compute_data_hash(data_for_hash) if data_for_hash else ""

        checkpoint = Checkpoint(
            checkpoint_id=f"{self.stage_id}_cp_{len(self._registry.checkpoints)}",
            checkpoint_type=checkpoint_type,
            stage_id=self.stage_id,
            created_at=now,
            data_hash=data_hash,
            metadata=metadata or {},
            items_completed=items_completed,
            items_total=items_total,
            progress_percent=progress_pct,
        )

        self._registry.checkpoints.append(checkpoint)
        self._registry.last_checkpoint_at = now

        # Update operation state
        if self._operation:
            self._operation.last_activity_at = now
            self._operation.current_item = current_item
            if progress_pct is not None:
                self._operation.progress_percent = progress_pct

        # Persist to disk
        self._save_registry()

        logger.debug(
            f"Checkpoint saved: {checkpoint.checkpoint_id} "
            f"({items_completed}/{items_total or '?'})"
        )
        return checkpoint

    def is_at_safe_point(self) -> bool:
        """Check if we're at a safe cancellation point.

        Per ADR-0013: Safe points are after table or stage completion.

        Returns:
            True if cancellation is safe at current point.
        """
        return self._registry.is_at_safe_point

    def get_last_checkpoint(self) -> Checkpoint | None:
        """Get the most recent checkpoint."""
        return self._registry.last_checkpoint

    def get_progress(self) -> tuple[int, int | None, float | None]:
        """Get current progress from last checkpoint.

        Returns:
            Tuple of (completed_items, total_items, progress_percent).
        """
        last = self.get_last_checkpoint()
        if not last:
            return 0, None, None
        return last.items_completed, last.items_total, last.progress_percent

    def request_cancellation(
        self,
        reason: CancellationReason = CancellationReason.USER_REQUESTED,
        actor: str = "user",
        force: bool = False,
    ) -> CancellationRequest:
        """Create a cancellation request.

        Args:
            reason: Reason for cancellation.
            actor: Who initiated the cancellation.
            force: If True, cancel immediately without waiting for checkpoint.

        Returns:
            CancellationRequest instance.
        """
        request = CancellationRequest(
            job_id=self.run_id,
            stage_id=self.stage_id,
            reason=reason,
            force=force,
            actor=actor,
        )

        # Log to audit
        self._audit_log = self._audit_log.add_entry(
            event_type="cancel_requested",
            actor=actor,
            stage_id=self.stage_id,
            details={"reason": reason.value, "force": force},
            message=f"Cancellation requested: {reason.value}",
        )

        if self._operation:
            self._operation.cancel_requested = True
            self._operation.cancel_request_at = datetime.now(timezone.utc)
            self._operation.state = CancellableOperationState.CANCELLING

        logger.info(f"Cancellation requested for {self.run_id}/{self.stage_id}")
        return request

    def complete_cancellation(
        self,
        preserved_artifacts: list[str] | None = None,
        discarded_count: int = 0,
    ) -> CancellationResult:
        """Complete a cancellation operation.

        Per ADR-0013: Record what was preserved and discarded.

        Args:
            preserved_artifacts: IDs of preserved artifacts.
            discarded_count: Number of partial items discarded.

        Returns:
            CancellationResult with full details.
        """
        now = datetime.now(timezone.utc)

        # Collect preserved checkpoint IDs
        preserved_checkpoints = [cp.checkpoint_id for cp in self._registry.checkpoints]

        result = CancellationResult(
            job_id=self.run_id,
            stage_id=self.stage_id,
            state=CancellationState.COMPLETED,
            reason=CancellationReason.USER_REQUESTED,
            preserved_artifacts=preserved_artifacts or [],
            preserved_checkpoints=preserved_checkpoints,
            discarded_partial_data=discarded_count > 0,
            discarded_items_count=discarded_count,
            cleanup_state=CleanupState.PENDING,
            requested_at=self._operation.cancel_request_at if self._operation else now,
            completed_at=now,
            message=f"Cancellation completed. {len(preserved_checkpoints)} checkpoints preserved.",
        )

        # Log to audit
        self._audit_log = self._audit_log.add_entry(
            event_type="cancel_completed",
            actor="system",
            stage_id=self.stage_id,
            details={
                "preserved_artifacts": preserved_artifacts or [],
                "discarded_count": discarded_count,
            },
            message=result.message,
        )

        if self._operation:
            self._operation.state = CancellableOperationState.CANCELLED

        # Save final state
        self._save_registry()
        self._save_audit_log()

        logger.info(f"Cancellation completed: {result.message}")
        return result

    def complete_operation(self) -> None:
        """Mark operation as successfully completed."""
        if self._operation:
            self._operation.state = CancellableOperationState.COMPLETED
            self._operation.progress_percent = 100.0

        # Save final checkpoint
        self.save_checkpoint(
            checkpoint_type=CheckpointType.STAGE_COMPLETE,
            items_completed=self._registry.last_checkpoint.items_total or 0
            if self._registry.last_checkpoint
            else 0,
            items_total=self._registry.last_checkpoint.items_total
            if self._registry.last_checkpoint
            else None,
        )

        logger.info(f"Operation completed: {self.stage_id}")

    def get_audit_log(self) -> CancellationAuditLog:
        """Get the cancellation audit log."""
        return self._audit_log

    def _save_audit_log(self) -> None:
        """Persist audit log to disk."""
        audit_path = self._checkpoint_dir / f"{self.stage_id}_audit.json"
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(self._audit_log.model_dump(mode="json"), f, indent=2, default=str)

    def clear_checkpoints(self) -> int:
        """Clear all checkpoints for this stage.

        Returns:
            Number of checkpoints cleared.
        """
        count = len(self._registry.checkpoints)
        self._registry = CheckpointRegistry(stage_id=self.stage_id)
        self._save_registry()
        logger.info(f"Cleared {count} checkpoints for {self.stage_id}")
        return count
