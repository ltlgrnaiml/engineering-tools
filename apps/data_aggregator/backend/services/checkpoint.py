"""Checkpoint registry for cancellation safety.

Per ADR-0013: Checkpoints are safe points where data integrity is guaranteed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.contracts.dat.cancellation import CheckpointType

__version__ = "1.0.0"


@dataclass
class Checkpoint:
    """A checkpoint marking a safe point in processing."""

    checkpoint_type: CheckpointType
    artifact_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class CheckpointRegistry:
    """Registry for tracking checkpoints during processing.

    Per ADR-0013: Track safe points for cancellation recovery.
    """

    def __init__(self, run_id: str):
        """Initialize checkpoint registry.

        Args:
            run_id: Run identifier.
        """
        self.run_id = run_id
        self._checkpoints: list[Checkpoint] = []

    def mark_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        artifact_id: str,
        metadata: dict | None = None,
    ) -> Checkpoint:
        """Mark a safe checkpoint.

        Args:
            checkpoint_type: Type of checkpoint.
            artifact_id: ID of the artifact at this checkpoint.
            metadata: Optional additional metadata.

        Returns:
            The created Checkpoint.
        """
        checkpoint = Checkpoint(
            checkpoint_type=checkpoint_type,
            artifact_id=artifact_id,
            metadata=metadata or {},
        )
        self._checkpoints.append(checkpoint)
        return checkpoint

    def get_last_safe_point(self) -> Checkpoint | None:
        """Get the last safe checkpoint for rollback.

        Returns:
            Last checkpoint or None if no checkpoints exist.
        """
        return self._checkpoints[-1] if self._checkpoints else None

    def get_all_checkpoints(self) -> list[Checkpoint]:
        """Get all checkpoints.

        Returns:
            List of all checkpoints.
        """
        return list(self._checkpoints)

    def clear(self) -> None:
        """Clear all checkpoints."""
        self._checkpoints.clear()
