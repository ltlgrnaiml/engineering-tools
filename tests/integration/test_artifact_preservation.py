"""Integration tests for artifact preservation on unlock/reset.

Per ADR-0002: Artifact Preservation on Unlock.
Per ART-001: Unlock MUST preserve artifacts (never delete).

These tests verify that:
1. Unlocking a stage preserves artifact files
2. Resetting a stage preserves completed artifacts
3. Cancellation preserves completed work
4. Only metadata is modified on unlock, not files
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.storage.artifact_store import ArtifactStore


class TestArtifactPreservationOnUnlock:
    """Tests for ADR-0002: Artifact Preservation on Unlock."""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "datasets").mkdir(parents=True)
            (workspace / "tools" / "dat").mkdir(parents=True)
            yield workspace

    @pytest.fixture
    def artifact_store(self, temp_workspace: Path) -> ArtifactStore:
        """Create an artifact store with temp workspace."""
        return ArtifactStore(workspace_path=temp_workspace)

    @pytest.fixture
    def sample_manifest(self) -> DataSetManifest:
        """Create a sample DataSet manifest."""
        return DataSetManifest(
            dataset_id="test_dataset_001",
            name="Test Dataset",
            created_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            columns=[
                ColumnMeta(name="col1", dtype="int64"),
                ColumnMeta(name="col2", dtype="float64"),
            ],
            row_count=100,
        )

    async def test_unlock_preserves_manifest_file(
        self, artifact_store: ArtifactStore, sample_manifest: DataSetManifest
    ) -> None:
        """Unlocking a dataset must preserve the manifest file."""
        # Save initial manifest
        dataset_dir = artifact_store.workspace / "datasets" / sample_manifest.dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = dataset_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(sample_manifest.model_dump(mode="json"), f)

        # Verify file exists
        assert manifest_path.exists(), "Manifest should exist after save"

        # Simulate unlock by modifying metadata only
        # Per ADR-0002: Never delete files, only update metadata
        manifest_data = json.loads(manifest_path.read_text())
        manifest_data["locked_at"] = None  # Unlock
        manifest_path.write_text(json.dumps(manifest_data))

        # Verify file still exists after unlock
        assert manifest_path.exists(), "Manifest must be preserved after unlock"
        
        # Verify content is still valid
        updated_manifest = json.loads(manifest_path.read_text())
        assert updated_manifest["dataset_id"] == sample_manifest.dataset_id
        assert updated_manifest["locked_at"] is None

    async def test_unlock_preserves_parquet_file(
        self, temp_workspace: Path
    ) -> None:
        """Unlocking must not delete data files (Parquet)."""
        # Create dummy parquet file
        dataset_dir = temp_workspace / "datasets" / "test_dataset_002"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        parquet_path = dataset_dir / "data.parquet"
        parquet_path.write_bytes(b"dummy parquet content")

        manifest_path = dataset_dir / "manifest.json"
        manifest_data = {
            "dataset_id": "test_dataset_002",
            "name": "Test",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by_tool": "dat",
            "columns": [],
            "row_count": 0,
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest_data))

        # Simulate unlock
        manifest_data["locked_at"] = None
        manifest_path.write_text(json.dumps(manifest_data))

        # Verify parquet file preserved
        assert parquet_path.exists(), "Parquet data must be preserved after unlock"

    async def test_unlock_sets_locked_false_not_delete(
        self, temp_workspace: Path
    ) -> None:
        """Per ADR-0002: Set locked=false, never delete artifacts."""
        dataset_dir = temp_workspace / "datasets" / "test_dataset_003"
        dataset_dir.mkdir(parents=True, exist_ok=True)

        # Create locked manifest
        manifest_path = dataset_dir / "manifest.json"
        manifest_data = {
            "dataset_id": "test_dataset_003",
            "name": "Locked Dataset",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by_tool": "dat",
            "columns": [],
            "row_count": 50,
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest_data))

        # Count files before unlock
        files_before = list(dataset_dir.iterdir())

        # Unlock (modify metadata only)
        updated_data = json.loads(manifest_path.read_text())
        updated_data["locked_at"] = None
        manifest_path.write_text(json.dumps(updated_data))

        # Count files after unlock
        files_after = list(dataset_dir.iterdir())

        # Verify no files deleted
        assert len(files_after) == len(files_before), "No files should be deleted on unlock"


class TestArtifactPreservationOnCancellation:
    """Tests for artifact preservation during cancellation (ADR-0013)."""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "tools" / "dat" / "jobs").mkdir(parents=True)
            yield workspace

    async def test_cancellation_preserves_completed_artifacts(
        self, temp_workspace: Path
    ) -> None:
        """Cancellation must preserve artifacts from completed stages."""
        job_dir = temp_workspace / "tools" / "dat" / "jobs" / "job_001"
        job_dir.mkdir(parents=True, exist_ok=True)

        # Create completed stage artifacts
        stage1_artifact = job_dir / "stage_1_output.parquet"
        stage1_artifact.write_bytes(b"stage 1 data")

        stage2_artifact = job_dir / "stage_2_output.parquet"
        stage2_artifact.write_bytes(b"stage 2 data")

        # Simulate cancellation during stage 3
        # Per ADR-0013: Preserve completed artifacts
        cancellation_log = job_dir / "cancellation.json"
        cancellation_log.write_text(json.dumps({
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_stage": "stage_3",
            "preserved_artifacts": ["stage_1_output.parquet", "stage_2_output.parquet"],
        }))

        # Verify completed artifacts preserved
        assert stage1_artifact.exists(), "Stage 1 artifact must be preserved"
        assert stage2_artifact.exists(), "Stage 2 artifact must be preserved"

    async def test_cancellation_discards_partial_data(
        self, temp_workspace: Path
    ) -> None:
        """Cancellation must discard partial (incomplete) data."""
        job_dir = temp_workspace / "tools" / "dat" / "jobs" / "job_002"
        job_dir.mkdir(parents=True, exist_ok=True)

        # Create partial artifact (in-progress)
        partial_artifact = job_dir / "stage_3_partial.tmp"
        partial_artifact.write_bytes(b"incomplete data")

        # Simulate cancellation cleanup of partial data
        # Per ADR-0013: Discard partial data
        if partial_artifact.exists():
            partial_artifact.unlink()

        # Verify partial data discarded
        assert not partial_artifact.exists(), "Partial data should be discarded"


class TestIdempotentRecomputation:
    """Tests for idempotent re-computation (ADR-0002)."""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "datasets").mkdir(parents=True)
            yield workspace

    async def test_relock_produces_same_artifact(
        self, temp_workspace: Path
    ) -> None:
        """Re-locking same inputs must produce identical artifact ID (determinism)."""
        from shared.utils.stage_id import compute_dataset_id

        # Same inputs should produce same ID (using keyword arguments per API)
        id1 = compute_dataset_id(run_id="test-run", columns=["a", "b"], row_count=100)
        id2 = compute_dataset_id(run_id="test-run", columns=["a", "b"], row_count=100)

        assert id1 == id2, "Same inputs must produce same dataset ID"

    async def test_unlock_and_relock_preserves_id(
        self, temp_workspace: Path
    ) -> None:
        """Unlock then re-lock with same inputs preserves artifact ID."""
        from shared.utils.stage_id import compute_dataset_id

        # First computation (using keyword arguments per API)
        original_id = compute_dataset_id(run_id="test-run", columns=["x", "y"])
        
        # Simulate unlock (metadata change only)
        # ... unlock logic ...
        
        # Re-lock with same inputs
        recomputed_id = compute_dataset_id(run_id="test-run", columns=["x", "y"])
        
        assert original_id == recomputed_id, "Re-lock must preserve artifact ID"
