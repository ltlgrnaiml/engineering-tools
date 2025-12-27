"""Tests for deterministic ID generation contracts.

Per ADR-0004: Deterministic Content-Addressed IDs.
Tests that same inputs always produce same IDs.
"""

import pytest

from shared.contracts.core.id_generator import (
    IDAlgorithm,
    IDConfig,
    IDGenerationRequest,
    IDGenerationResult,
    ParseStageInputs,
    UploadStageInputs,
    compute_content_hash,
    compute_deterministic_id,
    verify_id_determinism,
)


class TestComputeDeterministicId:
    """Tests for compute_deterministic_id function."""

    def test_same_inputs_produce_same_id(self) -> None:
        """Per ADR-0004: Same inputs must always yield same ID."""
        inputs = {"file_hash": "abc123", "profile": "test"}

        id1 = compute_deterministic_id(inputs)
        id2 = compute_deterministic_id(inputs)

        assert id1 == id2
        assert len(id1) == 8  # Default prefix length

    def test_different_inputs_produce_different_ids(self) -> None:
        """Different inputs must produce different IDs."""
        inputs1 = {"file_hash": "abc123"}
        inputs2 = {"file_hash": "def456"}

        id1 = compute_deterministic_id(inputs1)
        id2 = compute_deterministic_id(inputs2)

        assert id1 != id2

    def test_seed_affects_output(self) -> None:
        """Different seeds must produce different IDs."""
        inputs = {"file_hash": "abc123"}

        id1 = compute_deterministic_id(inputs, seed=42)
        id2 = compute_deterministic_id(inputs, seed=99)

        assert id1 != id2

    def test_default_seed_is_42(self) -> None:
        """Per ADR-0004: Default seed is 42."""
        inputs = {"test": "value"}

        id_default = compute_deterministic_id(inputs)
        id_explicit = compute_deterministic_id(inputs, seed=42)

        assert id_default == id_explicit

    def test_prefix_length_customization(self) -> None:
        """Prefix length should be configurable."""
        inputs = {"test": "value"}

        id_8 = compute_deterministic_id(inputs, prefix_length=8)
        id_16 = compute_deterministic_id(inputs, prefix_length=16)

        assert len(id_8) == 8
        assert len(id_16) == 16
        assert id_16.startswith(id_8)  # Longer prefix contains shorter

    def test_namespace_prefix(self) -> None:
        """Namespace should be prepended to ID."""
        inputs = {"test": "value"}

        id_no_ns = compute_deterministic_id(inputs)
        id_with_ns = compute_deterministic_id(inputs, namespace="dat")

        assert id_with_ns == f"dat_{id_no_ns}"

    def test_input_order_independence(self) -> None:
        """Input key order should not affect ID."""
        inputs1 = {"a": "1", "b": "2", "c": "3"}
        inputs2 = {"c": "3", "a": "1", "b": "2"}

        id1 = compute_deterministic_id(inputs1)
        id2 = compute_deterministic_id(inputs2)

        assert id1 == id2


class TestComputeContentHash:
    """Tests for compute_content_hash function."""

    def test_string_hash(self) -> None:
        """String content should produce consistent hash."""
        content = "test content"

        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # Full SHA-256 hex

    def test_bytes_hash(self) -> None:
        """Bytes content should produce consistent hash."""
        content = b"test content"

        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert hash1 == hash2

    def test_string_and_bytes_equivalent(self) -> None:
        """String and equivalent bytes should produce same hash."""
        string_hash = compute_content_hash("test")
        bytes_hash = compute_content_hash(b"test")

        assert string_hash == bytes_hash


class TestVerifyIdDeterminism:
    """Tests for verify_id_determinism function."""

    def test_valid_verification(self) -> None:
        """Valid inputs should verify successfully."""
        inputs = {"file": "test.csv", "hash": "abc123"}
        generated_id = compute_deterministic_id(inputs)

        assert verify_id_determinism(inputs, generated_id) is True

    def test_invalid_verification(self) -> None:
        """Different inputs should fail verification."""
        inputs = {"file": "test.csv"}
        wrong_id = "wrongid1"

        assert verify_id_determinism(inputs, wrong_id) is False


class TestStageIDInputs:
    """Tests for stage-specific ID input models."""

    def test_upload_stage_inputs(self) -> None:
        """UploadStageInputs should validate and serialize correctly."""
        inputs = UploadStageInputs(
            file_hash="abc123def456",
            file_name="data.csv",
            file_size_bytes=1024,
        )

        assert inputs.stage_type == "upload"
        hash_dict = inputs.to_hash_dict()
        assert "file_hash" in hash_dict
        assert hash_dict["stage_type"] == "upload"

    def test_parse_stage_inputs(self) -> None:
        """ParseStageInputs should include required fields."""
        inputs = ParseStageInputs(
            upload_stage_id="upload_1",
            profile_id="default_profile",
            profile_version="1.0.0",
        )

        assert inputs.stage_type == "parse"
        hash_dict = inputs.to_hash_dict()
        assert hash_dict["upload_stage_id"] == "upload_1"
        assert hash_dict["profile_id"] == "default_profile"

    def test_parse_stage_with_optional_context(self) -> None:
        """ParseStageInputs should handle optional context_stage_id."""
        inputs_without = ParseStageInputs(
            upload_stage_id="upload_1",
            profile_id="profile",
            profile_version="1.0",
        )
        inputs_with = ParseStageInputs(
            upload_stage_id="upload_1",
            context_stage_id="context_1",
            profile_id="profile",
            profile_version="1.0",
        )

        # IDs should differ when context is provided
        id_without = compute_deterministic_id(inputs_without.to_hash_dict())
        id_with = compute_deterministic_id(inputs_with.to_hash_dict())

        assert id_without != id_with


class TestIDConfig:
    """Tests for IDConfig model."""

    def test_default_config(self) -> None:
        """Default config should match ADR-0004 requirements."""
        config = IDConfig()

        assert config.algorithm == IDAlgorithm.SHA256_SHORT
        assert config.seed == 42
        assert config.prefix_length == 8

    def test_custom_config(self) -> None:
        """Custom config values should be accepted."""
        config = IDConfig(
            algorithm=IDAlgorithm.SHA256_MEDIUM,
            seed=123,
            prefix_length=16,
            namespace="test",
        )

        assert config.algorithm == IDAlgorithm.SHA256_MEDIUM
        assert config.seed == 123
        assert config.prefix_length == 16
        assert config.namespace == "test"

    def test_prefix_length_validation(self) -> None:
        """Prefix length should be validated."""
        # Valid range: 4-64
        IDConfig(prefix_length=4)
        IDConfig(prefix_length=64)

        with pytest.raises(ValueError):
            IDConfig(prefix_length=3)

        with pytest.raises(ValueError):
            IDConfig(prefix_length=65)


class TestIDGenerationContracts:
    """Tests for ID generation request/result contracts."""

    def test_id_generation_request(self) -> None:
        """IDGenerationRequest should serialize inputs correctly."""
        request = IDGenerationRequest(
            inputs={"test": "value"},
            config=IDConfig(namespace="test"),
        )

        assert request.inputs["test"] == "value"
        assert request.config.namespace == "test"

    def test_id_generation_result(self) -> None:
        """IDGenerationResult should include all required fields."""
        result = IDGenerationResult(
            id="abc12345",
            full_hash="abc12345" * 8,  # 64 chars
            inputs_hash="def67890" * 8,
            algorithm=IDAlgorithm.SHA256_SHORT,
            seed=42,
        )

        assert result.id == "abc12345"
        assert result.namespaced_id == "abc12345"

    def test_id_generation_result_with_namespace(self) -> None:
        """IDGenerationResult.namespaced_id should include namespace."""
        result = IDGenerationResult(
            id="abc12345",
            full_hash="abc12345" * 8,
            inputs_hash="def67890" * 8,
            algorithm=IDAlgorithm.SHA256_SHORT,
            seed=42,
            namespace="dat",
        )

        assert result.namespaced_id == "dat_abc12345"
