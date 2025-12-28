"""Generation models for PowerPoint generation requests and responses."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    """
    Generation status enumeration.

    Represents the current state of a PowerPoint generation task.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationRequest(BaseModel):
    """
    Request model for generating a PowerPoint presentation.

    Attributes:
        project_id: ID of the project to generate presentation for.
        output_filename: Optional custom filename for the generated presentation.
    """

    project_id: UUID = Field(..., description="Project ID")
    output_filename: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Custom output filename",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "output_filename": "Q4_Sales_Report_2024.pptx",
            }
        }


class GenerationResponse(BaseModel):
    """
    Response model for PowerPoint generation.

    Attributes:
        id: Unique identifier for the generation task.
        project_id: ID of the associated project.
        status: Current generation status.
        output_file_path: Path to the generated presentation file.
        output_filename: Name of the generated presentation file.
        error_message: Error message if generation failed.
        started_at: Timestamp when generation started.
        completed_at: Timestamp when generation completed.
    """

    id: UUID = Field(default_factory=uuid4, description="Generation task ID")
    project_id: UUID = Field(..., description="Associated project ID")
    status: GenerationStatus = Field(
        default=GenerationStatus.PENDING,
        description="Generation status",
    )
    output_file_path: str | None = Field(None, description="Output file path")
    output_filename: str | None = Field(None, description="Output filename")
    error_message: str | None = Field(None, description="Error message if failed")
    # Per ADR-0025: Lineage tracking
    source_dataset_id: str | None = Field(
        None,
        description="Source DataSet ID for lineage tracking (per ADR-0025)",
    )
    template_id: str | None = Field(
        None,
        description="Template ID used for generation",
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Start timestamp",
    )
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "output_file_path": "generated/123e4567-e89b-12d3-a456-426614174005.pptx",
                "output_filename": "Q4_Sales_Report_2024.pptx",
                "error_message": None,
                "started_at": "2024-01-15T10:50:00Z",
                "completed_at": "2024-01-15T10:51:30Z",
            }
        }
