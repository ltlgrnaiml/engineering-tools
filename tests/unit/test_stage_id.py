"""Unit tests for deterministic stage ID generation."""
import pytest

from shared.utils.stage_id import (
    compute_stage_id,
    compute_dataset_id,
    compute_pipeline_id,
    DEFAULT_SEED,
)


class TestComputeStageId:
    """Tests for compute_stage_id function."""

    def test_deterministic_same_inputs(self):
        """Same inputs always produce same ID."""
        inputs = {"files": ["a.csv", "b.csv"], "level": "wafer"}
        
        id1 = compute_stage_id(inputs)
        id2 = compute_stage_id(inputs)
        
        assert id1 == id2

    def test_different_inputs_different_ids(self):
        """Different inputs produce different IDs."""
        inputs1 = {"files": ["a.csv"]}
        inputs2 = {"files": ["b.csv"]}
        
        id1 = compute_stage_id(inputs1)
        id2 = compute_stage_id(inputs2)
        
        assert id1 != id2

    def test_prefix_applied(self):
        """Prefix is prepended to ID."""
        inputs = {"test": "data"}
        
        id_with_prefix = compute_stage_id(inputs, prefix="ds_")
        
        assert id_with_prefix.startswith("ds_")

    def test_id_length(self):
        """ID is 16 hex characters (plus prefix)."""
        inputs = {"test": "data"}
        
        id_no_prefix = compute_stage_id(inputs)
        id_with_prefix = compute_stage_id(inputs, prefix="ds_")
        
        assert len(id_no_prefix) == 16
        assert len(id_with_prefix) == 16 + 3  # 3 for "ds_"

    def test_seed_affects_output(self):
        """Different seeds produce different IDs."""
        inputs = {"test": "data"}
        
        id1 = compute_stage_id(inputs, seed=42)
        id2 = compute_stage_id(inputs, seed=43)
        
        assert id1 != id2

    def test_order_independent(self):
        """Dict key order doesn't affect ID (sorted keys)."""
        inputs1 = {"a": 1, "b": 2}
        inputs2 = {"b": 2, "a": 1}
        
        id1 = compute_stage_id(inputs1)
        id2 = compute_stage_id(inputs2)
        
        assert id1 == id2


class TestComputeDatasetId:
    """Tests for compute_dataset_id function."""

    def test_dataset_id_prefix(self):
        """Dataset IDs have ds_ prefix."""
        dataset_id = compute_dataset_id(run_id="run123")
        
        assert dataset_id.startswith("ds_")

    def test_dataset_id_with_columns(self):
        """Columns are included in hash computation."""
        id1 = compute_dataset_id(columns=["a", "b"])
        id2 = compute_dataset_id(columns=["a", "c"])
        
        assert id1 != id2

    def test_columns_sorted(self):
        """Column order doesn't affect ID (sorted)."""
        id1 = compute_dataset_id(columns=["b", "a"])
        id2 = compute_dataset_id(columns=["a", "b"])
        
        assert id1 == id2

    def test_none_values_excluded(self):
        """None values are not included in hash."""
        id1 = compute_dataset_id(run_id="run123")
        id2 = compute_dataset_id(run_id="run123", columns=None)
        
        assert id1 == id2


class TestComputePipelineId:
    """Tests for compute_pipeline_id function."""

    def test_pipeline_id_prefix(self):
        """Pipeline IDs have pipe_ prefix."""
        pipeline_id = compute_pipeline_id(
            name="Test Pipeline",
            steps=[{"type": "dat"}],
        )
        
        assert pipeline_id.startswith("pipe_")

    def test_different_steps_different_ids(self):
        """Different steps produce different IDs."""
        id1 = compute_pipeline_id("Pipeline", [{"type": "dat"}])
        id2 = compute_pipeline_id("Pipeline", [{"type": "sov"}])
        
        assert id1 != id2

    def test_different_names_different_ids(self):
        """Different names produce different IDs."""
        steps = [{"type": "dat"}]
        id1 = compute_pipeline_id("Pipeline A", steps)
        id2 = compute_pipeline_id("Pipeline B", steps)
        
        assert id1 != id2
