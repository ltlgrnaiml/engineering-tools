"""API request/response schemas for DAT."""
from datetime import datetime
from pathlib import Path
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


class TableSelectionRequest(BaseModel):
    """Request to lock table selection stage."""
    selected_tables: dict[str, list[str]]  # file path -> table names


class ParseRequest(BaseModel):
    """Request to start parse stage."""
    column_mappings: dict[str, str] | None = None


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
