"""DevTools routes for workflow artifacts."""
from fastapi import APIRouter, Path, Query

from shared.contracts.devtools.workflow import (
    ArtifactType,
    ArtifactListResponse,
    ArtifactGraphResponse,
    ArtifactCreateRequest,
    ArtifactCreateResponse,
    ArtifactDeleteResponse,
)
from gateway.services import workflow_service

router = APIRouter()


@router.get("/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    type: ArtifactType | None = Query(None, description="Filter by artifact type"),
    search: str | None = Query(None, description="Search text in title"),
) -> ArtifactListResponse:
    """List all workflow artifacts.

    Args:
        type: Optional filter by artifact type.
        search: Optional text search in title.

    Returns:
        List of artifacts with total count.
    """
    return await workflow_service.scan_artifacts(artifact_type=type, search=search)


@router.get("/artifacts/graph", response_model=ArtifactGraphResponse)
async def get_artifact_graph(
    focus: str | None = Query(None, description="Artifact ID to center graph on"),
    depth: int = Query(2, ge=1, le=5, description="Levels of relationships to include"),
) -> ArtifactGraphResponse:
    """Get artifact relationship graph.

    Args:
        focus: Optional artifact ID to center graph on.
        depth: How many levels of relationships to include.

    Returns:
        Graph with nodes and edges for visualization.
    """
    return await workflow_service.get_artifact_graph(focus=focus, depth=depth)


@router.post("/artifacts", response_model=ArtifactCreateResponse)
async def create_artifact(
    request: ArtifactCreateRequest,
) -> ArtifactCreateResponse:
    """Create a new workflow artifact.

    Args:
        request: Artifact creation request.

    Returns:
        Created artifact with file path.
    """
    artifact, path = await workflow_service.create_artifact(
        artifact_type=request.type,
        title=request.title,
        content=request.content,
    )
    return ArtifactCreateResponse(artifact=artifact, path=path)


@router.delete("/artifacts/{artifact_type}/{artifact_id}", response_model=ArtifactDeleteResponse)
async def delete_artifact(
    artifact_type: ArtifactType = Path(..., description="Artifact type"),
    artifact_id: str = Path(..., description="Artifact ID"),
) -> ArtifactDeleteResponse:
    """Soft delete an artifact (moves to .backup/).

    Args:
        artifact_type: Type of artifact.
        artifact_id: ID of artifact to delete.

    Returns:
        Deletion result with backup path.
    """
    success, backup_path = await workflow_service.delete_artifact(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
    )
    return ArtifactDeleteResponse(success=success, backup_path=backup_path)
