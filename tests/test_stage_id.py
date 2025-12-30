"""Tests for deterministic ID generation.

Per ADR-0005: IDs must be deterministic (same inputs = same ID).
"""
import pytest

from shared.utils.stage_id import (
    compute_stage_id,
    compute_dataset_id,
    compute_pipeline_id,
)


class TestStageIdGeneration:
    """Tests for stage ID generation."""

    def test_compute_stage_id_deterministic(self):
        """Test that same inputs produce same ID."""
        inputs = {"key": "value", "number": 42}
        
        id1 = compute_stage_id(inputs)
        id2 = compute_stage_id(inputs)
        
        assert id1 == id2

    def test_compute_stage_id_with_prefix(self):
        """Test stage ID with prefix."""
        inputs = {"test": True}
        
        stage_id = compute_stage_id(inputs, prefix="stg_")
        
        assert stage_id.startswith("stg_")
        assert len(stage_id) == 4 + 8  # prefix + 8 hex chars per ADR-0008

    def test_compute_stage_id_different_inputs(self):
        """Test that different inputs produce different IDs."""
        id1 = compute_stage_id({"key": "value1"})
        id2 = compute_stage_id({"key": "value2"})
        
        assert id1 != id2

    def test_compute_stage_id_order_independent(self):
        """Test that key order doesn't affect ID (sorted keys)."""
        id1 = compute_stage_id({"a": 1, "b": 2, "c": 3})
        id2 = compute_stage_id({"c": 3, "b": 2, "a": 1})
        
        assert id1 == id2


class TestDatasetIdGeneration:
    """Tests for dataset ID generation."""

    def test_compute_dataset_id_deterministic(self):
        """Test deterministic dataset ID."""
        id1 = compute_dataset_id(
            run_id="run123",
            columns=["a", "b", "c"],
            row_count=100,
        )
        id2 = compute_dataset_id(
            run_id="run123",
            columns=["a", "b", "c"],
            row_count=100,
        )
        
        assert id1 == id2

    def test_compute_dataset_id_has_prefix(self):
        """Test dataset ID has ds_ prefix."""
        ds_id = compute_dataset_id(run_id="test")
        
        assert ds_id.startswith("ds_")

    def test_compute_dataset_id_columns_sorted(self):
        """Test that column order doesn't affect ID."""
        id1 = compute_dataset_id(columns=["a", "b", "c"])
        id2 = compute_dataset_id(columns=["c", "a", "b"])
        
        assert id1 == id2

    def test_compute_dataset_id_different_row_count(self):
        """Test different row counts produce different IDs."""
        id1 = compute_dataset_id(run_id="run1", row_count=100)
        id2 = compute_dataset_id(run_id="run1", row_count=200)
        
        assert id1 != id2


class TestPipelineIdGeneration:
    """Tests for pipeline ID generation."""

    def test_compute_pipeline_id_deterministic(self):
        """Test deterministic pipeline ID."""
        steps = [{"type": "dat:aggregate"}, {"type": "pptx:generate"}]
        
        id1 = compute_pipeline_id("Test Pipeline", steps)
        id2 = compute_pipeline_id("Test Pipeline", steps)
        
        assert id1 == id2

    def test_compute_pipeline_id_has_prefix(self):
        """Test pipeline ID has pipe_ prefix."""
        pipe_id = compute_pipeline_id("Test", [{"type": "test"}])
        
        assert pipe_id.startswith("pipe_")

    def test_compute_pipeline_id_different_names(self):
        """Test different names produce different IDs."""
        steps = [{"type": "test"}]
        
        id1 = compute_pipeline_id("Pipeline A", steps)
        id2 = compute_pipeline_id("Pipeline B", steps)
        
        assert id1 != id2

    def test_compute_pipeline_id_different_steps(self):
        """Test different steps produce different IDs."""
        id1 = compute_pipeline_id("Test", [{"type": "a"}])
        id2 = compute_pipeline_id("Test", [{"type": "b"}])
        
        assert id1 != id2
