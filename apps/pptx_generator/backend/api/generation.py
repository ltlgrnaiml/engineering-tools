"""Presentation generation endpoints.

Per ADR-0018: Uses ErrorResponse contract for standardized errors.
Per ADR-0019/0019: Uses RenderRequest/RenderResult contracts for generation tracking.
Per ADR-0032: All errors use ErrorResponse contract via errors.py helper.
"""

import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from apps.pptx_generator.backend.api.data import asset_mappings_db, data_files_db
from apps.pptx_generator.backend.api.errors import (
    raise_internal_error,
    raise_not_found,
    raise_validation_error,
)
from apps.pptx_generator.backend.api.projects import projects_db, workflow_states_db
from apps.pptx_generator.backend.api.requirements import mapping_manifests_db
from apps.pptx_generator.backend.api.templates import templates_db
from apps.pptx_generator.backend.core.workflow_fsm import (
    check_generate_allowed,
)
from apps.pptx_generator.backend.models.drm import MappingSourceType
from apps.pptx_generator.backend.models.generation import (
    GenerationRequest,
    GenerationResponse,
    GenerationStatus,
)
from apps.pptx_generator.backend.models.project import ProjectStatus
from apps.pptx_generator.backend.services.data_processor import DataProcessorService
from apps.pptx_generator.backend.services.presentation_generator import PresentationGeneratorService
from apps.pptx_generator.backend.services.storage import StorageService
from shared.contracts.pptx.template import (
    RenderResult,
    RenderStageState,
)

logger = logging.getLogger(__name__)

router = APIRouter()

generations_db: dict[UUID, GenerationResponse] = {}
render_results_db: dict[str, RenderResult] = {}  # Per ADR-0019: Track render metrics

storage_service = StorageService()
data_processor = DataProcessorService()
presentation_generator = PresentationGeneratorService()


@router.post("", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_presentation(request: GenerationRequest) -> GenerationResponse:
    """
    Generate a PowerPoint presentation from project data.

    Args:
        request: Generation request with project ID and optional output filename.

    Returns:
        GenerationResponse: Generation task information.

    Raises:
        HTTPException: If project not found (404) or not ready (400).
    """
    project_id = request.project_id

    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    project = projects_db[project_id]

    # Per ADR-0020: Check workflow state for validation gating
    if project_id in workflow_states_db:
        workflow_state = workflow_states_db[project_id]
        allowed, error_msg = check_generate_allowed(workflow_state)
        if not allowed:
            raise_validation_error(f"Generation blocked per ADR-0020: {error_msg}")
    else:
        # Legacy check: Accept both READY_TO_GENERATE and PLAN_FROZEN
        if project.status not in [ProjectStatus.READY_TO_GENERATE, ProjectStatus.PLAN_FROZEN]:
            raise_validation_error(
                f"Project not ready for generation. Current status: {project.status}",
                field="status",
            )

    # Check for required components (support both old and new workflow)
    has_mappings = project.asset_mapping_id or (
        project.context_mapping_id and project.metrics_mapping_id
    )
    if not all(
        [
            project.template_id,
            project.data_file_id,
            has_mappings,
        ]
    ):
        raise_validation_error(
            "Project missing required components (template, data, or mapping)"
        )

    # Per ADR-0026: Capture lineage information
    source_dataset_id = getattr(project, 'source_dataset_id', None)
    template_id_str = str(project.template_id) if project.template_id else None

    generation = GenerationResponse(
        project_id=project_id,
        source_dataset_id=source_dataset_id,
        template_id=template_id_str,
    )
    generations_db[generation.id] = generation

    # Per ADR-0019: Create RenderResult for tracking
    render_id = f"render_{uuid4().hex[:12]}"
    render_result = RenderResult(
        template_id=str(project.template_id) if project.template_id else "unknown",
        render_id=render_id,
        job_id=str(generation.id),
        state=RenderStageState.PENDING,
        started_at=datetime.utcnow(),
    )
    render_results_db[render_id] = render_result

    project.status = ProjectStatus.GENERATING
    project.updated_at = datetime.utcnow()

    try:
        logger.info(f"[GENERATION] Starting generation for project {project_id}")
        generation.status = GenerationStatus.PROCESSING
        render_result.state = RenderStageState.LOADING_DATA
        render_result.progress_message = "Loading data and template"

        logger.info(f"[GENERATION] Retrieving template {project.template_id}")
        if project.template_id is None:
            raise ValueError("Project has no template_id")
        template = templates_db[project.template_id]
        logger.info(f"[GENERATION] Template path: {template.file_path}")

        logger.info(f"[GENERATION] Retrieving data file {project.data_file_id}")
        if project.data_file_id is None:
            raise ValueError("Project has no data_file_id")
        data_file = data_files_db[project.data_file_id]
        logger.info(f"[GENERATION] Data file path: {data_file.file_path}")

        # Support both old and new workflow for mappings
        if project.asset_mapping_id:
            logger.info(
                f"[GENERATION] Using old workflow - asset_mapping_id: {project.asset_mapping_id}"
            )
            asset_mapping = asset_mappings_db[project.asset_mapping_id]
            mappings_list = [mapping.model_dump() for mapping in asset_mapping.mappings]
        else:
            logger.info("[GENERATION] Using TOM v2 workflow")
            logger.info(f"[GENERATION] context_mapping_id: {project.context_mapping_id}")
            logger.info(f"[GENERATION] metrics_mapping_id: {project.metrics_mapping_id}")

            manifest_id = project.context_mapping_id or project.metrics_mapping_id
            logger.info(f"[GENERATION] Using manifest_id: {manifest_id}")
            if manifest_id is None:
                raise ValueError("Project has no mapping manifest")
            manifest = mapping_manifests_db[manifest_id]

            logger.info(
                f"[GENERATION] Manifest has {len(manifest.context_mappings)} context mappings"
            )
            logger.info(
                f"[GENERATION] Manifest has {len(manifest.metrics_mappings)} metrics mappings"
            )

            # Convert TOM v2 mappings to old format expected by data processor
            # Old format: {"shape_name": "...", "data_column": "...", "transformation": None, "default_value": "..."}
            # TOM v2 format: {"context_name": "...", "source_type": "column", "source_column": "...", "default_value": "..."}
            mappings_list = []

            for ctx_mapping in manifest.context_mappings:
                # ContextMapping has source_type to determine how to get the value
                if ctx_mapping.source_type == MappingSourceType.COLUMN:
                    data_column = ctx_mapping.source_column
                    default_value = None
                elif ctx_mapping.source_type == MappingSourceType.DEFAULT:
                    data_column = None
                    default_value = ctx_mapping.default_value
                else:  # REGEX - not directly supported by old format
                    data_column = None
                    default_value = ctx_mapping.default_value

                old_format = {
                    "shape_name": ctx_mapping.context_name,
                    "data_column": data_column,
                    "transformation": None,
                    "default_value": default_value,
                }
                logger.debug(f"[GENERATION] Converted context mapping: {old_format}")
                mappings_list.append(old_format)

            for metric_mapping in manifest.metrics_mappings:
                # MetricMapping always uses source_column (no source_type attribute)
                old_format = {
                    "shape_name": metric_mapping.metric_name,
                    "data_column": metric_mapping.source_column,
                    "transformation": None,
                    "default_value": None,
                }
                logger.debug(f"[GENERATION] Converted metrics mapping: {old_format}")
                mappings_list.append(old_format)

            logger.info(f"[GENERATION] Total mappings converted: {len(mappings_list)}")

        domain_knowledge = None
        if project.domain_knowledge_id:
            logger.info(f"[GENERATION] Loading domain knowledge {project.domain_knowledge_id}")
            domain_path = storage_service.get_upload_path(
                project.domain_knowledge_id,
                ".yaml",
            )
            if domain_path.exists():
                domain_knowledge = await data_processor.read_domain_knowledge(domain_path)
                logger.info("[GENERATION] Domain knowledge loaded")

        logger.info("[GENERATION] Preparing data for generation")
        prepared_data = await data_processor.prepare_data_for_generation(
            Path(data_file.file_path),
            mappings_list,
            domain_knowledge,
        )
        logger.info(f"[GENERATION] Data prepared: {len(prepared_data)} records")

        # DEBUG: Log first record structure
        if prepared_data:
            logger.info(f"[GENERATION] First record keys: {list(prepared_data[0].keys())}")
            logger.info(f"[GENERATION] First record sample: {prepared_data[0]}")
            # Also print to ensure visibility
            print(f"[GENERATION] Prepared data records: {len(prepared_data)}")
            print(f"[GENERATION] First record keys: {list(prepared_data[0].keys())}")
            print(f"[GENERATION] First record: {prepared_data[0]}")

        output_filename = request.output_filename or f"{project.name}.pptx"
        if not output_filename.endswith(".pptx"):
            output_filename += ".pptx"

        output_path = storage_service.get_generated_path(generation.id)
        logger.info(f"[GENERATION] Output path: {output_path}")

        logger.info("[GENERATION] Calling presentation generator")
        render_result.state = RenderStageState.RENDERING
        render_result.progress_message = "Rendering presentation"
        render_result.progress_pct = 50.0

        await presentation_generator.generate_presentation(
            Path(template.file_path),
            prepared_data,
            output_path,
        )
        logger.info("[GENERATION] Presentation generated successfully")

        # Update render result with success metrics
        render_result.state = RenderStageState.COMPLETED
        render_result.completed_at = datetime.utcnow()
        render_result.output_path = str(output_path)
        render_result.progress_pct = 100.0
        render_result.progress_message = "Complete"
        if output_path.exists():
            render_result.output_size_bytes = output_path.stat().st_size
        render_result.render_duration_ms = (
            (render_result.completed_at - render_result.started_at).total_seconds() * 1000
            if render_result.started_at else 0.0
        )

        generation.status = GenerationStatus.COMPLETED
        generation.output_file_path = str(output_path)
        generation.output_filename = output_filename
        generation.completed_at = datetime.utcnow()

        project.status = ProjectStatus.COMPLETED
        project.updated_at = datetime.utcnow()

        logger.info(f"[GENERATION] Generation completed: {generation.id}")

    except Exception as e:
        logger.error(f"[GENERATION] Generation failed with error: {str(e)}", exc_info=True)
        generation.status = GenerationStatus.FAILED
        generation.error_message = str(e)
        generation.completed_at = datetime.utcnow()

        # Update render result with failure
        render_result.state = RenderStageState.FAILED
        render_result.completed_at = datetime.utcnow()
        render_result.errors.append(str(e))
        render_result.progress_message = f"Failed: {str(e)}"

        project.status = ProjectStatus.FAILED
        project.updated_at = datetime.utcnow()

        raise_internal_error(f"Generation failed: {str(e)}", e)

    return generation


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation_status(generation_id: UUID) -> GenerationResponse:
    """
    Get the status of a generation task.

    Args:
        generation_id: Unique generation task identifier.

    Returns:
        GenerationResponse: Generation task information.

    Raises:
        HTTPException: If generation not found (404).
    """
    if generation_id not in generations_db:
        raise_not_found("Generation", str(generation_id))

    return generations_db[generation_id]


@router.get("/{generation_id}/download")
async def download_presentation(generation_id: UUID) -> FileResponse:
    """
    Download a generated PowerPoint presentation.

    Args:
        generation_id: Unique generation task identifier.

    Returns:
        FileResponse: PowerPoint file download.

    Raises:
        HTTPException: If generation not found (404) or file not ready (400).
    """
    if generation_id not in generations_db:
        raise_not_found("Generation", str(generation_id))

    generation = generations_db[generation_id]

    if generation.status != GenerationStatus.COMPLETED:
        raise_validation_error(
            f"Generation not completed. Current status: {generation.status}",
            field="status",
        )

    if not generation.output_file_path:
        raise_not_found("OutputFile", "Output file not found")

    file_path = Path(generation.output_file_path)
    if not file_path.exists():
        raise_not_found("OutputFile", "Output file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=generation.output_filename or "presentation.pptx",
    )
