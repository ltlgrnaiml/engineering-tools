"""Artifact Registry contracts - tracking all artifacts across tools.

The registry is a SQLite database (workspace/.registry.db) that tracks:
- All DataSets created by any tool
- All Pipelines (definitions and execution state)
- All Reports and other output artifacts
- Lineage relationships between artifacts

Per ADR-0002: Artifacts are preserved on unlock (never deleted).
Per ADR-0009: All timestamps are ISO-8601 UTC.
Per ADR-0018#path-safety: All paths are relative.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class ArtifactType(str, Enum):
    """Types of artifacts tracked in the registry."""

    DATASET = "dataset"
    PIPELINE = "pipeline"
    REPORT = "report"
    CONFIG = "config"
    TEMPLATE = "template"


class ArtifactState(str, Enum):
    """State of an artifact in the registry."""

    ACTIVE = "active"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    ARCHIVED = "archived"


class ArtifactRecord(BaseModel):
    """Registry entry for any artifact.

    This is stored in the SQLite registry and enables:
    - Cross-tool artifact discovery
    - Lineage tracking
    - Garbage collection of orphaned artifacts
    """

    # Identity
    artifact_id: str = Field(..., description="Unique artifact identifier")
    artifact_type: ArtifactType
    name: str = Field(..., description="Human-readable name")

    # Location (per ADR-0018#path-safety: always relative)
    relative_path: str = Field(
        ...,
        description="Path relative to workspace/ root",
    )

    # Timestamps (per ADR-0009)
    created_at: datetime
    updated_at: datetime
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None

    # State
    state: ArtifactState = ArtifactState.ACTIVE

    # Tool association
    created_by_tool: Literal["dat", "sov", "pptx", "gateway", "manual"]

    # Lineage
    parent_ids: list[str] = Field(
        default_factory=list,
        description="IDs of parent artifacts this was derived from",
    )

    # Size/Stats
    size_bytes: int = 0
    row_count: int | None = Field(None, description="For datasets only")
    column_count: int | None = Field(None, description="For datasets only")

    # Metadata
    tags: list[str] = Field(default_factory=list)
    description: str | None = None


class ArtifactQuery(BaseModel):
    """Query parameters for searching artifacts."""

    artifact_type: ArtifactType | None = None
    created_by_tool: str | None = None
    state: ArtifactState | None = None
    tags: list[str] | None = None
    parent_id: str | None = Field(
        None,
        description="Find artifacts derived from this parent",
    )
    created_after: datetime | None = None
    created_before: datetime | None = None
    name_contains: str | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class ArtifactStats(BaseModel):
    """Summary statistics for the artifact registry."""

    total_artifacts: int
    total_size_bytes: int
    by_type: dict[str, int]
    by_tool: dict[str, int]
    by_state: dict[str, int]
