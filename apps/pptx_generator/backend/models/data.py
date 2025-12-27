"""Data models for data file and mapping management."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DataFile(BaseModel):
    """
    Data file metadata for user-provided data.

    Attributes:
        id: Unique identifier for the data file.
        project_id: ID of the associated project.
        filename: Original filename of the uploaded data file.
        file_path: Server path to the stored data file.
        file_size: Size of the file in bytes.
        file_type: Type of data file (csv, xlsx, xls).
        row_count: Number of data rows in the file.
        column_names: List of column names from the data file.
        uploaded_at: Timestamp when the data file was uploaded.
    """

    id: UUID = Field(default_factory=uuid4, description="Data file ID")
    project_id: UUID = Field(..., description="Associated project ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Server file path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_type: str = Field(..., description="File type (csv, xlsx, xls)")
    row_count: int = Field(..., ge=0, description="Number of data rows")
    column_names: list[str] = Field(default_factory=list, description="Column names")
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Upload timestamp",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "sales_data.xlsx",
                "file_path": "uploads/123e4567-e89b-12d3-a456-426614174003.xlsx",
                "file_size": 524288,
                "file_type": "xlsx",
                "row_count": 150,
                "column_names": ["region", "sales", "growth", "target"],
                "uploaded_at": "2024-01-15T10:40:00Z",
            }
        }


class DataMapping(BaseModel):
    """
    Mapping configuration between data columns and template shapes.

    Attributes:
        shape_name: Name of the shape in the template.
        data_column: Name of the data column to map.
        transformation: Optional transformation to apply (e.g., 'currency', 'percentage').
        default_value: Default value if data is missing.
    """

    shape_name: str = Field(..., description="Template shape name")
    data_column: str = Field(..., description="Data column name")
    transformation: str | None = Field(None, description="Data transformation type")
    default_value: Any | None = Field(None, description="Default value if missing")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "shape_name": "Sales_Value_Text",
                "data_column": "sales",
                "transformation": "currency",
                "default_value": "$0",
            }
        }


class AssetMapping(BaseModel):
    """
    Complete asset mapping configuration for a project.

    Attributes:
        id: Unique identifier for the asset mapping.
        project_id: ID of the associated project.
        mappings: List of individual data-to-shape mappings.
        domain_knowledge: Optional domain-specific transformation rules.
        created_at: Timestamp when the mapping was created.
        updated_at: Timestamp when the mapping was last updated.
    """

    id: UUID = Field(default_factory=uuid4, description="Asset mapping ID")
    project_id: UUID = Field(..., description="Associated project ID")
    mappings: list[DataMapping] = Field(default_factory=list, description="Data mappings")
    domain_knowledge: dict[str, Any] | None = Field(
        None,
        description="Domain-specific rules",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174004",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "mappings": [
                    {
                        "shape_name": "Sales_Value_Text",
                        "data_column": "sales",
                        "transformation": "currency",
                        "default_value": "$0",
                    }
                ],
                "domain_knowledge": {"currency_format": "USD", "decimal_places": 2},
                "created_at": "2024-01-15T10:45:00Z",
                "updated_at": "2024-01-15T10:45:00Z",
            }
        }
