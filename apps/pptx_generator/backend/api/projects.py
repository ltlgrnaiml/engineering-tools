"""Project management endpoints.

Per ADR-0032: All errors use ErrorResponse contract via errors.py helper.
"""

from uuid import UUID

from fastapi import APIRouter, status

from apps.pptx_generator.backend.api.errors import (
    raise_not_found,
    raise_validation_error,
)
from apps.pptx_generator.backend.core.workflow_fsm import (
    WorkflowState,
    WorkflowStep,
    create_workflow_state,
)
from apps.pptx_generator.backend.models.project import Project, ProjectCreate, ProjectStatus

router = APIRouter()

projects_db: dict[UUID, Project] = {}
workflow_states_db: dict[UUID, WorkflowState] = {}


@router.post("", response_model=Project, status_code=status.HTTP_200_OK)
async def create_project(project_data: ProjectCreate) -> Project:
    """
    Create a new PowerPoint generation project.

    Per ADR-0020: Creates workflow state for 7-step guided workflow.

    Args:
        project_data: Project creation data.

    Returns:
        Project: Created project with generated ID.
    """
    project = Project(
        name=project_data.name,
        description=project_data.description,
    )
    projects_db[project.project_id] = project

    # Initialize workflow state per ADR-0020
    workflow_states_db[project.project_id] = create_workflow_state(project.project_id)

    return project


@router.get("", response_model=list[Project])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    """
    List all projects with pagination.

    Args:
        limit: Maximum number of projects to return (default 50).
        offset: Number of projects to skip (default 0).

    Returns:
        List[Project]: List of projects.
    """
    projects = list(projects_db.values())
    # Sort by created_at descending
    projects.sort(key=lambda p: p.created_at, reverse=True)
    return projects[offset:offset + limit]


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """
    Get a specific project by ID.

    Args:
        project_id: Unique project identifier.

    Returns:
        Project: Project details.

    Raises:
        HTTPException: If project not found (404).
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise_not_found("Project", project_id)

    if project_uuid not in projects_db:
        raise_not_found("Project", str(project_uuid))
    return projects_db[project_uuid]


@router.patch("/{project_id}", response_model=Project)
async def update_project_status(
    project_id: UUID,
    new_status: ProjectStatus,
) -> Project:
    """
    Update project status.

    Args:
        project_id: Unique project identifier.
        new_status: New project status.

    Returns:
        Project: Updated project.

    Raises:
        HTTPException: If project not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    project = projects_db[project_id]
    project.status = new_status

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID) -> None:
    """
    Delete a project.

    Args:
        project_id: Unique project identifier.

    Raises:
        HTTPException: If project not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))
    del projects_db[project_id]


@router.delete("/{project_id}/state/{step_name}", response_model=dict)
async def clear_project_state(project_id: UUID, step_name: str) -> dict:
    """
    Clear project state from a specific step onwards (cascade invalidation).

    This enables backward navigation in the workflow by clearing all
    dependent artifacts that would be invalidated by going back.

    Args:
        project_id: Unique project identifier.
        step_name: Step to clear from (template, environment, data, mappings, validation).

    Returns:
        dict: Information about what was cleared.

    Raises:
        HTTPException: If project not found (404) or invalid step (400).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    # Import the databases from other modules
    from apps.pptx_generator.backend.api.data import data_files_db
    from apps.pptx_generator.backend.api.requirements import (
        drm_db,
        env_profiles_db,
        mapping_manifests_db,
        plan_artifacts_db,
    )

    # Define cascade invalidation rules
    step_cascade = {
        "template": ["drm", "environment", "data", "mappings", "validation", "plan"],
        "environment": ["data", "mappings", "validation", "plan"],
        "data": ["mappings", "validation", "plan"],
        "mappings": ["validation", "plan"],
        "validation": ["plan"],
    }

    if step_name not in step_cascade:
        raise_validation_error(f"Invalid step name: {step_name}", field="step_name")

    artifacts_to_clear = step_cascade[step_name]
    cleared = []

    # Clear artifacts based on cascade rules
    if "drm" in artifacts_to_clear and project_id in drm_db:
        del drm_db[project_id]
        cleared.append("drm")

    if "environment" in artifacts_to_clear and project_id in env_profiles_db:
        del env_profiles_db[project_id]
        cleared.append("environment")

    if "data" in artifacts_to_clear and project_id in data_files_db:
        del data_files_db[project_id]
        cleared.append("data")

    if "mappings" in artifacts_to_clear and project_id in mapping_manifests_db:
        del mapping_manifests_db[project_id]
        cleared.append("mappings")

    if "plan" in artifacts_to_clear and project_id in plan_artifacts_db:
        del plan_artifacts_db[project_id]
        cleared.append("plan")

    # Update project status based on what step we're going back to
    project = projects_db[project_id]
    status_map = {
        "template": ProjectStatus.CREATED,
        "environment": ProjectStatus.DRM_EXTRACTED,
        "data": ProjectStatus.ENVIRONMENT_CONFIGURED,
        "mappings": ProjectStatus.DATA_UPLOADED,
        "validation": ProjectStatus.MAPPINGS_CONFIGURED,
    }

    if step_name in status_map:
        project.status = status_map[step_name]
        from datetime import datetime

        project.updated_at = datetime.utcnow()

    return {
        "project_id": str(project_id),
        "cleared_from": step_name,
        "artifacts_cleared": cleared,
        "new_status": project.status,
    }


@router.get("/{project_id}/workflow-state")
async def get_workflow_state(project_id: UUID) -> dict:
    """Get workflow FSM state for a project per ADR-0020.

    Returns the backend workflow state for frontend consumption.

    Args:
        project_id: Unique project identifier.

    Returns:
        Workflow state including current step, step statuses, and generation readiness.

    Raises:
        HTTPException: If project not found (404).
    """
    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    from apps.pptx_generator.backend.core.workflow_fsm import check_generate_allowed

    # Get workflow state if exists, otherwise create fresh state
    if project_id in workflow_states_db:
        state = workflow_states_db[project_id]
    else:
        state = create_workflow_state(project_id)
        workflow_states_db[project_id] = state

    # Convert step statuses to dict
    step_statuses = {
        step.value: status.value
        for step, status in state.step_statuses.items()
    }

    # Check if generation is allowed
    can_generate, validation_msg = check_generate_allowed(state)
    validation_errors = [validation_msg] if validation_msg else []

    # Determine current step (first incomplete step)
    current_step = "generate"
    for step in WorkflowStep:
        if state.step_statuses.get(step) != "completed":
            current_step = step.value
            break

    return {
        "project_id": str(project_id),
        "current_step": current_step,
        "step_statuses": step_statuses,
        "can_generate": can_generate,
        "validation_errors": validation_errors,
    }
