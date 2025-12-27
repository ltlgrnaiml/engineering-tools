"""Tests for shared contracts.

Per ADR-0009: Contracts are the single source of truth.
These tests verify contract creation and validation.
"""
import pytest
from datetime import datetime, timezone

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta, DataSetRef
from shared.contracts.core.pipeline import (
    Pipeline,
    PipelineStep,
    PipelineStepType,
    PipelineStepState,
    CreatePipelineRequest,
)
from shared.contracts.core.artifact_registry import (
    ArtifactRecord,
    ArtifactType,
    ArtifactState,
    ArtifactQuery,
)


class TestDataSetContracts:
    """Tests for DataSet contracts."""

    def test_column_meta_creation(self):
        """Test creating a ColumnMeta."""
        col = ColumnMeta(
            name="test_column",
            dtype="float64",
            nullable=True,
            description="Test column",
            source_tool="dat",
        )
        assert col.name == "test_column"
        assert col.dtype == "float64"
        assert col.nullable is True
        assert col.source_tool == "dat"

    def test_dataset_manifest_creation(self):
        """Test creating a DataSetManifest."""
        now = datetime.now(timezone.utc)
        manifest = DataSetManifest(
            dataset_id="ds_test123456789",
            name="Test Dataset",
            created_at=now,
            created_by_tool="dat",
            columns=[
                ColumnMeta(name="col1", dtype="float64"),
                ColumnMeta(name="col2", dtype="string"),
            ],
            row_count=100,
        )
        assert manifest.dataset_id == "ds_test123456789"
        assert manifest.name == "Test Dataset"
        assert len(manifest.columns) == 2
        assert manifest.row_count == 100
        assert manifest.created_by_tool == "dat"

    def test_dataset_manifest_with_lineage(self):
        """Test DataSetManifest with parent lineage."""
        now = datetime.now(timezone.utc)
        manifest = DataSetManifest(
            dataset_id="ds_child123",
            name="Child Dataset",
            created_at=now,
            created_by_tool="sov",
            columns=[ColumnMeta(name="result", dtype="float64")],
            row_count=10,
            parent_dataset_ids=["ds_parent1", "ds_parent2"],
            analysis_type="anova",
        )
        assert len(manifest.parent_dataset_ids) == 2
        assert manifest.analysis_type == "anova"

    def test_dataset_ref_creation(self):
        """Test creating a DataSetRef."""
        now = datetime.now(timezone.utc)
        ref = DataSetRef(
            dataset_id="ds_ref123",
            name="Reference Dataset",
            created_at=now,
            created_by_tool="dat",
            row_count=500,
            column_count=10,
            parent_count=0,
        )
        assert ref.dataset_id == "ds_ref123"
        assert ref.column_count == 10


class TestPipelineContracts:
    """Tests for Pipeline contracts."""

    def test_pipeline_step_creation(self):
        """Test creating a PipelineStep."""
        step = PipelineStep(
            step_index=0,
            step_type=PipelineStepType.DAT_AGGREGATE,
            config={"source_files": ["test.csv"]},
        )
        assert step.step_index == 0
        assert step.step_type == PipelineStepType.DAT_AGGREGATE
        assert step.state == PipelineStepState.PENDING
        assert "source_files" in step.config

    def test_pipeline_creation(self):
        """Test creating a Pipeline."""
        now = datetime.now(timezone.utc)
        pipeline = Pipeline(
            pipeline_id="pipe_test123",
            name="Test Pipeline",
            created_at=now,
            steps=[
                PipelineStep(
                    step_index=0,
                    step_type=PipelineStepType.DAT_AGGREGATE,
                    config={"source_files": ["test.csv"]},
                ),
                PipelineStep(
                    step_index=1,
                    step_type=PipelineStepType.PPTX_GENERATE,
                    input_dataset_ids=["$step_0_output"],
                    config={},
                ),
            ],
        )
        assert pipeline.pipeline_id == "pipe_test123"
        assert len(pipeline.steps) == 2
        assert pipeline.state == "draft"

    def test_create_pipeline_request(self):
        """Test CreatePipelineRequest validation."""
        request = CreatePipelineRequest(
            name="New Pipeline",
            description="A test pipeline",
            steps=[
                PipelineStep(
                    step_index=0,
                    step_type=PipelineStepType.DAT_AGGREGATE,
                    config={},
                ),
            ],
            auto_execute=True,
        )
        assert request.name == "New Pipeline"
        assert request.auto_execute is True


class TestArtifactRegistryContracts:
    """Tests for ArtifactRegistry contracts."""

    def test_artifact_record_creation(self):
        """Test creating an ArtifactRecord."""
        now = datetime.now(timezone.utc)
        record = ArtifactRecord(
            artifact_id="art_test123",
            artifact_type=ArtifactType.DATASET,
            name="Test Artifact",
            relative_path="datasets/art_test123",
            created_at=now,
            updated_at=now,
            created_by_tool="dat",
        )
        assert record.artifact_id == "art_test123"
        assert record.artifact_type == ArtifactType.DATASET
        assert record.state == ArtifactState.ACTIVE

    def test_artifact_query_creation(self):
        """Test creating an ArtifactQuery."""
        query = ArtifactQuery(
            artifact_type=ArtifactType.DATASET,
            created_by_tool="dat",
            limit=10,
        )
        assert query.artifact_type == ArtifactType.DATASET
        assert query.limit == 10
        assert query.offset == 0
