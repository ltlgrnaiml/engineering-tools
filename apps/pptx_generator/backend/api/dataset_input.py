"""DataSet input integration for PPTX Generator.

Allows loading data from the shared DataSet format instead of file uploads.

Per ADR-0032: All errors use ErrorResponse contract via errors.py helper.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from apps.pptx_generator.backend.api.errors import (
    raise_not_found,
    raise_internal_error,
)

from apps.pptx_generator.backend.api.projects import projects_db
from apps.pptx_generator.backend.api.data import data_files_db
from apps.pptx_generator.backend.models.data import DataFile
from apps.pptx_generator.backend.models.project import ProjectStatus

router = APIRouter()


class DataSetInputRequest(BaseModel):
    """Request to load data from a DataSet."""
    dataset_id: str


class DataSetInputResponse(BaseModel):
    """Response after loading DataSet."""
    data_file_id: str
    dataset_id: str
    name: str
    row_count: int
    column_names: list[str]


@router.post(
    "/{project_id}/from-dataset",
    response_model=DataSetInputResponse,
    status_code=status.HTTP_201_CREATED,
)
async def load_from_dataset(
    project_id: UUID,
    request: DataSetInputRequest,
) -> DataSetInputResponse:
    """
    Load data from an existing DataSet into a PPTX project.
    
    This enables the "Pipe To" workflow where data from DAT or SOV
    can be used directly for report generation.
    
    Args:
        project_id: Unique project identifier.
        request: DataSet input request with dataset_id.
    
    Returns:
        DataSetInputResponse: Information about the loaded data.
    
    Raises:
        HTTPException: If project not found (404) or DataSet not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))
    
    # Load DataSet from shared storage
    try:
        from shared.storage.artifact_store import ArtifactStore
        
        # Use default workspace - in production this would be configured
        store = ArtifactStore()
        
        if not store.dataset_exists(request.dataset_id):
            raise_not_found("DataSet", request.dataset_id)
        
        # Read the dataset
        df, manifest = store.read_dataset(request.dataset_id)
        
        # Create a DataFile record for this dataset
        data_file = DataFile(
            project_id=project_id,
            filename=f"{manifest.name}.parquet",
            file_path=str(store.get_dataset_paths(request.dataset_id)[0]),
            file_size=0,  # Will be updated
            file_type="parquet",
            row_count=manifest.row_count,
            column_names=[col.name for col in manifest.columns],
        )
        
        # Get actual file size
        parquet_path = store.get_dataset_paths(request.dataset_id)[0]
        if parquet_path.exists():
            data_file.file_size = parquet_path.stat().st_size
        
        # Store the data file record
        data_files_db[data_file.id] = data_file
        
        # Update project
        project = projects_db[project_id]
        project.data_file_id = data_file.id
        project.status = ProjectStatus.DATA_UPLOADED
        project.updated_at = datetime.utcnow()
        
        # Store reference to original dataset for lineage
        if not hasattr(project, 'source_dataset_id'):
            # Add dynamically if model doesn't have it yet
            setattr(project, 'source_dataset_id', request.dataset_id)
        
        return DataSetInputResponse(
            data_file_id=str(data_file.id),
            dataset_id=request.dataset_id,
            name=manifest.name,
            row_count=manifest.row_count,
            column_names=[col.name for col in manifest.columns],
        )
        
    except Exception as e:
        raise_internal_error(f"Failed to load DataSet: {str(e)}", e)


@router.get("/{project_id}/dataset-info")
async def get_dataset_info(project_id: UUID) -> Optional[dict]:
    """
    Get information about the source DataSet for a project.
    
    Args:
        project_id: Unique project identifier.
    
    Returns:
        Optional[dict]: DataSet information if project was loaded from a DataSet.
    
    Raises:
        HTTPException: If project not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))
    
    project = projects_db[project_id]
    source_dataset_id = getattr(project, 'source_dataset_id', None)
    
    if not source_dataset_id:
        return None
    
    try:
        from shared.storage.artifact_store import ArtifactStore
        
        store = ArtifactStore()
        if not store.dataset_exists(source_dataset_id):
            return {"dataset_id": source_dataset_id, "status": "not_found"}
        
        _, manifest = store.read_dataset(source_dataset_id)
        
        return {
            "dataset_id": source_dataset_id,
            "name": manifest.name,
            "created_by_tool": manifest.created_by_tool,
            "row_count": manifest.row_count,
            "column_count": len(manifest.columns),
            "created_at": manifest.created_at.isoformat(),
        }
    except Exception:
        return {"dataset_id": source_dataset_id, "status": "error"}
