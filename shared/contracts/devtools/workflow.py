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


class FileFormat(str, Enum):
    """File format of an artifact."""

    JSON = "json"
    MARKDOWN = "markdown"
    PYTHON = "python"
    UNKNOWN = "unknown"


class WorkflowMode(str, Enum):
    """Workflow automation mode."""

    MANUAL = "manual"
    AI_LITE = "ai_lite"
    AI_FULL = "ai_full"


class WorkflowScenario(str, Enum):
    """Workflow entry point scenarios."""

    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    ARCHITECTURE_CHANGE = "architecture_change"
    ENHANCEMENT = "enhancement"
    DATA_STRUCTURE = "data_structure"


class WorkflowStage(str, Enum):
    """Current stage in the workflow progression."""

    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    CONTRACT = "contract"
    PLAN = "plan"


# =============================================================================
# Workflow State Model
# =============================================================================


class WorkflowState(BaseModel):
    """State of an active workflow session."""

    id: str = Field(..., description="Unique workflow ID (e.g., WF-001)")
    mode: WorkflowMode = Field(..., description="Automation mode")
    scenario: WorkflowScenario = Field(..., description="Entry point scenario")
    title: str = Field(..., description="Workflow title")
    current_stage: WorkflowStage = Field(..., description="Current workflow stage")
    artifacts_created: list[str] = Field(default_factory=list, description="IDs of created artifacts")
    created_at: str = Field(..., description="Creation timestamp ISO format")


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
    file_format: FileFormat = Field(default=FileFormat.UNKNOWN, description="File format")
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


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    mode: WorkflowMode = Field(..., description="Automation mode")
    scenario: WorkflowScenario = Field(..., description="Entry point scenario")
    title: str = Field(..., description="Workflow title")


class WorkflowResponse(BaseModel):
    """Response containing workflow state."""

    workflow: WorkflowState = Field(..., description="The workflow state")
    initial_artifact: ArtifactSummary | None = Field(None, description="Initial artifact if created")
    message: str = Field(default="Success", description="Operation message")


class PromptResponse(BaseModel):
    """Response containing AI-Lite prompt."""

    prompt: str = Field(..., description="Generated prompt text")
    target_type: ArtifactType = Field(..., description="Target artifact type")
    context: dict = Field(default_factory=dict, description="Prompt context metadata")


class GenerationStatus(str, Enum):
    """Status of artifact generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationRequest(BaseModel):
    """Request to generate artifact content."""

    workflow_id: str = Field(..., description="Workflow ID")
    target_types: list[ArtifactType] = Field(..., description="Artifact types to generate")
    context: dict = Field(default_factory=dict, description="Generation context")


class GenerationResponse(BaseModel):
    """Response from artifact generation."""

    artifacts: list[ArtifactSummary] = Field(default_factory=list, description="Generated artifacts")
    status: GenerationStatus = Field(default=GenerationStatus.COMPLETED, description="Generation status")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")
