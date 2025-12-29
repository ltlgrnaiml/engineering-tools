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
)
from apps.data_aggregator.backend.src.dat_aggregation.core.run_store import RunStore
from apps.data_aggregator.backend.src.dat_aggregation.core.run_manager import RunManager


class TestStageEnum:
    """Test Stage and StageState enums."""
    
    def test_all_stages_defined(self):
        """Test all expected stages are defined per ADR-0001-DAT."""
        expected_stages = [
            "discovery", "selection", "context", "table_availability",
            "table_selection", "preview", "parse", "export"
        ]
        
        for stage in expected_stages:
            assert Stage(stage) is not None
    
    def test_stage_state_values(self):
        """Test stage state values."""
        assert StageState.UNLOCKED.value == "unlocked"
        assert StageState.LOCKED.value == "locked"


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
    async def test_can_lock_discovery(self, state_machine):
        """Test discovery can always be locked (first stage, no gates)."""
        can_lock, reason = await state_machine.can_lock(Stage.DISCOVERY)
        
        assert can_lock is True
        assert reason is None
    
    @pytest.mark.asyncio
    async def test_can_lock_selection_after_discovery(self, state_machine):
        """Test selection can be locked after discovery."""
        async def execute():
            return {"completed": True}
        
        # First lock discovery
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute,
        )
        
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
    async def test_lock_discovery_stage(self, state_machine):
        """Test locking discovery stage (first stage)."""
        async def execute():
            return {"files": ["test.json"], "completed": True}
        
        status = await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
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
        
        inputs = {"path": "/test"}
        
        status1 = await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs=inputs,
            execute_fn=execute,
        )
        
        status2 = await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs=inputs,
            execute_fn=execute,
        )
        
        # Same stage_id due to same inputs (per ADR-0004)
        assert status1.stage_id == status2.stage_id
    
    @pytest.mark.asyncio
    async def test_unlock_stage(self, state_machine):
        """Test unlocking a stage."""
        # First lock discovery
        async def execute():
            return {"completed": True}
        
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute,
        )
        
        # Now unlock
        unlocked = await state_machine.unlock_stage(Stage.DISCOVERY)
        
        assert len(unlocked) >= 1
        assert unlocked[0].stage == Stage.DISCOVERY
        assert unlocked[0].state == StageState.UNLOCKED
    
    @pytest.mark.asyncio
    async def test_unlock_cascades(self, state_machine):
        """Test that unlock cascades to downstream stages."""
        async def execute():
            return {"completed": True}
        
        # Lock discovery first
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute,
        )
        
        # Lock selection
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute,
        )
        
        # Unlock discovery - should cascade to selection
        unlocked = await state_machine.unlock_stage(Stage.DISCOVERY)
        
        unlocked_stages = {s.stage for s in unlocked}
        assert Stage.DISCOVERY in unlocked_stages
        assert Stage.SELECTION in unlocked_stages
    
    @pytest.mark.asyncio
    async def test_get_all_statuses(self, state_machine):
        """Test getting all stage statuses."""
        statuses = await state_machine.get_all_statuses()
        
        assert len(statuses) == len(Stage)
        for stage in Stage:
            assert stage in statuses


class TestFSMTransitionValidation:
    """Test FSM transition validation per ADR-0001.

    These tests verify that the state machine correctly enforces:
    - Forward gating rules (can't proceed without prerequisites)
    - Cascade unlock behavior (changes propagate downstream)
    - Idempotent re-locking with same inputs
    """

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
        await run_store.create_run("test-run-fsm")
        return DATStateMachine("test-run-fsm", run_store)

    @pytest.mark.asyncio
    async def test_cannot_lock_export_without_completed_parse(self, state_machine):
        """Test export requires COMPLETED parse (not just locked)."""
        async def execute():
            return {"completed": False}  # Parse not completed

        # Lock prerequisite stages including discovery
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute,
        )
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute,
        )
        await state_machine.lock_stage(
            Stage.TABLE_AVAILABILITY,
            inputs={"run_id": "test"},
            execute_fn=execute,
        )
        await state_machine.lock_stage(
            Stage.TABLE_SELECTION,
            inputs={"run_id": "test"},
            execute_fn=execute,
        )
        # Lock parse but NOT completed
        await state_machine.lock_stage(
            Stage.PARSE,
            inputs={"run_id": "test"},
            execute_fn=execute,
        )

        # Export should fail because parse is not completed
        can_lock, reason = await state_machine.can_lock(Stage.EXPORT)
        assert can_lock is False
        assert "completed" in reason.lower() or "parse" in reason.lower()

    @pytest.mark.asyncio
    async def test_can_lock_export_with_completed_parse(self, state_machine):
        """Test export can proceed when parse is completed."""
        async def execute_complete():
            return {"completed": True}

        # Lock all prerequisite stages with completed=True, starting with discovery
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.TABLE_AVAILABILITY,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.TABLE_SELECTION,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.PARSE,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )

        # Export should succeed
        can_lock, reason = await state_machine.can_lock(Stage.EXPORT)
        assert can_lock is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_full_pipeline_lock_sequence(self, state_machine):
        """Test locking stages in correct order through entire pipeline."""
        async def execute_complete():
            return {"completed": True}

        stages_in_order = [
            Stage.DISCOVERY,
            Stage.SELECTION,
            Stage.TABLE_AVAILABILITY,
            Stage.TABLE_SELECTION,
            Stage.PARSE,
            Stage.EXPORT,
        ]

        for stage in stages_in_order:
            status = await state_machine.lock_stage(
                stage,
                inputs={"run_id": "test", "stage": stage.value},
                execute_fn=execute_complete,
            )
            assert status.state == StageState.LOCKED
            assert status.completed is True

    @pytest.mark.asyncio
    async def test_context_and_preview_are_optional(self, state_machine):
        """Test that context and preview stages are optional per ADR-0003."""
        async def execute_complete():
            return {"completed": True}

        # Lock discovery and selection first
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute_complete,
        )

        # Skip context, lock table_availability directly
        can_lock, reason = await state_machine.can_lock(Stage.TABLE_AVAILABILITY)
        assert can_lock is True

        await state_machine.lock_stage(
            Stage.TABLE_AVAILABILITY,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.TABLE_SELECTION,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )

        # Skip preview, lock parse directly
        can_lock, reason = await state_machine.can_lock(Stage.PARSE)
        assert can_lock is True

    @pytest.mark.asyncio
    async def test_cascade_unlock_preserves_artifacts(self, run_store, state_machine):
        """Test that cascade unlock preserves artifacts per ADR-0002."""
        async def execute_complete():
            return {"completed": True, "data": "important"}

        # Lock stages, starting with discovery
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute_complete,
        )

        # Get artifact ID before unlock
        statuses = await state_machine.get_all_statuses()
        sel_stage_id = statuses[Stage.SELECTION].stage_id

        # Unlock discovery (should cascade to selection)
        await state_machine.unlock_stage(Stage.DISCOVERY)

        # Artifact should still exist (preserved per ADR-0002)
        artifact = await run_store.get_artifact(
            "test-run-fsm", Stage.SELECTION, sel_stage_id
        )
        assert artifact is not None

    @pytest.mark.asyncio
    async def test_context_unlock_does_not_cascade(self, state_machine):
        """Test that unlocking context does not cascade per ADR-0003."""
        async def execute_complete():
            return {"completed": True}

        # Lock discovery, selection, context and table_availability
        await state_machine.lock_stage(
            Stage.DISCOVERY,
            inputs={"path": "/test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.SELECTION,
            inputs={"paths": ["/test"]},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.CONTEXT,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )
        await state_machine.lock_stage(
            Stage.TABLE_AVAILABILITY,
            inputs={"run_id": "test"},
            execute_fn=execute_complete,
        )

        # Unlock context - should NOT cascade to table_availability
        unlocked = await state_machine.unlock_stage(Stage.CONTEXT)

        unlocked_stages = {s.stage for s in unlocked}
        assert Stage.CONTEXT in unlocked_stages
        assert Stage.TABLE_AVAILABILITY not in unlocked_stages

        # table_availability should still be locked
        statuses = await state_machine.get_all_statuses()
        assert statuses[Stage.TABLE_AVAILABILITY].state == StageState.LOCKED


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
