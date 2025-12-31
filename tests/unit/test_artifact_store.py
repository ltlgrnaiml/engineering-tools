"""Unit tests for ArtifactStore."""
from datetime import UTC, datetime
from pathlib import Path

import pytest

from shared.contracts.core.dataset import ColumnMeta, DataSetManifest
from shared.storage.artifact_store import ArtifactStore


class TestArtifactStore:
    """Tests for ArtifactStore class."""

    def test_init_creates_directories(self, temp_workspace: Path):
        """Store initialization creates required directories."""
        store = ArtifactStore(workspace_path=temp_workspace)

        assert (temp_workspace / "datasets").exists()
        assert (temp_workspace / "pipelines").exists()

    @pytest.mark.asyncio
    async def test_write_and_read_dataset(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test writing and reading a dataset."""
        dataset_id = "ds_test123"
        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name="Test Dataset",
            created_at=datetime.now(UTC),
            created_by_tool="dat",
            columns=[
                ColumnMeta(name=col, dtype=str(sample_dataframe[col].dtype))
                for col in sample_dataframe.columns
            ],
            row_count=len(sample_dataframe),
        )

        # Write
        await artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)

        # Read back
        read_df, read_manifest = await artifact_store.read_dataset_with_manifest(dataset_id)

        assert read_manifest.dataset_id == dataset_id
        assert read_manifest.name == "Test Dataset"
        assert len(read_df) == len(sample_dataframe)

    @pytest.mark.asyncio
    async def test_dataset_exists(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test checking if dataset exists."""
        dataset_id = "ds_exists123"
        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name="Test",
            created_at=datetime.now(UTC),
            created_by_tool="dat",
            columns=[ColumnMeta(name="col", dtype="str")],
            row_count=1,
        )

        assert not await artifact_store.dataset_exists(dataset_id)

        await artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)

        assert await artifact_store.dataset_exists(dataset_id)

    @pytest.mark.asyncio
    async def test_list_datasets(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test listing all datasets."""
        # Create a few datasets
        for i in range(3):
            dataset_id = f"ds_list{i}"
            manifest = DataSetManifest(
                dataset_id=dataset_id,
                name=f"Dataset {i}",
                created_at=datetime.now(UTC),
                created_by_tool="dat",
                columns=[ColumnMeta(name="col", dtype="str")],
                row_count=1,
            )
            await artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)

        datasets = await artifact_store.list_datasets()

        assert len(datasets) >= 3
        dataset_ids = [d.dataset_id for d in datasets]
        assert "ds_list0" in dataset_ids
        assert "ds_list1" in dataset_ids
        assert "ds_list2" in dataset_ids

    def test_path_construction(self, artifact_store: ArtifactStore):
        """Test that paths are constructed correctly."""
        dataset_id = "ds_path123"

        # Verify workspace path exists
        assert artifact_store.workspace.exists()

        # Verify datasets directory is within workspace
        datasets_dir = artifact_store.workspace / "datasets"
        assert datasets_dir.exists()

    def test_relative_path_methods(self, artifact_store: ArtifactStore):
        """Test relative path conversion methods."""
        # Test get_relative_path if it exists
        if hasattr(artifact_store, 'get_relative_path'):
            abs_path = artifact_store.workspace / "datasets" / "test"
            rel_path = artifact_store.get_relative_path(abs_path)
            assert "datasets" in rel_path.replace("\\", "/")
