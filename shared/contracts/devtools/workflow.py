"""DevTools Workflow Manager API contracts.

Defines Pydantic models for artifact discovery, graph visualization,
and CRUD operations.
"""
from enum import Enum
from pydantic import BaseModel, Field

class ArtifactType(str, Enum):
    """Types of workflow artifacts."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"
class ArtifactStatus(str, Enum):
    """Status of workflow artifacts."""

    DRAFT = "draft"
    ACTIVE = "active"
    ACCEPTED = "accepted"
    RESOLVED = "resolved"
    DEPRECATED = "deprecated"
class RelationshipType(str, Enum):
    """Types of relationships between artifacts."""

    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"
class ArtifactSummary(BaseModel):
    """Summary of a workflow artifact for list views."""

    id: str = Field(..., description="Unique artifact identifier")
    type: ArtifactType = Field(..., description="Artifact type")
    title: str = Field(..., description="Human-readable title")
    status: ArtifactStatus = Field(..., description="Current status")
    path: str = Field(..., description="Relative file path")
    created_date: str = Field(..., description="Creation date (YYYY-MM-DD)")
class GraphNode(BaseModel):
    """Node in the artifact relationship graph."""

    id: str = Field(..., description="Unique node identifier")
    type: ArtifactType = Field(..., description="Artifact type")
    label: str = Field(..., description="Display label")
    status: ArtifactStatus = Field(..., description="Current status")
    file_path: str = Field(..., description="Relative file path")
class GraphEdge(BaseModel):
    """Edge in the artifact relationship graph."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
class ArtifactListResponse(BaseModel):
    """Response for artifact list endpoint."""

    items: list[ArtifactSummary] = Field(default_factory=list)
    total: int = Field(..., description="Total count of artifacts")


class ArtifactGraphResponse(BaseModel):
    """Response for artifact graph endpoint."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class ArtifactCreateRequest(BaseModel):
    """Request to create a new artifact."""

    type: ArtifactType = Field(..., description="Artifact type to create")
    title: str = Field(..., min_length=5, description="Artifact title")
    content: dict | None = Field(None, description="Initial content (optional)")


class ArtifactCreateResponse(BaseModel):
    """Response after creating artifact."""

    artifact: ArtifactSummary = Field(..., description="Created artifact")
    path: str = Field(..., description="File path created")


class ArtifactDeleteResponse(BaseModel):
    """Response after deleting artifact."""

    success: bool = Field(..., description="Whether deletion succeeded")
    backup_path: str = Field(..., description="Path to backup file")