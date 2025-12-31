"""API request/response schemas for DAT."""
from datetime import datetime

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    """Request to create a new DAT run."""
    name: str | None = None
    profile_id: str | None = None


class CreateRunResponse(BaseModel):
    """Response for created run."""
    run_id: str
    name: str
    created_at: datetime
    profile_id: str | None = None


class StageStatusResponse(BaseModel):
    """Response for stage status."""
    stage: str
    state: str
    stage_id: str | None = None
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None
    completed: bool = False
    error: str | None = None


class RunResponse(BaseModel):
    """Response for run details."""
    run_id: str
    name: str
    created_at: datetime
    profile_id: str | None = None
    current_stage: str = "selection"
    stages: dict[str, StageStatusResponse] = Field(default_factory=dict)


class ScanRequest(BaseModel):
    """Request to scan a folder for files."""
    folder_path: str
    recursive: bool = True


class SelectionRequest(BaseModel):
    """Request to lock selection stage."""
    source_paths: list[str] | None = None
    selected_files: list[str]
    recursive: bool = True


class ContextOptionsRequest(BaseModel):
    """User-controlled context application options.
    
    Per DESIGN §9: These options map to UI checkboxes that allow
    users to control which context columns are added to output tables.
    """
    include_run_context: bool = Field(
        default=True,
        description="Add run-level context columns (LotID, WaferID, etc.)"
    )
    include_image_context: bool = Field(
        default=False,
        description="Add image-level context columns (ImageName, etc.)"
    )
    run_context_keys: list[str] | None = Field(
        default=None,
        description="Specific run context keys to include (None = all)"
    )
    image_context_keys: list[str] | None = Field(
        default=None,
        description="Specific image context keys to include (None = all)"
    )


class TableSelectionRequest(BaseModel):
    """Request to lock table selection stage."""
    selected_tables: dict[str, list[str]]  # file path -> table names
    context_options: ContextOptionsRequest | None = Field(
        default=None,
        description="Context application options for output"
    )


class ParseRequest(BaseModel):
    """Request to start parse stage."""
    column_mappings: dict[str, str] | None = None
    selected_tables: list[str] | None = Field(
        default=None,
        description="List of table IDs to extract (None = all)"
    )
    context_options: ContextOptionsRequest | None = Field(
        default=None,
        description="Context application options for output"
    )


class ExportRequest(BaseModel):
    """Request to export as DataSet."""
    name: str | None = None
    description: str | None = None
    aggregation_levels: list[str] | None = None


class FileInfoResponse(BaseModel):
    """Information about a discovered file."""
    path: str
    name: str
    extension: str
    size_bytes: int
    tables: list[str]


class SelectionResponse(BaseModel):
    """Response for selection stage."""
    discovered_files: list[FileInfoResponse]
    selected_files: list[str]


class PreviewResponse(BaseModel):
    """Response for data preview."""
    columns: list[str]
    rows: list[dict]
    row_count: int
    total_rows: int


class ContextInfo(BaseModel):
    """Information about extracted context."""
    run_context: dict[str, str | int | float | None] = Field(
        default_factory=dict,
        description="Run-level context values (LotID, WaferID, etc.)"
    )
    image_contexts: dict[str, dict[str, str | int | float | None]] = Field(
        default_factory=dict,
        description="Image-level context values keyed by image_id"
    )
    available_run_keys: list[str] = Field(
        default_factory=list,
        description="List of available run context keys"
    )
    available_image_keys: list[str] = Field(
        default_factory=list,
        description="List of available image context keys"
    )


class ExtractionResponse(BaseModel):
    """Response for profile-driven extraction.
    
    Per DESIGN §4, §9: Returns tables and context separately,
    allowing user to control context application.
    """
    run_id: str
    profile_id: str
    tables_extracted: int
    table_details: dict[str, dict] = Field(
        default_factory=dict,
        description="Details for each extracted table"
    )
    context: ContextInfo = Field(
        default_factory=ContextInfo,
        description="Extracted context information"
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal validation warnings"
    )
