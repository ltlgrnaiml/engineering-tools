"""Run manager for DAT pipeline orchestration."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .run_store import RunStore
from .state_machine import DATStateMachine, Stage


class RunManager:
    """Manages DAT runs and their lifecycle."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.store = RunStore(workspace_path)
    
    async def create_run(
        self,
        name: str | None = None,
        profile_id: str | None = None,
    ) -> dict:
        """Create a new DAT run.
        
        Args:
            name: Optional human-readable name
            profile_id: Optional extraction profile to use
            
        Returns:
            Run metadata dict
        """
        run_id = str(uuid.uuid4())
        run = await self.store.create_run(run_id, name)
        run["profile_id"] = profile_id
        return run
    
    async def get_run(self, run_id: str) -> dict | None:
        """Get run by ID."""
        return await self.store.get_run(run_id)
    
    async def list_runs(self, limit: int = 50) -> list[dict]:
        """List recent runs."""
        return await self.store.list_runs(limit)
    
    def get_state_machine(self, run_id: str) -> DATStateMachine:
        """Get state machine for a run."""
        return DATStateMachine(run_id, self.store)
    
    async def get_parse_result(self, run_id: str) -> dict | None:
        """Get parse result for a run if available."""
        from .state_machine import StageState
        
        status = await self.store.get_stage_status(run_id, Stage.PARSE)
        if status.state != StageState.LOCKED or not status.completed:
            return None
        
        if status.stage_id:
            return await self.store.get_artifact(run_id, Stage.PARSE, status.stage_id)
        return None
