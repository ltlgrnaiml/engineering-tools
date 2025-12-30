"""DevTools routes for Workflow Manager APIs."""

from fastapi import APIRouter, Query

from gateway.services.workflow_service import (
    build_artifact_graph,
    create_artifact,
    delete_artifact,
    scan_artifacts,
    update_artifact,
)
from shared.contracts.devtools.workflow import (
    ArtifactDeleteRequest,
    ArtifactDeleteResponse,
    ArtifactGraphResponse,
    ArtifactListResponse,
    ArtifactType,
    ArtifactWriteRequest,
    ArtifactWriteResponse,
)

router = APIRouter()


@router.get("/artifacts", response_model=ArtifactListResponse, name="GET_artifacts")
async def list_artifacts(
    artifact_type: ArtifactType | None = Query(None, alias="type"),
    search: str | None = Query(None, description="Case-insensitive substring search"),
) -> ArtifactListResponse:
    """List workflow artifacts across the repository.

    Args:
        artifact_type: Optional artifact type filter.
        search: Optional case-insensitive substring filter.

    Returns:
        List response containing artifacts and total count.
    """

    items = scan_artifacts(artifact_type=artifact_type, search=search)
    return ArtifactListResponse(items=items, total=len(items))


@router.get("/artifacts/graph", response_model=ArtifactGraphResponse, name="artifacts/graph")
async def get_artifact_graph(
    artifact_type: ArtifactType | None = Query(None, alias="type"),
    search: str | None = Query(None, description="Case-insensitive substring search"),
) -> ArtifactGraphResponse:
    """Get artifact relationship graph."""

    return build_artifact_graph(artifact_type=artifact_type, search=search)


@router.post("/artifacts", response_model=ArtifactWriteResponse, name="POST_artifacts")
async def post_artifact(request: ArtifactWriteRequest) -> ArtifactWriteResponse:
    """Create a new artifact file."""

    return create_artifact(request)


@router.put("/artifacts", response_model=ArtifactWriteResponse, name="PUT_artifacts")
async def put_artifact(request: ArtifactWriteRequest) -> ArtifactWriteResponse:
    """Update an existing artifact file."""

    return update_artifact(request)


@router.delete("/artifacts", response_model=ArtifactDeleteResponse, name="DELETE_artifacts")
async def delete_artifact_route(request: ArtifactDeleteRequest) -> ArtifactDeleteResponse:
    """Soft-delete an artifact by moving it to a backup."""

    return delete_artifact(request)
