"""Workflow service for artifact discovery and management."""
import json
from pathlib import Path
from datetime import datetime

from shared.contracts.devtools.workflow import (
    ArtifactType,
    ArtifactStatus,
    ArtifactSummary,
    GraphNode,
    GraphEdge,
    RelationshipType,
    ArtifactListResponse,
    ArtifactGraphResponse,
)

ARTIFACT_DIRECTORIES: dict[ArtifactType, str] = {
    ArtifactType.DISCUSSION: ".discussions",
    ArtifactType.ADR: ".adrs",
    ArtifactType.SPEC: "docs/specs",
    ArtifactType.PLAN: ".plans",
    ArtifactType.CONTRACT: "shared/contracts",
}

TIER_MAP: dict[ArtifactType, int] = {
    ArtifactType.DISCUSSION: 0,
    ArtifactType.ADR: 1,
    ArtifactType.SPEC: 2,
    ArtifactType.CONTRACT: 3,
    ArtifactType.PLAN: 4,
}

def _parse_json_artifact(file_path: Path, artifact_type: ArtifactType) -> ArtifactSummary | None:
    """Parse a JSON artifact file into ArtifactSummary."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ArtifactSummary(
            id=data.get("id", file_path.stem),
            type=artifact_type,
            title=data.get("title", file_path.stem),
            status=ArtifactStatus(data.get("status", "draft")),
            path=str(file_path),
            created_date=data.get("created_date", datetime.now().strftime("%Y-%m-%d")),
            updated_date=data.get("updated_date", datetime.now().strftime("%Y-%m-%d")),
        )
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return None

async def scan_artifacts(artifact_type: ArtifactType | None = None) -> ArtifactListResponse:
    """Scan directories for workflow artifacts.

    Args:
        artifact_type: Optional filter by artifact type.

    Returns:
        ArtifactListResponse containing found artifacts.
    """
    artifacts = []
    types_to_scan = [artifact_type] if artifact_type else list(ARTIFACT_DIRECTORIES.keys())

    for t in types_to_scan:
        dir_path = Path(ARTIFACT_DIRECTORIES[t])
        if not dir_path.exists():
            continue

        for file_path in dir_path.rglob("*.json"):
            artifact = _parse_json_artifact(file_path, t)
            if artifact:
                artifacts.append(artifact)

    return ArtifactListResponse(items=artifacts, total=len(artifacts))

async def get_artifact_graph() -> ArtifactGraphResponse:
    """Generate relationship graph for all artifacts.

    Returns:
        ArtifactGraphResponse with nodes and edges.
    """
    artifacts_resp = await scan_artifacts()
    nodes = []
    edges = []

    for a in artifacts_resp.items:
        nodes.append(
            GraphNode(
                id=a.id,
                type=a.type,
                label=a.title,
                status=a.status,
                file_path=a.path,
                tier=TIER_MAP.get(a.type, 5),
            )
        )

    return ArtifactGraphResponse(nodes=nodes, edges=edges)

async def create_artifact(
    artifact_type: ArtifactType,
    title: str,
    content: dict | None = None,
) -> tuple[ArtifactSummary, str]:
    """Create a new artifact file.

    Args:
        artifact_type: Type of artifact to create.
        title: Title for the artifact.
        content: Optional initial content.

    Returns:
        Tuple of (ArtifactSummary, file_path).
    """
    dir_path = Path(ARTIFACT_DIRECTORIES[artifact_type])
    dir_path.mkdir(parents=True, exist_ok=True)

    # Generate ID and filename
    timestamp = datetime.now().strftime("%Y%m%d")
    artifact_id = f"{artifact_type.value.upper()}-{timestamp}"
    file_name = f"{artifact_id}_{title.replace(' ', '-')}.json"
    file_path = dir_path / file_name

    # Create artifact data
    data = {
        "id": artifact_id,
        "title": title,
        "status": "draft",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "updated_date": datetime.now().strftime("%Y-%m-%d"),
        **(content or {}),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    artifact = ArtifactSummary(
        id=artifact_id,
        type=artifact_type,
        title=title,
        status=ArtifactStatus.DRAFT,
        path=str(file_path),
        created_date=data["created_date"],
        updated_date=data["updated_date"],
    )
    return artifact, str(file_path)

async def delete_artifact(
    artifact_type: ArtifactType,
    artifact_id: str,
) -> tuple[bool, str]:
    """Soft delete artifact by moving to .backup/ directory.

    Args:
        artifact_type: Type of artifact.
        artifact_id: ID of artifact to delete.

    Returns:
        Tuple of (success, backup_path).
    """
    dir_path = Path(ARTIFACT_DIRECTORIES[artifact_type])
    backup_dir = Path(".backup") / artifact_type.value
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Find the file
    for file_path in dir_path.rglob(f"*{artifact_id}*.json"):
        backup_path = backup_dir / file_path.name
        file_path.rename(backup_path)
        return True, str(backup_path)

    return False, ""
