"""Requirements API endpoints.

Endpoints for TOM v2 requirements management:
- Environment profile configuration
- Mapping suggestions and configuration
- Four Bars validation
- Plan building
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from apps.pptx_generator.backend.api.projects import projects_db
from apps.pptx_generator.backend.models.drm import DerivedRequirementsManifest
from apps.pptx_generator.backend.models.environment_profile import EnvironmentProfile
from apps.pptx_generator.backend.models.mapping_manifest import (
    ContextMapping,
    MappingManifest,
    MappingSuggestion,
    MetricMapping,
)
from apps.pptx_generator.backend.models.plan_artifacts import PlanArtifacts
from apps.pptx_generator.backend.models.project import ProjectStatus
from apps.pptx_generator.backend.models.validation_report import FourBarsStatus
from apps.pptx_generator.backend.services.mapping_suggester import MappingSuggesterService
from apps.pptx_generator.backend.services.plan_builder import PlanBuilderService
from apps.pptx_generator.backend.services.requirements_validator import RequirementsValidatorService

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory databases (replace with real DB in production)
env_profiles_db: dict[UUID, EnvironmentProfile] = {}
mapping_manifests_db: dict[UUID, MappingManifest] = {}
plan_artifacts_db: dict[UUID, PlanArtifacts] = {}
drm_db: dict[UUID, DerivedRequirementsManifest] = {}  # Imported from templates.py

# Service instances
mapping_suggester = MappingSuggesterService()
requirements_validator = RequirementsValidatorService()
plan_builder = PlanBuilderService()


class EnvironmentProfileCreate(BaseModel):
    """Request model for creating environment profile."""

    name: str
    source: str
    roots: dict
    job_context: dict
    encoding_policy: list = ["utf-8", "utf-8-sig", "cp1252"]


class ContextMappingsCreate(BaseModel):
    """Request model for creating context mappings."""

    mappings: list[dict]


class MetricsMappingsCreate(BaseModel):
    """Request model for creating metrics mappings."""

    mappings: list[dict]


class MappingSuggestionsResponse(BaseModel):
    """Response model for mapping suggestions."""

    context_suggestions: dict[str, MappingSuggestion]
    metrics_suggestions: dict[str, MappingSuggestion]


@router.post(
    "/{project_id}/environment-profile",
    response_model=EnvironmentProfile,
    status_code=status.HTTP_201_CREATED,
)
async def create_environment_profile(
    project_id: UUID, profile_data: EnvironmentProfileCreate
) -> EnvironmentProfile:
    """Create or update environment profile for project.

    Args:
        project_id: Project ID.
        profile_data: Environment profile configuration.

    Returns:
        Created environment profile.

    Raises:
        HTTPException: If project not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Create environment profile
    from apps.pptx_generator.backend.models.environment_profile import DataRoots, JobContext, SourceType

    profile = EnvironmentProfile(
        project_id=project_id,
        name=profile_data.name,
        source=SourceType(profile_data.source),
        roots=DataRoots(**profile_data.roots),
        job_context=JobContext(**profile_data.job_context),
        encoding_policy=profile_data.encoding_policy,
    )

    env_profiles_db[profile.id] = profile

    # Update project
    project = projects_db[project_id]
    project.environment_profile_id = profile.id
    project.status = ProjectStatus.ENVIRONMENT_CONFIGURED

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    logger.info(f"Environment profile created for project {project_id}")
    return profile


@router.post("/{project_id}/mappings/suggest", response_model=MappingSuggestionsResponse)
async def suggest_mappings(project_id: UUID) -> MappingSuggestionsResponse:
    """Auto-suggest mappings for project.

    Args:
        project_id: Project ID.

    Returns:
        Mapping suggestions for contexts and metrics.

    Raises:
        HTTPException: If project, DRM, or data not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = projects_db[project_id]

    # Check DRM exists
    if not project.drm_id or project.drm_id not in drm_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DRM not found. Please parse template first.",
        )

    # Check data file exists (would get columns from data file)
    # For now, use placeholder columns
    data_columns = [
        "LCDU",
        "Side",
        "Wafer",
        "CD",
        "LWR",
        "ImageColumn",
    ]

    drm = drm_db[project.drm_id]

    # Generate suggestions
    context_suggestions = mapping_suggester.suggest_context_mappings(drm, data_columns)
    metrics_suggestions = mapping_suggester.suggest_metrics_mappings(drm, data_columns)

    logger.info(f"Generated mapping suggestions for project {project_id}")

    return MappingSuggestionsResponse(
        context_suggestions=context_suggestions,
        metrics_suggestions=metrics_suggestions,
    )


@router.post(
    "/{project_id}/mappings/context",
    response_model=MappingManifest,
    status_code=status.HTTP_201_CREATED,
)
async def save_context_mappings(
    project_id: UUID, mappings_data: ContextMappingsCreate
) -> MappingManifest:
    """Save context mappings for project.

    Args:
        project_id: Project ID.
        mappings_data: Context mappings.

    Returns:
        Updated mapping manifest.

    Raises:
        HTTPException: If project not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get or create mapping manifest
    project = projects_db[project_id]
    if project.context_mapping_id and project.context_mapping_id in mapping_manifests_db:
        manifest = mapping_manifests_db[project.context_mapping_id]
    else:
        manifest = MappingManifest(project_id=project_id)
        mapping_manifests_db[manifest.id] = manifest
        project.context_mapping_id = manifest.id

    # Update context mappings
    manifest.context_mappings = [
        ContextMapping(**mapping_dict) for mapping_dict in mappings_data.mappings
    ]

    from datetime import datetime

    manifest.updated_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()

    logger.info(f"Context mappings saved for project {project_id}")
    return manifest


@router.post(
    "/{project_id}/mappings/metrics",
    response_model=MappingManifest,
    status_code=status.HTTP_201_CREATED,
)
async def save_metrics_mappings(
    project_id: UUID, mappings_data: MetricsMappingsCreate
) -> MappingManifest:
    """Save metrics mappings for project.

    Args:
        project_id: Project ID.
        mappings_data: Metrics mappings.

    Returns:
        Updated mapping manifest.

    Raises:
        HTTPException: If project not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get or create mapping manifest
    project = projects_db[project_id]
    manifest_id = project.context_mapping_id or project.metrics_mapping_id
    if manifest_id and manifest_id in mapping_manifests_db:
        manifest = mapping_manifests_db[manifest_id]
    else:
        manifest = MappingManifest(project_id=project_id)
        mapping_manifests_db[manifest.id] = manifest

    # Update metrics mappings
    manifest.metrics_mappings = [
        MetricMapping(**mapping_dict) for mapping_dict in mappings_data.mappings
    ]

    from datetime import datetime

    manifest.updated_at = datetime.utcnow()
    project.metrics_mapping_id = manifest.id
    project.status = ProjectStatus.MAPPINGS_CONFIGURED
    project.updated_at = datetime.utcnow()

    logger.info(f"Metrics mappings saved for project {project_id}")
    return manifest


@router.get("/{project_id}/validation/four-bars", response_model=FourBarsStatus)
async def get_four_bars_status(project_id: UUID) -> FourBarsStatus:
    """Get Four Bars validation status.

    Args:
        project_id: Project ID.

    Returns:
        FourBarsStatus with validation results.

    Raises:
        HTTPException: If project, DRM, or mappings not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = projects_db[project_id]

    # Check DRM exists
    if not project.drm_id or project.drm_id not in drm_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DRM not found. Please parse template first.",
        )

    # Get mappings (may be empty)
    manifest_id = project.context_mapping_id or project.metrics_mapping_id
    if manifest_id and manifest_id in mapping_manifests_db:
        mappings = mapping_manifests_db[manifest_id]
    else:
        # Create empty manifest for validation
        mappings = MappingManifest(project_id=project_id)

    drm = drm_db[project.drm_id]

    # Validate
    status_result = requirements_validator.validate_four_bars(drm, mappings)

    logger.info(
        f"Four Bars validation for project {project_id}: all_green={status_result.is_all_green()}"
    )

    return status_result


@router.post(
    "/{project_id}/plan/build",
    response_model=PlanArtifacts,
    status_code=status.HTTP_201_CREATED,
)
async def build_plan(project_id: UUID) -> PlanArtifacts:
    """Build frozen plan artifacts.

    Args:
        project_id: Project ID.

    Returns:
        PlanArtifacts with lookup, request_graph, and manifest.

    Raises:
        HTTPException: If validation fails or prerequisites missing.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = projects_db[project_id]

    # Check prerequisites
    if not project.drm_id or project.drm_id not in drm_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DRM not found. Please parse template first.",
        )

    if not project.environment_profile_id or project.environment_profile_id not in env_profiles_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment profile not configured.",
        )

    manifest_id = project.context_mapping_id or project.metrics_mapping_id
    if not manifest_id or manifest_id not in mapping_manifests_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mappings not configured.",
        )

    # Validate Four Bars
    drm = drm_db[project.drm_id]
    mappings = mapping_manifests_db[manifest_id]
    validation_status = requirements_validator.validate_four_bars(drm, mappings)

    if not validation_status.is_all_green():
        blocking_issues = validation_status.get_blocking_issues()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed. Blocking issues: {', '.join(blocking_issues)}",
        )

    # Build plan
    env_profile = env_profiles_db[project.environment_profile_id]
    artifacts = plan_builder.build_plan(drm, mappings, env_profile, project_id)

    plan_artifacts_db[artifacts.id] = artifacts

    # Update project
    project.plan_artifacts_id = artifacts.id
    project.status = ProjectStatus.PLAN_FROZEN

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    logger.info(f"Plan built for project {project_id}")
    return artifacts


@router.get("/{project_id}/plan", response_model=PlanArtifacts)
async def get_plan(project_id: UUID) -> PlanArtifacts:
    """Get plan artifacts for project.

    Args:
        project_id: Project ID.

    Returns:
        PlanArtifacts if exists.

    Raises:
        HTTPException: If project or plan not found.
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = projects_db[project_id]

    if not project.plan_artifacts_id or project.plan_artifacts_id not in plan_artifacts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not built yet. Please build plan first.",
        )

    return plan_artifacts_db[project.plan_artifacts_id]
