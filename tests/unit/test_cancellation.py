"""Tests for DAT cancellation semantics contracts.

Per ADR-0013: Cancellation Semantics for Parse & Export.
Tests for soft cancellation, checkpointing, and audit trails.
"""

from datetime import datetime, timezone

import pytest

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
    CleanupRequest,
    CleanupResult,
    CleanupState,
    CleanupTarget,
)


class TestCancellationRequest:
    """Tests for CancellationRequest model."""

    def test_minimal_request(self) -> None:
        """Minimal request should have defaults."""
        request = CancellationRequest(job_id="job_123")

        assert request.job_id == "job_123"
        assert request.stage_id is None
        assert request.reason == CancellationReason.USER_REQUESTED
        assert request.force is False
        assert request.cleanup_temp_files is False

    def test_full_request(self) -> None:
        """Full request with all fields."""
        request = CancellationRequest(
            job_id="job_123",
            stage_id="parse_abc",
            reason=CancellationReason.TIMEOUT,
            force=True,
            cleanup_temp_files=True,
            actor="system",
        )

        assert request.stage_id == "parse_abc"
        assert request.reason == CancellationReason.TIMEOUT
        assert request.force is True


class TestCancellationResult:
    """Tests for CancellationResult model."""

    def test_successful_cancellation(self) -> None:
        """Successful cancellation preserves artifacts."""
        result = CancellationResult(
            job_id="job_123",
            stage_id="parse_1",
            state=CancellationState.COMPLETED,
            reason=CancellationReason.USER_REQUESTED,
            preserved_artifacts=["artifact_1", "artifact_2"],
            discarded_partial_data=True,
            discarded_items_count=5,
            requested_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            message="Cancelled successfully",
        )

        assert result.state == CancellationState.COMPLETED
        assert len(result.preserved_artifacts) == 2
        assert result.discarded_partial_data is True

    def test_artifact_preservation(self) -> None:
        """Per ADR-0013: Completed artifacts must be preserved."""
        result = CancellationResult(
            job_id="job_1",
            state=CancellationState.COMPLETED,
            reason=CancellationReason.USER_REQUESTED,
            preserved_artifacts=["table_1", "table_2", "table_3"],
            preserved_checkpoints=["checkpoint_1", "checkpoint_2"],
            requested_at=datetime.now(timezone.utc),
        )

        # Per ADR-0013: preserved_artifacts should contain completed work
        assert "table_1" in result.preserved_artifacts
        assert len(result.preserved_checkpoints) > 0


class TestCheckpoint:
    """Tests for Checkpoint model."""

    def test_checkpoint_creation(self) -> None:
        """Checkpoint should track completed work."""
        checkpoint = Checkpoint(
            checkpoint_id="cp_001",
            checkpoint_type=CheckpointType.TABLE_COMPLETE,
            stage_id="parse_abc",
            created_at=datetime.now(timezone.utc),
            data_hash="abc123",
            items_completed=10,
            items_total=20,
            progress_percent=50.0,
        )

        assert checkpoint.checkpoint_type == CheckpointType.TABLE_COMPLETE
        assert checkpoint.items_completed == 10
        assert checkpoint.progress_percent == 50.0

    def test_checkpoint_types(self) -> None:
        """All checkpoint types should be valid."""
        types = [
            CheckpointType.TABLE_COMPLETE,
            CheckpointType.ROW_BATCH_COMPLETE,
            CheckpointType.STAGE_COMPLETE,
            CheckpointType.VALIDATION_COMPLETE,
        ]

        for cp_type in types:
            checkpoint = Checkpoint(
                checkpoint_id="test",
                checkpoint_type=cp_type,
                stage_id="stage_1",
                created_at=datetime.now(timezone.utc),
                data_hash="hash",
            )
            assert checkpoint.checkpoint_type == cp_type


class TestCheckpointRegistry:
    """Tests for CheckpointRegistry model."""

    def test_empty_registry(self) -> None:
        """Empty registry should indicate safe cancellation point."""
        registry = CheckpointRegistry(stage_id="stage_1")

        assert registry.last_checkpoint is None
        assert registry.is_at_safe_point is True

    def test_registry_with_checkpoints(self) -> None:
        """Registry should track multiple checkpoints."""
        now = datetime.now(timezone.utc)
        checkpoints = [
            Checkpoint(
                checkpoint_id="cp_1",
                checkpoint_type=CheckpointType.ROW_BATCH_COMPLETE,
                stage_id="stage_1",
                created_at=now,
                data_hash="hash1",
            ),
            Checkpoint(
                checkpoint_id="cp_2",
                checkpoint_type=CheckpointType.TABLE_COMPLETE,
                stage_id="stage_1",
                created_at=now,
                data_hash="hash2",
            ),
        ]

        registry = CheckpointRegistry(
            stage_id="stage_1",
            checkpoints=checkpoints,
        )

        assert len(registry.checkpoints) == 2
        assert registry.last_checkpoint is not None

    def test_safe_point_detection(self) -> None:
        """Per ADR-0013: TABLE_COMPLETE is a safe cancellation point."""
        now = datetime.now(timezone.utc)

        # Table complete = safe
        safe_registry = CheckpointRegistry(
            stage_id="stage_1",
            checkpoints=[
                Checkpoint(
                    checkpoint_id="cp_1",
                    checkpoint_type=CheckpointType.TABLE_COMPLETE,
                    stage_id="stage_1",
                    created_at=now,
                    data_hash="hash",
                ),
            ],
        )
        assert safe_registry.is_at_safe_point is True

        # Row batch = not safe (partial)
        unsafe_registry = CheckpointRegistry(
            stage_id="stage_1",
            checkpoints=[
                Checkpoint(
                    checkpoint_id="cp_1",
                    checkpoint_type=CheckpointType.ROW_BATCH_COMPLETE,
                    stage_id="stage_1",
                    created_at=now,
                    data_hash="hash",
                ),
            ],
        )
        assert unsafe_registry.is_at_safe_point is False


class TestCancellableOperation:
    """Tests for CancellableOperation model."""

    def test_operation_creation(self) -> None:
        """Operation should track cancellation state."""
        operation = CancellableOperation(
            operation_id="op_001",
            job_id="job_123",
            stage_id="parse_abc",
            operation_type="parse",
        )

        assert operation.state == CancellableOperationState.PENDING
        assert operation.cancel_requested is False

    def test_can_cancel_safely_pending(self) -> None:
        """Pending operations can always be cancelled safely."""
        operation = CancellableOperation(
            operation_id="op_001",
            job_id="job_123",
            stage_id="stage_1",
            operation_type="parse",
            state=CancellableOperationState.PENDING,
        )

        assert operation.can_cancel_safely() is True

    def test_can_cancel_safely_running(self) -> None:
        """Running operations need checkpoint check."""
        now = datetime.now(timezone.utc)

        # With safe checkpoint
        operation_safe = CancellableOperation(
            operation_id="op_001",
            job_id="job_123",
            stage_id="stage_1",
            operation_type="parse",
            state=CancellableOperationState.RUNNING,
            checkpoint_registry=CheckpointRegistry(
                stage_id="stage_1",
                checkpoints=[
                    Checkpoint(
                        checkpoint_id="cp_1",
                        checkpoint_type=CheckpointType.TABLE_COMPLETE,
                        stage_id="stage_1",
                        created_at=now,
                        data_hash="hash",
                    ),
                ],
            ),
        )
        assert operation_safe.can_cancel_safely() is True


class TestCleanupRequest:
    """Tests for CleanupRequest model."""

    def test_default_cleanup_is_dry_run(self) -> None:
        """Per ADR-0013: Cleanup should default to dry run."""
        request = CleanupRequest()

        assert request.dry_run is True
        assert request.targets == [CleanupTarget.TEMP_FILES]

    def test_full_cleanup_request(self) -> None:
        """Full cleanup with all targets."""
        request = CleanupRequest(
            job_id="job_123",
            targets=[CleanupTarget.ALL],
            dry_run=False,
            actor="admin",
        )

        assert request.job_id == "job_123"
        assert CleanupTarget.ALL in request.targets
        assert request.dry_run is False


class TestCleanupResult:
    """Tests for CleanupResult model."""

    def test_cleanup_result(self) -> None:
        """Cleanup result should summarize operations."""
        result = CleanupResult(
            state=CleanupState.COMPLETED,
            dry_run=False,
            total_items=10,
            cleaned_count=8,
            failed_count=2,
            bytes_freed=1024000,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        assert result.state == CleanupState.COMPLETED
        assert result.cleaned_count == 8
        assert result.bytes_freed == 1024000


class TestCancellationAuditLog:
    """Tests for CancellationAuditLog model."""

    def test_audit_log_creation(self) -> None:
        """Audit log should start empty."""
        log = CancellationAuditLog(job_id="job_123")

        assert log.job_id == "job_123"
        assert len(log.entries) == 0

    def test_add_audit_entry(self) -> None:
        """Per ADR-0008/ADR-0013: All events must be logged."""
        log = CancellationAuditLog(job_id="job_123")

        # Add entries (immutable pattern)
        log = log.add_entry(
            event_type="cancel_requested",
            actor="user",
            message="User requested cancellation",
        )
        log = log.add_entry(
            event_type="checkpoint_reached",
            actor="system",
            stage_id="parse_1",
            details={"checkpoint_id": "cp_1"},
        )

        assert len(log.entries) == 2
        assert log.entries[0].event_type == "cancel_requested"
        assert log.entries[1].stage_id == "parse_1"

    def test_audit_entry_timestamps(self) -> None:
        """Per ADR-0008: Timestamps must be ISO-8601 UTC."""
        entry = CancellationAuditEntry(
            event_id="evt_001",
            event_type="cancel_requested",
            timestamp=datetime.now(timezone.utc).replace(microsecond=0),
            job_id="job_123",
            actor="user",
        )

        # Timestamp should have no microseconds (per ADR-0008)
        assert entry.timestamp.microsecond == 0
