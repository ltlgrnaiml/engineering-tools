"""Workflow Manager API contracts.

Per ADR-0043: DevTools Workflow Manager UI Architecture.

This module defines the contracts for the AI Development Workflow artifacts
including Discussions, ADRs, SPECs, Plans, and Contracts with graph visualization.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.1"


# =============================================================================
# Artifact Types & Status
# =============================================================================


class ArtifactType(str, Enum):
    """Types of workflow artifacts."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class ArtifactStatus(str, Enum):
    """Status values for artifacts."""

    DRAFT = "draft"
    ACTIVE = "active"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RelationshipType(str, Enum):
    """Types of relationships between artifacts."""

    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"


# =============================================================================
# Artifact Models
# =============================================================================


class ArtifactSummary(BaseModel):
    """Summary of an artifact for list views."""

    id: str = Field(..., description="Artifact ID (e.g., DISC-001, ADR-0043)")
    type: ArtifactType
    title: str
    status: ArtifactStatus
    file_path: str = Field(..., description="Relative path to artifact file")
    created_date: str | None = Field(None, description="ISO-8601 date string")
    updated_date: str | None = Field(None, description="ISO-8601 date string")
    author: str | None = None
    summary: str | None = Field(None, description="Brief description")


class ArtifactListResponse(BaseModel):
    """Response containing list of artifacts."""

    items: list[ArtifactSummary]
    total: int
    filtered_type: ArtifactType | None = Field(
        None,
        description="Type filter applied",
    )


class ArtifactContent(BaseModel):
    """Full artifact content for reading/editing."""

    id: str
    type: ArtifactType
    title: str
    status: ArtifactStatus
    file_path: str
    content: dict[str, Any] | str = Field(
        ...,
        description="Full artifact content (dict for JSON, str for markdown/code)",
    )
    raw_content: str = Field(
        ...,
        description="Raw file content for editor",
    )


class ArtifactReadResponse(BaseModel):
    """Response when reading a single artifact."""

    artifact: ArtifactContent


# =============================================================================
# Graph Models
# =============================================================================


class GraphNode(BaseModel):
    """Node in the artifact relationship graph."""

    id: str = Field(..., description="Artifact ID")
    type: ArtifactType
    label: str = Field(..., description="Display label (usually title)")
    status: ArtifactStatus
    file_path: str = Field(..., description="Relative path to artifact file")
    tier: int | None = Field(None, description="Workflow tier (0-5 per ADR-0041)")


class GraphEdge(BaseModel):
    """Edge in the artifact relationship graph."""

    source: str = Field(..., description="Source artifact ID")
    target: str = Field(..., description="Target artifact ID")
    relationship: RelationshipType


class ArtifactGraphResponse(BaseModel):
    """Response containing artifact relationship graph."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int


# =============================================================================
# CRUD Operations
# =============================================================================


class ArtifactCreateRequest(BaseModel):
    """Request to create a new artifact."""

    type: ArtifactType
    title: str
    content: dict[str, Any] | str = Field(
        ...,
        description="Initial content (dict for JSON types, str for markdown/code)",
    )
    status: ArtifactStatus = Field(
        ArtifactStatus.DRAFT,
        description="Initial status",
    )


class ArtifactCreateResponse(BaseModel):
    """Response after creating an artifact."""

    success: bool
    artifact: ArtifactSummary
    file_path: str
    message: str


class ArtifactUpdateRequest(BaseModel):
    """Request to update an existing artifact."""

    file_path: str = Field(..., description="Relative path to artifact file")
    content: dict[str, Any] | str
    create_backup: bool = Field(
        True,
        description="Whether to backup existing file before overwriting",
    )


class ArtifactUpdateResponse(BaseModel):
    """Response after updating an artifact."""

    success: bool
    artifact: ArtifactSummary
    backup_path: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    message: str


class ArtifactDeleteRequest(BaseModel):
    """Request to delete an artifact."""

    file_path: str = Field(..., description="Relative path to artifact file")
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


# =============================================================================
# Activity & History
# =============================================================================


class ActivityEvent(BaseModel):
    """Recent activity event for an artifact."""

    artifact_id: str
    artifact_type: ArtifactType
    artifact_title: str
    event_type: str = Field(
        ...,
        description="Event type (created, updated, deleted)",
    )
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    file_path: str


class ActivityFeedResponse(BaseModel):
    """Response containing recent activity feed."""

    events: list[ActivityEvent]
    total: int
    since: str | None = Field(
        None,
        description="ISO-8601 timestamp of oldest event",
    )
