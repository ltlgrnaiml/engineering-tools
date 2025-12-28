"""Template models for PowerPoint template management."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ShapeInfo(BaseModel):
    """
    Information about a shape in a PowerPoint template.

    Attributes:
        shape_id: Unique identifier for the shape within the slide.
        name: Name of the shape as defined in PowerPoint.
        shape_type: Type of shape (e.g., 'text_box', 'picture', 'table', 'chart').
        slide_index: Zero-based index of the slide containing the shape.
        position: Position coordinates (left, top, width, height) in EMUs.
        has_text: Whether the shape contains text.
        has_table: Whether the shape is a table.
        has_chart: Whether the shape is a chart.
    """

    shape_id: int = Field(..., description="Shape ID within the slide")
    name: str = Field(..., description="Shape name")
    shape_type: str = Field(..., description="Type of shape")
    slide_index: int = Field(..., ge=0, description="Slide index (0-based)")
    position: dict[str, int] = Field(
        ...,
        description="Position (left, top, width, height) in EMUs",
    )
    has_text: bool = Field(default=False, description="Contains text")
    has_table: bool = Field(default=False, description="Is a table")
    has_chart: bool = Field(default=False, description="Is a chart")
    parsed_name: object | None = Field(None, description="Parsed shape name (ParsedShapeName)")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "shape_id": 1,
            "name": "Title_Placeholder",
            "shape_type": "text_box",
            "slide_index": 0,
            "position": {"left": 914400, "top": 685800, "width": 7315200, "height": 1143000},
            "has_text": True,
            "has_table": False,
            "has_chart": False,
        }
    })


class ShapeMap(BaseModel):
    """
    Complete mapping of all shapes in a PowerPoint template.

    Attributes:
        id: Unique identifier for the shape map.
        template_id: ID of the associated template.
        shapes: List of all shapes found in the template.
        slide_count: Total number of slides in the template.
        created_at: Timestamp when the shape map was created.
    """

    id: UUID = Field(default_factory=uuid4, description="Shape map ID")
    template_id: UUID = Field(..., description="Associated template ID")
    shapes: list[ShapeInfo] = Field(default_factory=list, description="List of shapes")
    slide_count: int = Field(..., ge=1, description="Number of slides")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "template_id": "123e4567-e89b-12d3-a456-426614174002",
            "slide_count": 5,
            "shapes": [
                {
                    "shape_id": 1,
                    "name": "Title_Placeholder",
                    "shape_type": "text_box",
                    "slide_index": 0,
                    "position": {
                        "left": 914400,
                        "top": 685800,
                        "width": 7315200,
                        "height": 1143000,
                    },
                    "has_text": True,
                    "has_table": False,
                    "has_chart": False,
                }
            ],
            "created_at": "2024-01-15T10:35:00Z",
        }
    })


class Template(BaseModel):
    """
    PowerPoint template file metadata.

    Attributes:
        id: Unique identifier for the template.
        project_id: ID of the associated project.
        filename: Original filename of the uploaded template.
        file_path: Server path to the stored template file.
        file_size: Size of the file in bytes.
        uploaded_at: Timestamp when the template was uploaded.
    """

    id: UUID = Field(default_factory=uuid4, description="Template ID")
    project_id: UUID = Field(..., description="Associated project ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Server file path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Upload timestamp",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174002",
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "sales_template.pptx",
            "file_path": "uploads/123e4567-e89b-12d3-a456-426614174002.pptx",
            "file_size": 1048576,
            "uploaded_at": "2024-01-15T10:32:00Z",
        }
    })
