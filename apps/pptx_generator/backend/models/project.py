"""Project models for managing PowerPoint generation projects."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    """
    Project status enumeration.

    Represents the current state of a PowerPoint generation project.
    """

    CREATED = "created"
    TEMPLATE_UPLOADED = "template_uploaded"
    TEMPLATE_PARSED = "template_parsed"
    DATA_UPLOADED = "data_uploaded"
    MAPPING_CONFIGURED = "mapping_configured"
    READY_TO_GENERATE = "ready_to_generate"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

    # TOM v2 statuses
    DRM_EXTRACTED = "drm_extracted"
    ENVIRONMENT_CONFIGURED = "environment_configured"
    MAPPINGS_CONFIGURED = "mappings_configured"
    PLAN_FROZEN = "plan_frozen"


class ProjectCreate(BaseModel):
    """
    Request model for creating a new project.

    Attributes:
        name: Human-readable name for the project.
        description: Optional project description.
    """

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, max_length=1000, description="Project description")


class Project(BaseModel):
    """
    Project model representing a PowerPoint generation project.

    Attributes:
        id: Unique project identifier.
        name: Human-readable name for the project.
        description: Optional project description.
        status: Current project status.
        template_id: ID of the uploaded template file.
        data_file_id: ID of the uploaded data file.
        domain_knowledge_id: ID of the domain knowledge file.
        shape_map_id: ID of the generated shape map.
        asset_mapping_id: ID of the configured asset mapping.
        created_at: Timestamp when project was created.
        updated_at: Timestamp when project was last updated.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique project identifier")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    status: ProjectStatus = Field(
        default=ProjectStatus.CREATED,
        description="Current project status",
    )
    template_id: UUID | None = Field(None, description="Template file ID")
    data_file_id: UUID | None = Field(None, description="Data file ID")
    domain_knowledge_id: UUID | None = Field(None, description="Domain knowledge file ID")
    shape_map_id: UUID | None = Field(None, description="Shape map ID")
    asset_mapping_id: UUID | None = Field(None, description="Asset mapping ID")
    drm_id: UUID | None = Field(None, description="DRM ID")
    environment_profile_id: UUID | None = Field(None, description="Environment profile ID")
    context_mapping_id: UUID | None = Field(None, description="Context mapping ID")
    metrics_mapping_id: UUID | None = Field(None, description="Metrics mapping ID")
    plan_artifacts_id: UUID | None = Field(None, description="Plan artifacts ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Q4 Sales Report",
            "description": "Quarterly sales presentation for executive team",
            "status": "created",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
        }
    })
