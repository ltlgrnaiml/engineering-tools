"""Unit tests for shared contracts."""
from datetime import datetime, timezone

import pytest

from shared.contracts.core.dataset import (
    DataSetManifest,
    ColumnMeta,
    DataSetRef,
    DataSetPreview,
)
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


class TestDataSetManifest:
    """Tests for DataSetManifest contract."""

    def test_create_minimal_manifest(self):
        """Test creating a manifest with minimal required fields."""
        manifest = DataSetManifest(
            dataset_id="ds_test123",
            name="Test Dataset",
            created_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            columns=[
                ColumnMeta(name="col1", dtype="str"),
            ],
            row_count=100,
        )
        assert manifest.dataset_id == "ds_test123"
        assert manifest.name == "Test Dataset"
        assert manifest.row_count == 100
        assert len(manifest.columns) == 1

    def test_manifest_with_lineage(self):
        """Test creating a manifest with parent lineage."""
        manifest = DataSetManifest(
            dataset_id="ds_child123",
            name="Child Dataset",
            created_at=datetime.now(timezone.utc),
            created_by_tool="sov",
            columns=[ColumnMeta(name="result", dtype="float")],
            row_count=50,
            parent_dataset_ids=["ds_parent1", "ds_parent2"],
        )
        assert len(manifest.parent_dataset_ids) == 2
        assert "ds_parent1" in manifest.parent_dataset_ids

    def test_manifest_with_aggregation_levels(self):
        """Test creating a manifest with aggregation levels."""
        manifest = DataSetManifest(
            dataset_id="ds_agg123",
            name="Aggregated Dataset",
            created_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            columns=[ColumnMeta(name="mean_value", dtype="float")],
            row_count=10,
            aggregation_levels=["wafer", "lot"],
        )
        assert manifest.aggregation_levels == ["wafer", "lot"]


class TestDataSetRef:
    """Tests for DataSetRef contract."""

    def test_create_ref(self):
        """Test creating a dataset reference."""
        ref = DataSetRef(
            dataset_id="ds_test123",
            name="Test Dataset",
            created_by_tool="dat",
            row_count=100,
            created_at=datetime.now(timezone.utc),
        )
        assert ref.dataset_id == "ds_test123"


class TestPipeline:
    """Tests for Pipeline contract."""

    def test_create_pipeline(self):
        """Test creating a pipeline with steps."""
        pipeline = Pipeline(
            pipeline_id="pipe_test123",
            name="Test Pipeline",
            steps=[
                PipelineStep(
                    step_id="step_1",
                    step_type=PipelineStepType.DAT,
                    config={"files": ["test.csv"]},
                ),
                PipelineStep(
                    step_id="step_2",
                    step_type=PipelineStepType.SOV,
                    config={"factors": ["tool"]},
                    input_dataset_id="$step_1.output",
                ),
            ],
            created_at=datetime.now(timezone.utc),
        )
        assert pipeline.pipeline_id == "pipe_test123"
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0].step_type == PipelineStepType.DAT

    def test_pipeline_step_states(self):
        """Test pipeline step state transitions."""
        step = PipelineStep(
            step_id="step_1",
            step_type=PipelineStepType.PPTX,
            config={},
            state=PipelineStepState.PENDING,
        )
        assert step.state == PipelineStepState.PENDING


class TestArtifactRecord:
    """Tests for ArtifactRecord contract."""

    def test_create_artifact_record(self):
        """Test creating an artifact record."""
        record = ArtifactRecord(
            artifact_id="ds_test123",
            artifact_type=ArtifactType.DATASET,
            name="Test Dataset",
            relative_path="datasets/ds_test123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by_tool="dat",
            size_bytes=1024,
            row_count=100,
        )
        assert record.artifact_type == ArtifactType.DATASET
        assert record.state == ArtifactState.ACTIVE

    def test_artifact_query(self):
        """Test artifact query parameters."""
        query = ArtifactQuery(
            artifact_type=ArtifactType.DATASET,
            created_by_tool="dat",
            limit=10,
        )
        assert query.limit == 10
        assert query.offset == 0
