"""Workflow Manager API contracts.

Per ADR-0045: DevTools Workflow Manager UI Architecture.
Defines Pydantic models for artifact discovery and graph visualization.
"""

from enum import Enum

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


# =============================================================================
# Enums (EXACTLY 5 values each for consistency)
# =============================================================================


class ArtifactType(str, Enum):
    """Types of workflow artifacts."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class ArtifactStatus(str, Enum):
    """Status of a workflow artifact."""

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
# Graph Models
# =============================================================================


class GraphNode(BaseModel):
    """A node in the artifact relationship graph."""

    id: str = Field(..., description="Unique artifact ID (e.g., ADR-0001)")
    type: ArtifactType = Field(..., description="Artifact type")
    label: str = Field(..., description="Display label (title)")
    status: ArtifactStatus = Field(..., description="Current status")
    file_path: str = Field(..., description="Relative path to artifact file")


class GraphEdge(BaseModel):
    """An edge (relationship) between two artifacts."""

    source: str = Field(..., description="Source artifact ID")
    target: str = Field(..., description="Target artifact ID")
    relationship: RelationshipType = Field(..., description="Type of relationship")


class GraphResponse(BaseModel):
    """Response containing the artifact relationship graph."""

    nodes: list[GraphNode] = Field(default_factory=list, description="Graph nodes")
    edges: list[GraphEdge] = Field(default_factory=list, description="Graph edges")


# =============================================================================
# Artifact Summary Models
# =============================================================================


class ArtifactSummary(BaseModel):
    """Summary of a workflow artifact for list views."""

    id: str = Field(..., description="Unique artifact ID")
    type: ArtifactType = Field(..., description="Artifact type")
    title: str = Field(..., description="Artifact title")
    status: ArtifactStatus = Field(..., description="Current status")
    file_path: str = Field(..., description="Relative path to artifact file")
    updated_date: str | None = Field(None, description="Last update date (YYYY-MM-DD)")


class ArtifactListResponse(BaseModel):
    """Response containing a list of artifacts."""

    items: list[ArtifactSummary] = Field(default_factory=list, description="Artifacts")
    total: int = Field(..., description="Total count")


class ArtifactResponse(BaseModel):
    """Response for single artifact operations."""

    artifact: ArtifactSummary = Field(..., description="The artifact")
    message: str = Field(default="Success", description="Operation message")


# =============================================================================
# Request Models
# =============================================================================


class CreateArtifactRequest(BaseModel):
    """Request to create a new artifact."""

    type: ArtifactType = Field(..., description="Artifact type to create")
    title: str = Field(..., description="Artifact title")
    content: dict | None = Field(None, description="Initial content (optional)")


class UpdateArtifactRequest(BaseModel):
    """Request to update an existing artifact."""

    title: str | None = Field(None, description="New title (optional)")
    status: ArtifactStatus | None = Field(None, description="New status (optional)")
    content: dict | None = Field(None, description="Updated content (optional)")
