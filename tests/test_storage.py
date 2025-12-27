"""Tests for shared storage.

Tests for ArtifactStore and RegistryDB operations.
"""
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.contracts.core.artifact_registry import (
    ArtifactRecord,
    ArtifactType,
    ArtifactState,
    ArtifactQuery,
)
from shared.storage.artifact_store import ArtifactStore
from shared.storage.registry_db import RegistryDB


class TestArtifactStore:
    """Tests for ArtifactStore."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_workspace):
        """Create an ArtifactStore with temp workspace."""
        return ArtifactStore(workspace_path=temp_workspace)

    @pytest.mark.asyncio
    async def test_write_and_read_dataset(self, store):
        """Test writing and reading a DataSet."""
        # Create test data
        df = pl.DataFrame({
            "col1": [1.0, 2.0, 3.0],
            "col2": ["a", "b", "c"],
        })
        
        now = datetime.now(timezone.utc)
        manifest = DataSetManifest(
            dataset_id="ds_test123",
            name="Test Dataset",
            created_at=now,
            created_by_tool="dat",
            columns=[
                ColumnMeta(name="col1", dtype="float64"),
                ColumnMeta(name="col2", dtype="string"),
            ],
            row_count=3,
        )
        
        # Write dataset
        path = await store.write_dataset("ds_test123", df, manifest)
        assert path == Path("datasets/ds_test123")
        
        # Read back
        read_df = await store.read_dataset("ds_test123")
        assert len(read_df) == 3
        assert "col1" in read_df.columns
        
        # Get manifest
        read_manifest = await store.get_manifest("ds_test123")
        assert read_manifest.dataset_id == "ds_test123"
        assert read_manifest.name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_list_datasets(self, store):
        """Test listing datasets."""
        # Create multiple datasets
        for i in range(3):
            df = pl.DataFrame({"val": [i]})
            now = datetime.now(timezone.utc)
            manifest = DataSetManifest(
                dataset_id=f"ds_list_{i}",
                name=f"Dataset {i}",
                created_at=now,
                created_by_tool="dat" if i < 2 else "sov",
                columns=[ColumnMeta(name="val", dtype="int64")],
                row_count=1,
            )
            await store.write_dataset(f"ds_list_{i}", df, manifest)
        
        # List all
        all_refs = await store.list_datasets()
        assert len(all_refs) == 3
        
        # Filter by tool
        dat_refs = await store.list_datasets(tool="dat")
        assert len(dat_refs) == 2

    @pytest.mark.asyncio
    async def test_dataset_exists(self, store):
        """Test checking if dataset exists."""
        assert not await store.dataset_exists("ds_nonexistent")
        
        # Create a dataset
        df = pl.DataFrame({"val": [1]})
        now = datetime.now(timezone.utc)
        manifest = DataSetManifest(
            dataset_id="ds_exists",
            name="Existing",
            created_at=now,
            created_by_tool="dat",
            columns=[ColumnMeta(name="val", dtype="int64")],
            row_count=1,
        )
        await store.write_dataset("ds_exists", df, manifest)
        
        assert await store.dataset_exists("ds_exists")

    def test_relative_path_conversion(self, store):
        """Test path conversion utilities."""
        abs_path = store.workspace / "datasets" / "test"
        rel_path = store.get_relative_path(abs_path)
        assert rel_path == "datasets/test"
        
        back_to_abs = store.get_absolute_path(rel_path)
        assert back_to_abs == abs_path


class TestRegistryDB:
    """Tests for RegistryDB."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test.db"

    @pytest.fixture
    async def registry(self, temp_db):
        """Create and initialize a RegistryDB."""
        db = RegistryDB(db_path=temp_db)
        await db.initialize()
        return db

    @pytest.mark.asyncio
    async def test_register_and_get_artifact(self, registry):
        """Test registering and retrieving an artifact."""
        now = datetime.now(timezone.utc)
        record = ArtifactRecord(
            artifact_id="art_test123",
            artifact_type=ArtifactType.DATASET,
            name="Test Artifact",
            relative_path="datasets/art_test123",
            created_at=now,
            updated_at=now,
            created_by_tool="dat",
            size_bytes=1024,
        )
        
        await registry.register(record)
        
        retrieved = await registry.get("art_test123")
        assert retrieved is not None
        assert retrieved.artifact_id == "art_test123"
        assert retrieved.name == "Test Artifact"
        assert retrieved.size_bytes == 1024

    @pytest.mark.asyncio
    async def test_query_artifacts(self, registry):
        """Test querying artifacts with filters."""
        now = datetime.now(timezone.utc)
        
        # Register multiple artifacts
        for i in range(5):
            record = ArtifactRecord(
                artifact_id=f"art_query_{i}",
                artifact_type=ArtifactType.DATASET if i < 3 else ArtifactType.PIPELINE,
                name=f"Artifact {i}",
                relative_path=f"path/{i}",
                created_at=now,
                updated_at=now,
                created_by_tool="dat" if i % 2 == 0 else "sov",
            )
            await registry.register(record)
        
        # Query by type
        datasets = await registry.query(ArtifactQuery(
            artifact_type=ArtifactType.DATASET
        ))
        assert len(datasets) == 3
        
        # Query by tool
        dat_artifacts = await registry.query(ArtifactQuery(
            created_by_tool="dat"
        ))
        assert len(dat_artifacts) == 3

    @pytest.mark.asyncio
    async def test_update_state(self, registry):
        """Test updating artifact state (per ADR-0002)."""
        now = datetime.now(timezone.utc)
        record = ArtifactRecord(
            artifact_id="art_state",
            artifact_type=ArtifactType.DATASET,
            name="State Test",
            relative_path="path/state",
            created_at=now,
            updated_at=now,
            created_by_tool="dat",
        )
        await registry.register(record)
        
        # Update to locked
        await registry.update_state("art_state", ArtifactState.LOCKED)
        locked = await registry.get("art_state")
        assert locked.state == ArtifactState.LOCKED
        assert locked.locked_at is not None
        
        # Update to unlocked (artifact preserved per ADR-0002)
        await registry.update_state("art_state", ArtifactState.UNLOCKED)
        unlocked = await registry.get("art_state")
        assert unlocked.state == ArtifactState.UNLOCKED
        assert unlocked.unlocked_at is not None

    @pytest.mark.asyncio
    async def test_get_stats(self, registry):
        """Test getting registry statistics."""
        now = datetime.now(timezone.utc)
        
        for i in range(3):
            record = ArtifactRecord(
                artifact_id=f"art_stats_{i}",
                artifact_type=ArtifactType.DATASET,
                name=f"Stats {i}",
                relative_path=f"path/{i}",
                created_at=now,
                updated_at=now,
                created_by_tool="dat",
                size_bytes=100 * (i + 1),
            )
            await registry.register(record)
        
        stats = await registry.get_stats()
        assert stats.total_artifacts == 3
        assert stats.total_size_bytes == 600  # 100 + 200 + 300
        assert stats.by_type.get("dataset", 0) == 3
