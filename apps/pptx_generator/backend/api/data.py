"""Data file and mapping management endpoints.

Per ADR-0032: All errors use ErrorResponse contract via errors.py helper.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from apps.pptx_generator.backend.api.errors import (
    raise_not_found,
    raise_validation_error,
    raise_internal_error,
)
from apps.pptx_generator.backend.api.projects import projects_db
from apps.pptx_generator.backend.core.config import settings
from apps.pptx_generator.backend.models.data import AssetMapping, DataFile
from apps.pptx_generator.backend.models.project import ProjectStatus
from apps.pptx_generator.backend.services.data_processor import DataProcessorService
from apps.pptx_generator.backend.services.storage import StorageService

router = APIRouter()

data_files_db: dict[UUID, DataFile] = {}
asset_mappings_db: dict[UUID, AssetMapping] = {}

storage_service = StorageService()
data_processor = DataProcessorService()


@router.post("/{project_id}/upload", response_model=DataFile, status_code=status.HTTP_201_CREATED)
async def upload_data_file(
    project_id: UUID,
    file: UploadFile = File(...),
) -> DataFile:
    """
    Upload a data file for a project.

    Args:
        project_id: Unique project identifier.
        file: Data file (CSV or Excel).

    Returns:
        DataFile: Uploaded data file metadata.

    Raises:
        HTTPException: If project not found (404) or file is invalid (400).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    if not file.filename:
        raise_validation_error("No filename provided", field="file")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_DATA_EXTENSIONS:
        raise_validation_error(
            f"Invalid file type. Allowed: {settings.ALLOWED_DATA_EXTENSIONS}",
            field="file",
        )

    data_file = DataFile(
        project_id=project_id,
        filename=file.filename,
        file_path="",
        file_size=0,
        file_type=file_extension[1:],
        row_count=0,
        column_names=[],
    )

    try:
        file_path = await storage_service.save_upload(
            file.file,
            data_file.id,
            file_extension,
        )
        data_file.file_path = str(file_path)
        data_file.file_size = file_path.stat().st_size

        column_names = await data_processor.get_column_names(file_path)
        row_count = await data_processor.get_row_count(file_path)

        data_file.column_names = column_names
        data_file.row_count = row_count
    except Exception as e:
        raise_internal_error(f"Failed to process data file: {str(e)}", e)

    data_files_db[data_file.id] = data_file

    project = projects_db[project_id]
    project.data_file_id = data_file.id
    project.status = ProjectStatus.DATA_UPLOADED

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    return data_file


@router.get("/{project_id}/data-file", response_model=DataFile)
async def get_data_file(project_id: UUID) -> DataFile:
    """
    Get data file information for a project.

    Args:
        project_id: Unique project identifier.

    Returns:
        DataFile: Data file metadata.

    Raises:
        HTTPException: If project or data file not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    project = projects_db[project_id]
    if not project.data_file_id or project.data_file_id not in data_files_db:
        raise_not_found("DataFile", "No data file uploaded for this project")

    return data_files_db[project.data_file_id]


@router.post(
    "/{project_id}/mapping", response_model=AssetMapping, status_code=status.HTTP_201_CREATED
)
async def create_asset_mapping(
    project_id: UUID,
    mapping: AssetMapping,
) -> AssetMapping:
    """
    Create or update asset mapping for a project.

    Args:
        project_id: Unique project identifier.
        mapping: Asset mapping configuration.

    Returns:
        AssetMapping: Created or updated asset mapping.

    Raises:
        HTTPException: If project not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    mapping.project_id = project_id

    asset_mappings_db[mapping.id] = mapping

    project = projects_db[project_id]
    project.asset_mapping_id = mapping.id
    project.status = ProjectStatus.MAPPING_CONFIGURED

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    if (
        project.template_id
        and project.data_file_id
        and project.shape_map_id
        and project.asset_mapping_id
    ):
        project.status = ProjectStatus.READY_TO_GENERATE
        project.updated_at = datetime.utcnow()

    return mapping


@router.get("/{project_id}/mapping", response_model=AssetMapping)
async def get_asset_mapping(project_id: UUID) -> AssetMapping:
    """
    Get asset mapping for a project.

    Args:
        project_id: Unique project identifier.

    Returns:
        AssetMapping: Asset mapping configuration.

    Raises:
        HTTPException: If project or mapping not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    project = projects_db[project_id]
    if not project.asset_mapping_id or project.asset_mapping_id not in asset_mappings_db:
        raise_not_found("AssetMapping", "No asset mapping configured for this project")

    return asset_mappings_db[project.asset_mapping_id]


@router.post("/{project_id}/domain-knowledge", status_code=status.HTTP_201_CREATED)
async def upload_domain_knowledge(
    project_id: UUID,
    file: UploadFile = File(...),
) -> dict[str, str]:
    """
    Upload domain knowledge file for a project.

    Args:
        project_id: Unique project identifier.
        file: Domain knowledge file (YAML or JSON).

    Returns:
        Dict[str, str]: Success message with file ID.

    Raises:
        HTTPException: If project not found (404) or file is invalid (400).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    if not file.filename:
        raise_validation_error("No filename provided", field="file")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_DOMAIN_EXTENSIONS:
        raise_validation_error(
            f"Invalid file type. Allowed: {settings.ALLOWED_DOMAIN_EXTENSIONS}",
            field="file",
        )

    from uuid import uuid4

    domain_id = uuid4()

    try:
        file_path = await storage_service.save_upload(
            file.file,
            domain_id,
            file_extension,
        )

        await data_processor.read_domain_knowledge(file_path)

        project = projects_db[project_id]
        project.domain_knowledge_id = domain_id

        from datetime import datetime

        project.updated_at = datetime.utcnow()

    except Exception as e:
        raise_internal_error(f"Failed to process domain knowledge file: {str(e)}", e)

    return {
        "message": "Domain knowledge uploaded successfully",
        "domain_knowledge_id": str(domain_id),
    }
