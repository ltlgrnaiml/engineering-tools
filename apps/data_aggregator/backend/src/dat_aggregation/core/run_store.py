"""Run storage for DAT pipeline state.

Stores run metadata, stage statuses, and artifact references.
"""
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .state_machine import Stage, StageState, StageStatus


class RunStore:
    """Storage for DAT run state and artifacts."""
    
    def __init__(self, workspace_path: Path | None = None):
        if workspace_path is None:
            workspace_path = Path.cwd() / "workspace"
        self.workspace = workspace_path
        self.dat_workspace = self.workspace / "tools" / "dat"
        self.dat_workspace.mkdir(parents=True, exist_ok=True)
    
    def _run_dir(self, run_id: str) -> Path:
        """Get directory for a run."""
        path = self.dat_workspace / "runs" / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _state_file(self, run_id: str) -> Path:
        """Get state file path for a run."""
        return self._run_dir(run_id) / "state.json"
    
    async def create_run(self, run_id: str, name: str | None = None) -> dict:
        """Create a new run."""
        run_dir = self._run_dir(run_id)
        state = {
            "run_id": run_id,
            "name": name or f"Run {run_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stages": {},
        }
        self._write_state(run_id, state)
        return state
    
    async def get_run(self, run_id: str) -> dict | None:
        """Get run metadata."""
        try:
            return self._read_state(run_id)
        except FileNotFoundError:
            return None
    
    async def list_runs(self, limit: int = 50) -> list[dict]:
        """List all runs."""
        runs_dir = self.dat_workspace / "runs"
        if not runs_dir.exists():
            return []
        
        runs = []
        for run_dir in sorted(runs_dir.iterdir(), reverse=True)[:limit]:
            if run_dir.is_dir():
                state = await self.get_run(run_dir.name)
                if state:
                    runs.append(state)
        return runs
    
    async def get_stage_status(self, run_id: str, stage: Stage) -> StageStatus:
        """Get status of a specific stage."""
        state = self._read_state(run_id)
        stage_data = state.get("stages", {}).get(stage.value, {})
        
        if not stage_data:
            return StageStatus(stage=stage, state=StageState.UNLOCKED)
        
        return StageStatus(
            stage=stage,
            state=StageState(stage_data.get("state", "unlocked")),
            stage_id=stage_data.get("stage_id"),
            locked_at=datetime.fromisoformat(stage_data["locked_at"]) if stage_data.get("locked_at") else None,
            unlocked_at=datetime.fromisoformat(stage_data["unlocked_at"]) if stage_data.get("unlocked_at") else None,
            completed=stage_data.get("completed", False),
            error=stage_data.get("error"),
            artifact_path=stage_data.get("artifact_path"),
        )
    
    async def set_stage_status(self, run_id: str, stage: Stage, status: StageStatus) -> None:
        """Set status of a specific stage."""
        state = self._read_state(run_id)
        if "stages" not in state:
            state["stages"] = {}
        
        state["stages"][stage.value] = {
            "state": status.state.value,
            "stage_id": status.stage_id,
            "locked_at": status.locked_at.isoformat() if status.locked_at else None,
            "unlocked_at": status.unlocked_at.isoformat() if status.unlocked_at else None,
            "completed": status.completed,
            "error": status.error,
            "artifact_path": status.artifact_path,
        }
        
        self._write_state(run_id, state)
    
    async def get_all_stage_statuses(self, run_id: str) -> dict[Stage, StageStatus]:
        """Get status of all stages."""
        result = {}
        for stage in Stage:
            result[stage] = await self.get_stage_status(run_id, stage)
        return result
    
    async def get_artifact(self, run_id: str, stage: Stage, stage_id: str) -> dict | None:
        """Get artifact data if it exists."""
        artifact_path = self._run_dir(run_id) / f"{stage.value}_{stage_id}.json"
        if artifact_path.exists():
            with open(artifact_path) as f:
                return json.load(f)
        return None
    
    async def save_artifact(
        self, run_id: str, stage: Stage, stage_id: str, data: dict
    ) -> str:
        """Save artifact and return path."""
        artifact_path = self._run_dir(run_id) / f"{stage.value}_{stage_id}.json"
        with open(artifact_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return str(artifact_path)
    
    def _read_state(self, run_id: str) -> dict:
        """Read state file."""
        state_file = self._state_file(run_id)
        if not state_file.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        with open(state_file) as f:
            return json.load(f)
    
    def _write_state(self, run_id: str, state: dict) -> None:
        """Write state file."""
        state_file = self._state_file(run_id)
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)
