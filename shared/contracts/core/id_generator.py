"""Deterministic ID generation contracts.

Per ADR-0004: Deterministic Content-Addressed IDs.
Per ADR-0004-DAT: DAT Stage ID Configuration.

This module defines contracts for generating deterministic, content-addressed
IDs using SHA-256 hashing of stable JSON serialization of inputs.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


# =============================================================================
# ID Generation Configuration
# =============================================================================


class IDAlgorithm(str, Enum):
    """Supported ID generation algorithms."""

    SHA256 = "sha256"
    SHA256_SHORT = "sha256_short"  # 8-char prefix (default)
    SHA256_MEDIUM = "sha256_medium"  # 16-char prefix
    SHA256_FULL = "sha256_full"  # Full 64-char hash


class IDConfig(BaseModel):
    """Configuration for ID generation.

    Per ADR-0004: SHA-256 hash of inputs with seed=42, 8-char prefix default.
    """

    algorithm: IDAlgorithm = IDAlgorithm.SHA256_SHORT
    seed: int = Field(42, description="Random seed for determinism")
    prefix_length: int = Field(
        8,
        ge=4,
        le=64,
        description="Length of hash prefix to use as ID",
    )
    include_timestamp: bool = Field(
        False,
        description="Whether to include timestamp in hash inputs (breaks idempotency)",
    )
    namespace: str | None = Field(
        None,
        description="Optional namespace prefix (e.g., 'dat', 'sov')",
    )


# =============================================================================
# Stage ID Inputs (Per ADR-0004-DAT)
# =============================================================================


class StageIDInputs(BaseModel):
    """Base class for stage-specific ID inputs.

    Per ADR-0004-DAT: Each stage has specific inputs that determine its ID.
    Same inputs must always yield same ID (idempotent re-computation).
    """

    stage_type: str = Field(..., description="Type of stage (e.g., 'upload', 'parse')")

    def to_hash_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing. Override in subclasses."""
        return self.model_dump(mode="json", exclude_none=True)


class UploadStageInputs(StageIDInputs):
    """Inputs for Upload stage ID computation."""

    stage_type: Literal["upload"] = "upload"
    file_hash: str = Field(..., description="SHA-256 hash of uploaded file content")
    file_name: str
    file_size_bytes: int


class ContextStageInputs(StageIDInputs):
    """Inputs for Context stage ID computation."""

    stage_type: Literal["context"] = "context"
    upload_stage_id: str = Field(..., description="ID of parent Upload stage")
    context_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Context configuration overrides",
    )


class PreviewStageInputs(StageIDInputs):
    """Inputs for Preview stage ID computation."""

    stage_type: Literal["preview"] = "preview"
    upload_stage_id: str
    context_stage_id: str | None = Field(
        None,
        description="Optional - None if Context was skipped",
    )
    preview_config: dict[str, Any] = Field(default_factory=dict)


class ParseStageInputs(StageIDInputs):
    """Inputs for Parse stage ID computation."""

    stage_type: Literal["parse"] = "parse"
    upload_stage_id: str
    context_stage_id: str | None = None
    profile_id: str = Field(..., description="Extraction profile ID")
    profile_version: str = Field(..., description="Profile version")
    parse_config: dict[str, Any] = Field(default_factory=dict)


class AggregateStageInputs(StageIDInputs):
    """Inputs for Aggregate stage ID computation."""

    stage_type: Literal["aggregate"] = "aggregate"
    parse_stage_id: str
    aggregation_config: dict[str, Any] = Field(
        ...,
        description="Aggregation rules and groupings",
    )


class TransformStageInputs(StageIDInputs):
    """Inputs for Transform stage ID computation."""

    stage_type: Literal["transform"] = "transform"
    aggregate_stage_id: str
    transform_plan: list[dict[str, Any]] = Field(
        ...,
        description="Ordered list of transformations",
    )


class ValidateStageInputs(StageIDInputs):
    """Inputs for Validate stage ID computation."""

    stage_type: Literal["validate"] = "validate"
    transform_stage_id: str
    validation_rules: list[dict[str, Any]] = Field(default_factory=list)


class ExportStageInputs(StageIDInputs):
    """Inputs for Export stage ID computation."""

    stage_type: Literal["export"] = "export"
    validate_stage_id: str
    export_format: Literal["parquet", "csv", "json", "tsv"] = "parquet"
    export_config: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# ID Generation Functions (as contracts)
# =============================================================================


class IDGenerationRequest(BaseModel):
    """Request to generate a deterministic ID."""

    inputs: dict[str, Any] = Field(
        ...,
        description="Inputs to hash for ID generation",
    )
    config: IDConfig = Field(default_factory=IDConfig)


class IDGenerationResult(BaseModel):
    """Result of ID generation."""

    id: str = Field(..., description="Generated deterministic ID")
    full_hash: str = Field(..., description="Full SHA-256 hash (64 chars)")
    inputs_hash: str = Field(
        ...,
        description="Hash of the serialized inputs (for verification)",
    )
    algorithm: IDAlgorithm
    seed: int
    namespace: str | None = None

    @property
    def namespaced_id(self) -> str:
        """Return ID with namespace prefix if configured."""
        if self.namespace:
            return f"{self.namespace}_{self.id}"
        return self.id


# =============================================================================
# Artifact ID Contracts
# =============================================================================


class ArtifactIDRequest(BaseModel):
    """Request to generate an artifact ID.

    Per ADR-0004: Artifact IDs are content-addressed.
    """

    artifact_type: str = Field(
        ...,
        description="Type of artifact (e.g., 'dataset', 'chart', 'report')",
    )
    content_hash: str = Field(
        ...,
        description="Hash of artifact content",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata to include in ID computation",
    )
    config: IDConfig = Field(default_factory=IDConfig)


class ArtifactIDResult(BaseModel):
    """Result of artifact ID generation."""

    artifact_id: str
    artifact_type: str
    content_hash: str
    full_hash: str
    created_at: datetime


# =============================================================================
# ID Validation
# =============================================================================


class IDValidationRequest(BaseModel):
    """Request to validate an ID against expected inputs."""

    id: str = Field(..., description="ID to validate")
    expected_inputs: dict[str, Any] = Field(
        ...,
        description="Expected inputs that should produce this ID",
    )
    config: IDConfig = Field(default_factory=IDConfig)


class IDValidationResult(BaseModel):
    """Result of ID validation."""

    valid: bool = Field(
        ...,
        description="Whether ID matches expected inputs",
    )
    expected_id: str = Field(
        ...,
        description="ID that would be generated from expected_inputs",
    )
    actual_id: str
    match: bool = Field(..., description="Whether expected_id == actual_id")
    message: str


# =============================================================================
# Utility Functions (Pure functions for ID generation)
# =============================================================================


def compute_deterministic_id(
    inputs: dict[str, Any],
    seed: int = 42,
    prefix_length: int = 8,
    namespace: str | None = None,
) -> str:
    """Compute a deterministic ID from inputs.

    Per ADR-0004:
    - SHA-256 hash of stable JSON serialization
    - Fixed seed for determinism
    - 8-char prefix by default

    Args:
        inputs: Dictionary of inputs to hash
        seed: Random seed (included in hash for extra determinism)
        prefix_length: Length of hash prefix to return
        namespace: Optional namespace prefix

    Returns:
        Deterministic ID string
    """
    # Create stable JSON representation
    # Sort keys and use separators without spaces for consistency
    hash_input = {
        "_seed": seed,
        **inputs,
    }
    json_str = json.dumps(hash_input, sort_keys=True, separators=(",", ":"), default=str)

    # Compute SHA-256 hash
    hash_bytes = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    # Extract prefix
    id_str = hash_bytes[:prefix_length]

    # Add namespace if provided
    if namespace:
        return f"{namespace}_{id_str}"

    return id_str


def compute_content_hash(content: bytes | str) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: Content to hash (bytes or string)

    Returns:
        Full 64-character hex hash
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def verify_id_determinism(
    inputs: dict[str, Any],
    expected_id: str,
    seed: int = 42,
    prefix_length: int = 8,
) -> bool:
    """Verify that inputs produce the expected ID.

    Per ADR-0004: Same inputs must always yield same ID.

    Args:
        inputs: Inputs to hash
        expected_id: Expected ID value
        seed: Random seed
        prefix_length: Length of ID

    Returns:
        True if inputs produce expected_id
    """
    computed_id = compute_deterministic_id(
        inputs=inputs,
        seed=seed,
        prefix_length=prefix_length,
    )
    return computed_id == expected_id
