"""Hybrid FSM for DAT stage orchestration.

Per ADR-0001-DAT: 8-stage pipeline with lockable artifacts.
Per ADR-0002: Artifacts preserved on unlock (never deleted).
Per ADR-0003: Context and Preview are optional, do not cascade.
Per ADR-0004-DAT: Stage IDs are deterministic (same inputs = same ID).

Each stage manages its own lifecycle while a global orchestrator
coordinates forward gating and unlock cascades.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from shared.contracts.dat import DATStageState, DATStageType
from shared.contracts.dat.stage_graph import StageGraphConfig

if TYPE_CHECKING:
    from .run_store import RunStore


# Re-export for backward compatibility
Stage = DATStageType
StageState = DATStageState


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


class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration.

    Per ADR-0001-DAT: Config-driven stage graph.
    """

    def __init__(
        self,
        run_id: str,
        store: "RunStore",
        config: StageGraphConfig | None = None,
    ) -> None:
        """Initialize the state machine.

        Args:
            run_id: Unique run identifier.
            store: Run store for persistence.
            config: Stage graph configuration. Defaults to standard 8-stage pipeline.
        """
        self.run_id = run_id
        self.store = store
        self.config = config or StageGraphConfig.default()
        self._build_lookup_tables()

    def _build_lookup_tables(self) -> None:
        """Build fast lookup dicts from config."""
        self._forward_gates: dict[Stage, list[tuple[Stage, bool]]] = {}
        for rule in self.config.gating_rules:
            self._forward_gates[rule.target_stage] = [
                (s, rule.require_completion) for s in rule.required_stages
            ]

        self._cascade_targets: dict[Stage, list[Stage]] = {}
        for rule in self.config.cascade_rules:
            self._cascade_targets[rule.trigger_stage] = list(rule.cascade_targets)

    async def can_lock(self, stage: Stage) -> tuple[bool, str | None]:
        """Check if a stage can be locked (forward gating).

        Returns:
            (can_lock, reason) - reason is None if can_lock is True
        """
        gates = self._forward_gates.get(stage, [])

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
                locked_at=datetime.now(UTC),
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
            locked_at=datetime.now(UTC),
            completed=result.get("completed", False),
            artifact_path=artifact_path,
        )
        await self.store.set_stage_status(self.run_id, stage, status)

        return status

    async def unlock_stage(self, stage: Stage, cascade: bool = True) -> list[StageStatus]:
        """Unlock a stage and optionally cascade to downstream stages.

        Per ADR-0002: Artifacts are preserved (never deleted).

        Args:
            stage: The stage to unlock.
            cascade: If True, also unlock downstream stages per CASCADE_TARGETS.

        Returns:
            List of StageStatus for all unlocked stages.
        """
        now = datetime.now(UTC)
        unlocked: list[StageStatus] = []

        # Unlock this stage (preserve artifact)
        status = StageStatus(
            stage=stage,
            state=StageState.UNLOCKED,
            unlocked_at=now,
        )
        await self.store.set_stage_status(self.run_id, stage, status)
        unlocked.append(status)

        # Cascade to downstream stages if requested
        if cascade:
            for target in self._cascade_targets.get(stage, []):
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
