"""Hybrid FSM for DAT stage orchestration.

Per ADR-0001: Each stage manages its own UNLOCKED ↔ LOCKED lifecycle,
while a global orchestrator coordinates unlock cascades.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .run_store import RunStore


class Stage(str, Enum):
    """DAT pipeline stages.

    Per ADR-0001-DAT: 8-stage pipeline with Discovery as first stage.
    """
    DISCOVERY = "discovery"  # Implicit file scan made explicit
    SELECTION = "selection"
    CONTEXT = "context"
    TABLE_AVAILABILITY = "table_availability"
    TABLE_SELECTION = "table_selection"
    PREVIEW = "preview"
    PARSE = "parse"
    EXPORT = "export"


class StageState(str, Enum):
    """State of a stage."""
    UNLOCKED = "unlocked"
    LOCKED = "locked"


@dataclass
class StageStatus:
    """Current status of a stage."""
    stage: Stage
    state: StageState
    stage_id: str | None = None
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None
    completed: bool = False
    error: str | None = None
    artifact_path: str | None = None


# Forward gating rules (per ADR-0001-DAT)
FORWARD_GATES: dict[Stage, list[tuple[Stage, bool]]] = {
    # Stage: [(required_stage, must_be_completed), ...]
    # Discovery has no gates - it's the first stage
    Stage.SELECTION: [(Stage.DISCOVERY, False)],
    Stage.CONTEXT: [(Stage.SELECTION, False)],
    Stage.TABLE_AVAILABILITY: [(Stage.SELECTION, False)],
    Stage.TABLE_SELECTION: [(Stage.TABLE_AVAILABILITY, False)],
    Stage.PREVIEW: [(Stage.TABLE_SELECTION, False)],
    Stage.PARSE: [(Stage.TABLE_SELECTION, False)],
    Stage.EXPORT: [(Stage.PARSE, True)],  # Must be completed
}

# Cascade unlock rules (per ADR-0001-DAT)
CASCADE_TARGETS: dict[Stage, list[Stage]] = {
    Stage.DISCOVERY: [
        Stage.SELECTION, Stage.CONTEXT, Stage.TABLE_AVAILABILITY,
        Stage.TABLE_SELECTION, Stage.PREVIEW, Stage.PARSE, Stage.EXPORT
    ],
    Stage.SELECTION: [
        Stage.CONTEXT, Stage.TABLE_AVAILABILITY, Stage.TABLE_SELECTION,
        Stage.PREVIEW, Stage.PARSE, Stage.EXPORT
    ],
    Stage.TABLE_AVAILABILITY: [
        Stage.TABLE_SELECTION, Stage.PREVIEW, Stage.PARSE, Stage.EXPORT
    ],
    Stage.TABLE_SELECTION: [Stage.PREVIEW, Stage.PARSE, Stage.EXPORT],
    Stage.PARSE: [Stage.EXPORT],
    # Context and Preview do NOT cascade (per ADR-0003)
    Stage.CONTEXT: [],
    Stage.PREVIEW: [],
}


class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration."""
    
    def __init__(self, run_id: str, store: "RunStore"):
        self.run_id = run_id
        self.store = store
    
    async def can_lock(self, stage: Stage) -> tuple[bool, str | None]:
        """Check if a stage can be locked (forward gating).
        
        Returns:
            (can_lock, reason) - reason is None if can_lock is True
        """
        gates = FORWARD_GATES.get(stage, [])
        
        for required_stage, must_complete in gates:
            status = await self.store.get_stage_status(self.run_id, required_stage)
            
            if status.state != StageState.LOCKED:
                return False, f"{required_stage.value} must be locked first"
            
            if must_complete and not status.completed:
                return False, f"{required_stage.value} must be completed first"
        
        return True, None
    
    async def lock_stage(
        self,
        stage: Stage,
        inputs: dict[str, Any] | None = None,
        execute_fn: Callable[[], dict] | None = None,
    ) -> StageStatus:
        """Lock a stage, optionally executing its logic.
        
        Per ADR-0002: If stage ID exists, reuse artifact (idempotent re-lock).
        """
        from shared.utils.stage_id import compute_stage_id
        
        # Check forward gating
        can_lock, reason = await self.can_lock(stage)
        if not can_lock:
            raise ValueError(f"Cannot lock {stage.value}: {reason}")
        
        # Get inputs for deterministic ID
        stage_inputs = inputs or await self._get_stage_inputs(stage)
        stage_id = compute_stage_id(stage_inputs, prefix=f"{stage.value}_")
        
        # Check for existing artifact (idempotent re-lock per ADR-0004)
        existing = await self.store.get_artifact(self.run_id, stage, stage_id)
        if existing:
            # Reuse existing artifact
            status = StageStatus(
                stage=stage,
                state=StageState.LOCKED,
                stage_id=stage_id,
                locked_at=datetime.now(timezone.utc),
                completed=existing.get("completed", False),
                artifact_path=existing.get("path"),
            )
            await self.store.set_stage_status(self.run_id, stage, status)
            return status
        
        # Execute stage logic if provided
        result: dict = {}
        if execute_fn:
            result = await execute_fn()
        
        # Save artifact and update status
        artifact_path = await self.store.save_artifact(self.run_id, stage, stage_id, result)
        status = StageStatus(
            stage=stage,
            state=StageState.LOCKED,
            stage_id=stage_id,
            locked_at=datetime.now(timezone.utc),
            completed=result.get("completed", True),
            artifact_path=artifact_path,
        )
        await self.store.set_stage_status(self.run_id, stage, status)
        
        return status
    
    async def unlock_stage(self, stage: Stage) -> list[StageStatus]:
        """Unlock a stage and cascade to downstream stages.
        
        Per ADR-0002: Artifacts are preserved (never deleted).
        """
        now = datetime.now(timezone.utc)
        unlocked: list[StageStatus] = []
        
        # Unlock this stage (preserve artifact)
        status = StageStatus(
            stage=stage,
            state=StageState.UNLOCKED,
            unlocked_at=now,
        )
        await self.store.set_stage_status(self.run_id, stage, status)
        unlocked.append(status)
        
        # Cascade to downstream stages
        for target in CASCADE_TARGETS.get(stage, []):
            current = await self.store.get_stage_status(self.run_id, target)
            if current.state == StageState.LOCKED:
                target_status = StageStatus(
                    stage=target,
                    state=StageState.UNLOCKED,
                    unlocked_at=now,
                )
                await self.store.set_stage_status(self.run_id, target, target_status)
                unlocked.append(target_status)
        
        return unlocked
    
    async def get_all_statuses(self) -> dict[Stage, StageStatus]:
        """Get status of all stages."""
        return await self.store.get_all_stage_statuses(self.run_id)
    
    async def _get_stage_inputs(self, stage: Stage) -> dict:
        """Get inputs for deterministic stage ID computation."""
        return {"run_id": self.run_id, "stage": stage.value}
