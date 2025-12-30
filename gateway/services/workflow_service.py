"""Workflow artifact scanning and graph building service.

Per PLAN-001 M1: Backend API Foundation.
Provides functions for discovering and relating workflow artifacts.
"""

import json
import re
from pathlib import Path

from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    GraphEdge,
    GraphNode,
    GraphResponse,
    RelationshipType,
)

__version__ = "2025.12.01"


# =============================================================================
# Constants
# =============================================================================

ARTIFACT_DIRECTORIES: dict[ArtifactType, str] = {
    ArtifactType.DISCUSSION: ".discussions",
    ArtifactType.ADR: ".adrs",
    ArtifactType.SPEC: "docs/specs",
    ArtifactType.PLAN: ".plans",
    ArtifactType.CONTRACT: "shared/contracts",
}


# =============================================================================
# Artifact Scanning
# =============================================================================


def scan_artifacts(
    artifact_type: ArtifactType | None = None,
    search: str | None = None,
) -> list[ArtifactSummary]:
    """Scan filesystem for workflow artifacts.

    Args:
        artifact_type: Filter by artifact type (optional).
        search: Filter by title/ID containing this string (optional).

    Returns:
        List of artifact summaries found.
    """
    results: list[ArtifactSummary] = []
    types_to_scan = [artifact_type] if artifact_type else list(ArtifactType)

    for atype in types_to_scan:
        directory = Path(ARTIFACT_DIRECTORIES[atype])
        if not directory.exists():
            continue

        # Determine file patterns based on artifact type
        if atype == ArtifactType.ADR:
            pattern = "*.json"
        elif atype == ArtifactType.SPEC:
            pattern = "*.json"
        elif atype == ArtifactType.CONTRACT:
            pattern = "*.py"
        else:
            pattern = "*.md"

        for file_path in directory.rglob(pattern):
            # Skip templates, __init__.py, __pycache__, etc.
            if (
                file_path.name.startswith(".")
                or file_path.name.startswith("_")
                or "template" in file_path.name.lower()
                or "__pycache__" in str(file_path)
                or file_path.name == "AGENTS.md"
                or file_path.name == "INDEX.md"
            ):
                continue

            artifact = _parse_artifact(file_path, atype)
            if artifact:
                # Apply search filter
                if search:
                    search_lower = search.lower()
                    if (
                        search_lower not in artifact.title.lower()
                        and search_lower not in artifact.id.lower()
                    ):
                        continue
                results.append(artifact)

    return sorted(results, key=lambda a: a.id)


def _parse_artifact(file_path: Path, atype: ArtifactType) -> ArtifactSummary | None:
    """Parse artifact metadata from file.

    Args:
        file_path: Path to artifact file.
        atype: Type of artifact.

    Returns:
        ArtifactSummary or None if parsing fails.
    """
    try:
        if atype in (ArtifactType.ADR, ArtifactType.SPEC):
            return _parse_json_artifact(file_path, atype)
        elif atype == ArtifactType.CONTRACT:
            return _parse_python_artifact(file_path)
        else:
            return _parse_markdown_artifact(file_path, atype)
    except Exception:
        return None


def _parse_json_artifact(file_path: Path, atype: ArtifactType) -> ArtifactSummary | None:
    """Parse JSON-based artifact (ADR, SPEC)."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    artifact_id = data.get("id", file_path.stem)
    title = data.get("title", artifact_id)
    status_str = data.get("status", "draft")
    updated_date = data.get("updated_date")

    # Map status string to enum
    try:
        status = ArtifactStatus(status_str)
    except ValueError:
        status = ArtifactStatus.DRAFT

    return ArtifactSummary(
        id=artifact_id,
        type=atype,
        title=title,
        status=status,
        file_path=str(file_path),
        updated_date=updated_date,
    )


def _parse_markdown_artifact(
    file_path: Path, atype: ArtifactType
) -> ArtifactSummary | None:
    """Parse markdown-based artifact (Discussion, Plan)."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read(2000)  # Read first 2KB for metadata

    # Extract ID from filename (e.g., DISC-001_title.md -> DISC-001)
    match = re.match(r"^(DISC-\d+|PLAN-\d+)", file_path.stem)
    artifact_id = match.group(1) if match else file_path.stem

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else artifact_id

    # Try to detect status from content
    if "status: active" in content.lower() or "## active" in content.lower():
        status = ArtifactStatus.ACTIVE
    elif "status: completed" in content.lower():
        status = ArtifactStatus.COMPLETED
    else:
        status = ArtifactStatus.DRAFT

    return ArtifactSummary(
        id=artifact_id,
        type=atype,
        title=title,
        status=status,
        file_path=str(file_path),
        updated_date=None,
    )


def _parse_python_artifact(file_path: Path) -> ArtifactSummary | None:
    """Parse Python contract file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read(1000)  # Read first 1KB

    # Use module name as ID
    artifact_id = file_path.stem

    # Extract docstring for title
    docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
    if docstring_match:
        # First line of docstring
        title = docstring_match.group(1).strip().split("\n")[0]
    else:
        title = artifact_id

    return ArtifactSummary(
        id=artifact_id,
        type=ArtifactType.CONTRACT,
        title=title,
        status=ArtifactStatus.ACTIVE,
        file_path=str(file_path),
        updated_date=None,
    )


# =============================================================================
# Graph Building
# =============================================================================


def build_artifact_graph() -> GraphResponse:
    """Build the artifact relationship graph.

    Returns:
        GraphResponse with nodes and edges representing artifact relationships.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    artifacts = scan_artifacts()

    # Create nodes for all artifacts
    for artifact in artifacts:
        nodes.append(
            GraphNode(
                id=artifact.id,
                type=artifact.type,
                label=artifact.title,
                status=artifact.status,
                file_path=artifact.file_path,
            )
        )

    # Build edges by scanning for references
    artifact_ids = {a.id for a in artifacts}

    for artifact in artifacts:
        if artifact.type in (ArtifactType.ADR, ArtifactType.SPEC):
            # Parse JSON artifacts for explicit references
            try:
                with open(artifact.file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Check implements_adr field (SPEC -> ADR)
                implements = data.get("implements_adr", [])
                for adr_id in implements:
                    if adr_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=adr_id,
                                relationship=RelationshipType.IMPLEMENTS,
                            )
                        )

                # Check resulting_specs field (ADR -> SPEC)
                specs = data.get("resulting_specs", [])
                for spec in specs:
                    spec_id = spec.get("id") if isinstance(spec, dict) else spec
                    if spec_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=spec_id,
                                relationship=RelationshipType.CREATES,
                            )
                        )

                # Check source_references in plans
                refs = data.get("source_references", [])
                for ref in refs:
                    ref_id = ref.get("id") if isinstance(ref, dict) else ref
                    if ref_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=ref_id,
                                relationship=RelationshipType.REFERENCES,
                            )
                        )

            except Exception:
                pass

    return GraphResponse(nodes=nodes, edges=edges)
