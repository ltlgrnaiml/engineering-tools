"""DevTools Workflow API contracts.

Per ADR-0043: DevTools Workflow Manager UI Architecture.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class ArtifactType(str, Enum):
    """Types of workflow artifacts."""
    
    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class ArtifactStatus(str, Enum):
    """Common statuses for artifacts."""
    
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class ArtifactSummary(BaseModel):
    """Summary of an artifact for list views."""
    
    id: str
    type: ArtifactType
    title: str
    status: ArtifactStatus | str  # Allow string fallback for unknown statuses
    file_path: str
    created_at: str | None = None
    updated_at: str | None = None


class ArtifactListResponse(BaseModel):
    """Response containing list of artifacts."""
    
    artifacts: list[ArtifactSummary]
    total: int


class GraphNodeType(str, Enum):
    """Node types for the graph."""
    
    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class GraphEdgeType(str, Enum):
    """Edge types for the graph."""
    
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"
    SUPERSEDES = "supersedes"
    DEPRECATES = "deprecates"


class GraphNode(BaseModel):
    """Node in the artifact graph."""
    
    id: str
    type: GraphNodeType
    label: str
    status: str
    file_path: str
    tier: int  # T0=Discussion, T1=ADR, T2=SPEC, T3=Contract, T4=Plan


class GraphEdge(BaseModel):
    """Edge in the artifact graph."""
    
    source: str
    target: str
    type: GraphEdgeType


class GraphResponse(BaseModel):
    """Response containing graph data."""
    
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ArtifactContent(BaseModel):
    """Full content of an artifact."""
    
    id: str
    type: ArtifactType
    title: str
    status: str
    content: str | dict[str, Any]  # Markdown string or JSON dict
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactCreateRequest(BaseModel):
    """Request to create a new artifact."""
    
    type: ArtifactType
    title: str
    template: str | None = None  # Optional template name


class ArtifactCreateResponse(BaseModel):
    """Response after creating an artifact."""
    
    success: bool
    artifact: ArtifactSummary | None = None
    message: str


class ArtifactUpdateRequest(BaseModel):
    """Request to update an artifact."""
    
    content: str | dict[str, Any]
    message: str | None = None  # Commit/Change message


class ArtifactUpdateResponse(BaseModel):
    """Response after updating an artifact."""
    
    success: bool
    artifact: ArtifactSummary | None = None
    message: str
