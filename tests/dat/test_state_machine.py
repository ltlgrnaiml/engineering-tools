"""Tests for DAT state machine and run management."""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from apps.data_aggregator.backend.src.dat_aggregation.core.state_machine import (
    DATStateMachine,
    Stage,
    StageState,
    StageStatus,
    FORWARD_GATES,
    CASCADE_TARGETS,
)
from apps.data_aggregator.backend.src.dat_aggregation.core.run_store import RunStore
from apps.data_aggregator.backend.src.dat_aggregation.core.run_manager import RunManager


class TestStageEnum:
    """Test Stage and StageState enums."""
    
    def test_all_stages_defined(self):
        """Test all expected stages are defined."""
        expected_stages = [
            "selection", "context", "table_availability",
            "table_selection", "preview", "parse", "export"
        ]
        
        for stage in expected_stages:
            assert Stage(stage) is not None
    
    def test_stage_state_values(self):
        """Test stage state values."""
        assert StageState.UNLOCKED.value == "unlocked"
        assert StageState.LOCKED.value == "locked"


class TestForwardGating:
    """Test forward gating rules."""
    
    def test_selection_has_no_gates(self):
        """Test selection stage has no forward gates."""
        gates = FORWARD_GATES.get(Stage.SELECTION, [])
        assert len(gates) == 0
    
    def test_context_requires_selection(self):
        """Test context stage requires selection."""
        gates = FORWARD_GATES.get(Stage.CONTEXT, [])
        
        required_stages = [g[0] for g in gates]
        assert Stage.SELECTION in required_stages
    
    def test_parse_requires_table_selection(self):
        """Test parse stage requires table selection."""
        gates = FORWARD_GATES.get(Stage.PARSE, [])
        
        required_stages = [g[0] for g in gates]
        assert Stage.TABLE_SELECTION in required_stages
    
    def test_export_requires_completed_parse(self):
        """Test export requires completed parse."""
        gates = FORWARD_GATES.get(Stage.EXPORT, [])
        
        # Find parse gate
        parse_gate = next((g for g in gates if g[0] == Stage.PARSE), None)
        assert parse_gate is not None
        assert parse_gate[1] is True  # must_be_completed = True


class TestCascadeUnlock:
    """Test cascade unlock rules."""
    
    def test_selection_cascades_to_all_downstream(self):
        """Test selection unlock cascades to all downstream stages."""
        targets = CASCADE_TARGETS.get(Stage.SELECTION, [])
        
        assert Stage.CONTEXT in targets
        assert Stage.TABLE_AVAILABILITY in targets
        assert Stage.TABLE_SELECTION in targets
        assert Stage.PARSE in targets
        assert Stage.EXPORT in targets
    
    def test_context_does_not_cascade(self):
        """Test context stage does not cascade (per ADR-0003)."""
        targets = CASCADE_TARGETS.get(Stage.CONTEXT, [])
        assert len(targets) == 0
    
    def test_preview_does_not_cascade(self):
        """Test preview stage does not cascade (per ADR-0003)."""
        targets = CASCADE_TARGETS.get(Stage.PREVIEW, [])
        assert len(targets) == 0
    
    def test_parse_cascades_to_export(self):
        """Test parse unlock cascades to export."""
        targets = CASCADE_TARGETS.get(Stage.PARSE, [])
        assert Stage.EXPORT in targets


class TestRunStore:
    """Test run storage functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def run_store(self, temp_workspace):
        """Create run store with temp workspace."""
        return RunStore(workspace_path=temp_workspace)
    
    @pytest.mark.asyncio
    async def test_create_run(self, run_store):
        """Test creating a new run."""
        run = await run_store.create_run("test-run-123", name="Test Run")
        
        assert run["run_id"] == "test-run-123"
        assert run["name"] == "Test Run"
        assert "created_at" in run
    
    @pytest.mark.asyncio
    async def test_get_run(self, run_store):
        """Test getting a run by ID."""
        await run_store.create_run("test-run-123", name="Test Run")
        
        run = await run_store.get_run("test-run-123")
        
        assert run is not None
        assert run["run_id"] == "test-run-123"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_run(self, run_store):
        """Test getting a nonexistent run returns None."""
        run = await run_store.get_run("nonexistent")
        assert run is None
    
    @pytest.mark.asyncio
    async def test_list_runs(self, run_store):
        """Test listing runs."""
        await run_store.create_run("run-1", name="Run 1")
        await run_store.create_run("run-2", name="Run 2")
        
        runs = await run_store.list_runs()
        
        assert len(runs) == 2
    
    @pytest.mark.asyncio
    async def test_get_stage_status_default(self, run_store):
        """Test getting default stage status (unlocked)."""
        await run_store.create_run("test-run-123")
        
        status = await run_store.get_stage_status("test-run-123", Stage.SELECTION)
        
        assert status.stage == Stage.SELECTION
        assert status.state == StageState.UNLOCKED
        assert status.stage_id is None
    
    @pytest.mark.asyncio
    async def test_set_stage_status(self, run_store):
        """Test setting stage status."""
        await run_store.create_run("test-run-123")
        
        status = StageStatus(
            stage=Stage.SELECTION,
            state=StageState.LOCKED,
            stage_id="sel_abc123",
            locked_at=datetime.now(timezone.utc),
            completed=True,
        )
        
        await run_store.set_stage_status("test-run-123", Stage.SELECTION, status)
        
        retrieved = await run_store.get_stage_status("test-run-123", Stage.SELECTION)
        
        assert retrieved.state == StageState.LOCKED
        assert retrieved.stage_id == "sel_abc123"
        assert retrieved.completed is True
    
    @pytest.mark.asyncio
    async def test_save_and_get_artifact(self, run_store):
        """Test saving and retrieving artifacts."""
        await run_store.create_run("test-run-123")
        
        artifact_data = {
            "files": ["file1.json", "file2.json"],
            "completed": True,
        }
        
        await run_store.save_artifact(
            "test-run-123",
            Stage.SELECTION,
            "sel_abc123",
            artifact_data
        )
        
        retrieved = await run_store.get_artifact("test-run-123", Stage.SELECTION, "sel_abc123")
        
        assert retrieved is not None
        assert retrieved["files"] == ["file1.json", "file2.json"]
        assert retrieved["completed"] is True
    
    @pytest.mark.asyncio
    async def test_get_all_stage_statuses(self, run_store):
        """Test getting all stage statuses."""
        await run_store.create_run("test-run-123")
        
        statuses = await run_store.get_all_stage_statuses("test-run-123")
        
        assert len(statuses) == len(Stage)
        for stage in Stage:
            assert stage in statuses


class TestDATStateMachine:
    """Test DAT state machine functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def run_store(self, temp_workspace):
        """Create run store with temp workspace."""
        return RunStore(workspace_path=temp_workspace)
    
    @pytest.fixture
    async def state_machine(self, run_store):
        """Create state machine for a test run."""
        await run_store.create_run("test-run-123")
        return DATStateMachine("test-run-123", run_store)
    
    @pytest.mark.asyncio
    async def test_can_lock_selection(self, state_machine):
        """Test selection can always be locked (no gates)."""
        can_lock, reason = await state_machine.can_lock(Stage.SELECTION)
        
        assert can_lock is True
        assert reason is None
    
    @pytest.mark.asyncio
    async def test_cannot_lock_parse_without_table_selection(self, state_machine):
        """Test parse cannot be locked without table selection."""
        can_lock, reason = await state_machine.can_lock(Stage.PARSE)
        
        assert can_lock is False
        assert "table_selection" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_lock_selection_stage(self, state_machine):
        """Test locking selection stage."""
        async def execute():
            return {"files": ["test.json"], "completed": True}
        
        status = await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute,
        )
        
        assert status.state == StageState.LOCKED
        assert status.stage_id is not None
        assert status.completed is True
    
    @pytest.mark.asyncio
    async def test_lock_stage_idempotent(self, state_machine):
        """Test that locking with same inputs is idempotent."""
        async def execute():
            return {"files": ["test.json"], "completed": True}
        
        inputs = {"paths": ["/test"]}
        
        status1 = await state_machine.lock_stage(
            Stage.SELECTION,
            inputs=inputs,
            execute_fn=execute,
        )
        
        status2 = await state_machine.lock_stage(
            Stage.SELECTION,
            inputs=inputs,
            execute_fn=execute,
        )
        
        # Same stage_id due to same inputs (per ADR-0004)
        assert status1.stage_id == status2.stage_id
    
    @pytest.mark.asyncio
    async def test_unlock_stage(self, state_machine):
        """Test unlocking a stage."""
        # First lock selection
        async def execute():
            return {"completed": True}
        
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute,
        )
        
        # Now unlock
        unlocked = await state_machine.unlock_stage(Stage.SELECTION)
        
        assert len(unlocked) >= 1
        assert unlocked[0].stage == Stage.SELECTION
        assert unlocked[0].state == StageState.UNLOCKED
    
    @pytest.mark.asyncio
    async def test_unlock_cascades(self, state_machine):
        """Test that unlock cascades to downstream stages."""
        # Lock selection
        async def execute():
            return {"completed": True}
        
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute,
        )
        
        # Lock table_availability (which depends on selection)
        await state_machine.lock_stage(
            Stage.TABLE_AVAILABILITY,
            inputs={"run_id": "test"},
            execute_fn=execute,
        )
        
        # Unlock selection - should cascade to table_availability
        unlocked = await state_machine.unlock_stage(Stage.SELECTION)
        
        unlocked_stages = {s.stage for s in unlocked}
        assert Stage.SELECTION in unlocked_stages
        assert Stage.TABLE_AVAILABILITY in unlocked_stages
    
    @pytest.mark.asyncio
    async def test_get_all_statuses(self, state_machine):
        """Test getting all stage statuses."""
        statuses = await state_machine.get_all_statuses()
        
        assert len(statuses) == len(Stage)
        for stage in Stage:
            assert stage in statuses


class TestRunManager:
    """Test run manager functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def run_manager(self, temp_workspace):
        """Create run manager with temp workspace."""
        return RunManager(workspace_path=temp_workspace)
    
    @pytest.mark.asyncio
    async def test_create_run(self, run_manager):
        """Test creating a run through manager."""
        run = await run_manager.create_run(name="Test Run")
        
        assert run["run_id"] is not None
        assert run["name"] == "Test Run"
    
    @pytest.mark.asyncio
    async def test_create_run_generates_unique_ids(self, run_manager):
        """Test that each created run has a unique ID."""
        run1 = await run_manager.create_run()
        run2 = await run_manager.create_run()
        
        assert run1["run_id"] != run2["run_id"]
    
    @pytest.mark.asyncio
    async def test_get_state_machine(self, run_manager):
        """Test getting state machine for a run."""
        run = await run_manager.create_run()
        
        sm = run_manager.get_state_machine(run["run_id"])
        
        assert sm is not None
        assert sm.run_id == run["run_id"]
    
    @pytest.mark.asyncio
    async def test_list_runs(self, run_manager):
        """Test listing runs through manager."""
        await run_manager.create_run(name="Run 1")
        await run_manager.create_run(name="Run 2")
        
        runs = await run_manager.list_runs()
        
        assert len(runs) == 2
