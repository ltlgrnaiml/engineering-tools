"""DevTools Workflow Manager contracts.

Defines cross-artifact discovery and workflow graph structures for the DevTools
Workflow Manager UI.

Artifact types covered:
- Discussions (.discussions/*.md)
- ADRs (.adrs/**/*.json)
- SPECs (docs/specs/*.json)
- Plans (.plans/*.json)
- Contracts (shared/contracts/**/*.py)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class ArtifactType(str, Enum):
    """Supported workflow artifact types."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"


class ArtifactStatus(str, Enum):
    """Lifecycle status for workflow artifacts."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class ArtifactSummary(BaseModel):
    """Summary metadata for a workflow artifact."""

    id: str = Field(..., description="Artifact ID (e.g., ADR-0001, SPEC-0046)")
    type: ArtifactType
    title: str = Field(..., description="Human-readable title")
    status: ArtifactStatus = ArtifactStatus.UNKNOWN
    file_path: str = Field(..., description="Relative path to artifact file")

    updated_at: datetime | None = Field(
        None,
        description="Last modified time (if available)",
    )
    size_bytes: int | None = Field(
        None,
        ge=0,
        description="File size in bytes (if available)",
    )


class ArtifactListResponse(BaseModel):
    """Response containing a list of workflow artifacts."""

    items: list[ArtifactSummary]
    total: int = Field(..., ge=0)


class ArtifactContentFormat(str, Enum):
    """On-disk format of an artifact file."""

    JSON = "json"
    MARKDOWN = "markdown"
    PYTHON = "python"
    TEXT = "text"


class ArtifactReadResponse(BaseModel):
    """Response when reading an artifact."""

    artifact: ArtifactSummary
    content: str = Field(..., description="Raw artifact file content")
    format: ArtifactContentFormat


class ArtifactWriteRequest(BaseModel):
    """Request to create or update an artifact file."""

    type: ArtifactType
    file_path: str = Field(..., description="Relative path to write")
    content: str = Field(..., description="Raw content to write")
    format: ArtifactContentFormat

    create_backup: bool = Field(
        True,
        description="Whether to create a backup before overwriting",
    )


class ArtifactWriteResponse(BaseModel):
    """Response after creating or updating an artifact."""

    success: bool
    artifact: ArtifactSummary | None = None
    file_path: str
    backup_path: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    message: str


class ArtifactDeleteRequest(BaseModel):
    """Request to delete an artifact (moves to backup by default)."""

    file_path: str = Field(..., description="Relative path to delete")
    permanent: bool = Field(
        False,
        description="If True, permanently delete (not recommended)",
    )


class ArtifactDeleteResponse(BaseModel):
    """Response after deleting an artifact."""

    success: bool
    file_path: str
    backup_path: str | None = None
    message: str


class GraphRelationship(str, Enum):
    """Relationship type between artifacts."""

    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"


class GraphNode(BaseModel):
    """Graph node representing an artifact."""

    id: str
    type: ArtifactType
    label: str
    status: ArtifactStatus = ArtifactStatus.UNKNOWN
    file_path: str


class GraphEdge(BaseModel):
    """Graph edge representing a relationship between two artifacts."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: GraphRelationship


class ArtifactGraphResponse(BaseModel):
    """Response containing graph nodes and edges."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ArtifactScanRequest(BaseModel):
    """Request to scan artifacts.

    Used primarily for debugging. In most cases, scanning is invoked by
    GET endpoints without a request body.
    """

    types: list[ArtifactType] | None = None
    search: str | None = None


class ArtifactGraphRequest(BaseModel):
    """Request to build the artifact relationship graph."""

    types: list[ArtifactType] | None = None
    relationships: list[GraphRelationship] | None = None
    include_orphans: bool = True


class ArtifactScanDiagnostics(BaseModel):
    """Optional diagnostics metadata from a scan."""

    scanned_paths: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ArtifactScanResponse(BaseModel):
    """Extended scan response including optional diagnostics."""

    response: ArtifactListResponse
    diagnostics: ArtifactScanDiagnostics | None = None


class ArtifactKindConfig(BaseModel):
    """Descriptor for how a given artifact type is stored and parsed."""

    type: ArtifactType
    file_glob: str
    format: ArtifactContentFormat
    root_dir: str = Field(..., description="Relative root directory")


class WorkflowManagerInfo(BaseModel):
    """High-level info contract for Workflow Manager support."""

    version: str = __version__
    supported_types: list[ArtifactType] = Field(default_factory=list)
    supported_relationships: list[GraphRelationship] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class WorkflowManagerErrorResponse(BaseModel):
    """Error response for workflow manager APIs."""

    error: str
    details: dict[str, Any] | None = None
    code: Literal[
        "invalid_request",
        "not_found",
        "path_unsafe",
        "io_error",
        "parse_error",
        "validation_error",
        "internal_error",
    ] = "internal_error"


__all__ = [
    "ArtifactType",
    "ArtifactStatus",
    "ArtifactSummary",
    "ArtifactListResponse",
    "ArtifactContentFormat",
    "ArtifactReadResponse",
    "ArtifactWriteRequest",
    "ArtifactWriteResponse",
    "ArtifactDeleteRequest",
    "ArtifactDeleteResponse",
    "GraphRelationship",
    "GraphNode",
    "GraphEdge",
    "ArtifactGraphResponse",
    "ArtifactScanRequest",
    "ArtifactScanDiagnostics",
    "ArtifactScanResponse",
    "ArtifactGraphRequest",
    "ArtifactKindConfig",
    "WorkflowManagerInfo",
    "WorkflowManagerErrorResponse",
]
