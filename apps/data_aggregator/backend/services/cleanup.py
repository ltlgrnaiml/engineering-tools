"""Explicit cleanup service.

Per ADR-0014: Cleanup is user-initiated only, dry-run by default.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from shared.contracts.dat.cancellation import CleanupTarget, CleanupResult

__version__ = "1.0.0"


@dataclass
class CleanupAction:
    """A single cleanup action."""

    target: CleanupTarget
    action: Literal["delete", "archive", "skip"]
    path: Path | None
    reason: str


async def cleanup(
    run_id: str,
    targets: list[CleanupTarget],
    dry_run: bool = True,
    archive_dir: Path | None = None,
) -> CleanupResult:
    """Clean up partial artifacts from cancelled runs.

    Per ADR-0014: Dry-run by default, explicit cleanup only.

    Args:
        run_id: Run identifier.
        targets: List of cleanup targets.
        dry_run: If True, only report what would be cleaned (default: True).
        archive_dir: Optional directory to archive instead of delete.

    Returns:
        CleanupResult with details of cleanup actions.
    """
    actions: list[CleanupAction] = []
    deleted_count = 0
    archived_count = 0
    skipped_count = 0

    for target in targets:
        # Determine action based on target type
        if target.is_checkpoint_safe:
            actions.append(CleanupAction(
                target=target,
                action="skip",
                path=None,
                reason="Checkpoint-safe artifact preserved",
            ))
            skipped_count += 1
            continue

        target_path = Path(target.path) if target.path else None

        if not target_path or not target_path.exists():
            actions.append(CleanupAction(
                target=target,
                action="skip",
                path=target_path,
                reason="Path does not exist",
            ))
            skipped_count += 1
            continue

        if dry_run:
            action_type = "archive" if archive_dir else "delete"
            actions.append(CleanupAction(
                target=target,
                action=action_type,
                path=target_path,
                reason=f"Would {action_type} (dry-run)",
            ))
        else:
            if archive_dir:
                # Move to archive
                archive_path = archive_dir / target_path.name
                target_path.rename(archive_path)
                actions.append(CleanupAction(
                    target=target,
                    action="archive",
                    path=archive_path,
                    reason="Archived",
                ))
                archived_count += 1
            else:
                # Delete
                if target_path.is_file():
                    target_path.unlink()
                else:
                    shutil.rmtree(target_path)
                actions.append(CleanupAction(
                    target=target,
                    action="delete",
                    path=target_path,
                    reason="Deleted",
                ))
                deleted_count += 1

    return CleanupResult(
        run_id=run_id,
        dry_run=dry_run,
        deleted_count=deleted_count,
        archived_count=archived_count,
        skipped_count=skipped_count,
        actions=[a.__dict__ for a in actions],
        completed_at=datetime.now(timezone.utc),
    )
