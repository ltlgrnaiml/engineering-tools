"""Unit tests for ArtifactStore."""
from datetime import datetime, timezone
from pathlib import Path

import pytest
import polars as pl

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.storage.artifact_store import ArtifactStore


class TestArtifactStore:
    """Tests for ArtifactStore class."""

    def test_init_creates_directories(self, temp_workspace: Path):
        """Store initialization creates required directories."""
        store = ArtifactStore(workspace_root=temp_workspace)
        
        assert (temp_workspace / "datasets").exists()
        assert (temp_workspace / "pipelines").exists()
        assert (temp_workspace / "reports").exists()

    def test_write_and_read_dataset(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test writing and reading a dataset."""
        dataset_id = "ds_test123"
        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name="Test Dataset",
            created_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            columns=[
                ColumnMeta(name=col, dtype=str(sample_dataframe[col].dtype))
                for col in sample_dataframe.columns
            ],
            row_count=len(sample_dataframe),
        )
        
        # Write
        artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)
        
        # Read back
        read_df, read_manifest = artifact_store.read_dataset(dataset_id)
        
        assert read_manifest.dataset_id == dataset_id
        assert read_manifest.name == "Test Dataset"
        assert len(read_df) == len(sample_dataframe)

    def test_dataset_exists(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test checking if dataset exists."""
        dataset_id = "ds_exists123"
        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name="Test",
            created_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            columns=[ColumnMeta(name="col", dtype="str")],
            row_count=1,
        )
        
        assert not artifact_store.dataset_exists(dataset_id)
        
        artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)
        
        assert artifact_store.dataset_exists(dataset_id)

    def test_list_datasets(self, artifact_store: ArtifactStore, sample_dataframe):
        """Test listing all datasets."""
        # Create a few datasets
        for i in range(3):
            dataset_id = f"ds_list{i}"
            manifest = DataSetManifest(
                dataset_id=dataset_id,
                name=f"Dataset {i}",
                created_at=datetime.now(timezone.utc),
                created_by_tool="dat",
                columns=[ColumnMeta(name="col", dtype="str")],
                row_count=1,
            )
            artifact_store.write_dataset(dataset_id, sample_dataframe, manifest)
        
        datasets = artifact_store.list_datasets()
        
        assert len(datasets) >= 3
        dataset_ids = [d.dataset_id for d in datasets]
        assert "ds_list0" in dataset_ids
        assert "ds_list1" in dataset_ids
        assert "ds_list2" in dataset_ids

    def test_path_safety_rejects_traversal(self, artifact_store: ArtifactStore):
        """Test that path traversal is rejected."""
        with pytest.raises(ValueError, match="path"):
            artifact_store._validate_path("../../../etc/passwd")

    def test_get_dataset_path(self, artifact_store: ArtifactStore):
        """Test getting dataset file paths."""
        dataset_id = "ds_path123"
        
        parquet_path, manifest_path = artifact_store.get_dataset_paths(dataset_id)
        
        assert parquet_path.name == f"{dataset_id}.parquet"
        assert manifest_path.name == f"{dataset_id}.manifest.json"
        assert "datasets" in str(parquet_path)
