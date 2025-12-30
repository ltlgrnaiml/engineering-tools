"""DevTools Workflow Manager contracts.

Per ADR-0043: DevTools Workflow Manager UI Architecture.

This module defines contracts for the AI Development Workflow artifact
management, including artifact discovery, graph visualization, and CRUD.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


# =============================================================================
# Artifact Type Enums
# =============================================================================


class ArtifactType(str, Enum):
    """Types of artifacts in the AI Development Workflow."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class ArtifactStatus(str, Enum):
    """Status values for workflow artifacts."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    COMPLETED = "completed"


class RelationshipType(str, Enum):
    """Types of relationships between artifacts."""

    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"


# =============================================================================
# Artifact Summary Models
# =============================================================================


class ArtifactSummary(BaseModel):
    """Summary of an artifact for list views."""

    id: str = Field(..., description="Artifact ID (e.g., ADR-0001, DISC-001)")
    type: ArtifactType
    title: str
    status: ArtifactStatus
    file_path: str = Field(..., description="Relative path to artifact file")
    created_date: str | None = Field(None, description="ISO-8601 date string")
    updated_date: str | None = Field(None, description="ISO-8601 date string")


class ArtifactListResponse(BaseModel):
    """Response containing list of artifacts."""

    items: list[ArtifactSummary]
    total: int
    types: list[ArtifactType] = Field(
        default_factory=list,
        description="Unique types in the result set",
    )


# =============================================================================
# Graph Visualization Models
# =============================================================================


class GraphNode(BaseModel):
    """Node in the artifact relationship graph."""

    id: str = Field(..., description="Unique node ID (same as artifact ID)")
    type: ArtifactType
    label: str = Field(..., description="Display label for the node")
    status: ArtifactStatus
    file_path: str = Field(..., description="Relative path to artifact file")


class GraphEdge(BaseModel):
    """Edge connecting two nodes in the artifact graph."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: RelationshipType


class ArtifactGraphResponse(BaseModel):
    """Response containing the artifact relationship graph."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_count: int
    edge_count: int


# =============================================================================
# CRUD Operations
# =============================================================================


class ArtifactCreateRequest(BaseModel):
    """Request to create a new artifact."""

    type: ArtifactType
    title: str
    content: dict | str = Field(
        ...,
        description="Artifact content (dict for JSON, str for markdown)",
    )
    file_path: str | None = Field(
        None,
        description="Optional custom file path, auto-generated if not provided",
    )


class ArtifactCreateResponse(BaseModel):
    """Response after creating an artifact."""

    success: bool
    artifact: ArtifactSummary | None = None
    file_path: str | None = None
    message: str


class ArtifactUpdateRequest(BaseModel):
    """Request to update an existing artifact."""

    file_path: str = Field(..., description="Path to the artifact file")
    content: dict | str = Field(..., description="Updated artifact content")
    create_backup: bool = Field(
        True,
        description="Whether to backup existing file before overwriting",
    )


class ArtifactUpdateResponse(BaseModel):
    """Response after updating an artifact."""

    success: bool
    artifact: ArtifactSummary | None = None
    backup_path: str | None = None
    message: str


class ArtifactDeleteRequest(BaseModel):
    """Request to delete an artifact."""

    file_path: str
    permanent: bool = Field(
        False,
        description="If True, permanently delete (not recommended)",
    )


class ArtifactDeleteResponse(BaseModel):
    """Response after deleting an artifact."""

    success: bool
    backup_path: str | None = Field(
        None,
        description="Path where deleted artifact was backed up",
    )
    message: str


class ArtifactReadResponse(BaseModel):
    """Response when reading a single artifact."""

    artifact: ArtifactSummary
    content: dict | str = Field(
        ...,
        description="Full artifact content",
    )
    raw: str = Field(
        ...,
        description="Raw file content for editor",
    )
