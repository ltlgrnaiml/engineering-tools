"""Workflow Service - Artifact scanning and management for AI Development Workflow.

Per ADR-0043: DevTools Workflow Manager UI Architecture.

This service scans and manages workflow artifacts (Discussions, ADRs, SPECs, Plans, Contracts)
and builds relationship graphs between them.
"""

import json
from pathlib import Path
from typing import Any

from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    GraphEdge,
    GraphNode,
    RelationshipType,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent

ARTIFACT_DIRECTORIES = {
    ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
    ArtifactType.ADR: PROJECT_ROOT / ".adrs",
    ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
    ArtifactType.PLAN: PROJECT_ROOT / ".plans",
    ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
}


def scan_artifacts(
    artifact_type: ArtifactType | None = None,
    search_query: str | None = None,
) -> list[ArtifactSummary]:
    """Scan directories for workflow artifacts.

    Args:
        artifact_type: Optional filter by artifact type.
        search_query: Optional text search in titles/content.

    Returns:
        List of ArtifactSummary objects.
    """
    artifacts: list[ArtifactSummary] = []

    types_to_scan = (
        [artifact_type] if artifact_type else list(ArtifactType)
    )

    for atype in types_to_scan:
        directory = ARTIFACT_DIRECTORIES.get(atype)
        if not directory or not directory.exists():
            continue

        if atype == ArtifactType.CONTRACT:
            artifacts.extend(_scan_contracts(directory, search_query))
        elif atype in (ArtifactType.ADR, ArtifactType.SPEC):
            artifacts.extend(_scan_json_artifacts(directory, atype, search_query))
        elif atype in (ArtifactType.DISCUSSION, ArtifactType.PLAN):
            artifacts.extend(_scan_markdown_artifacts(directory, atype, search_query))

    return artifacts


def _scan_json_artifacts(
    directory: Path,
    artifact_type: ArtifactType,
    search_query: str | None,
) -> list[ArtifactSummary]:
    """Scan JSON artifacts (ADRs, SPECs).

    Args:
        directory: Directory to scan.
        artifact_type: Type of artifact.
        search_query: Optional text search.

    Returns:
        List of ArtifactSummary objects.
    """
    artifacts: list[ArtifactSummary] = []

    for json_file in directory.rglob("*.json"):
        if json_file.name.startswith("."):
            continue

        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)

            artifact_id = data.get("id", json_file.stem)
            title = data.get("title", json_file.stem)
            status = data.get("status", "draft")

            if search_query and search_query.lower() not in title.lower():
                continue

            rel_path = json_file.relative_to(PROJECT_ROOT).as_posix()

            artifacts.append(
                ArtifactSummary(
                    id=artifact_id,
                    type=artifact_type,
                    title=title,
                    status=_normalize_status(status),
                    file_path=rel_path,
                    created_date=data.get("created_date"),
                    updated_date=data.get("updated_date"),
                    author=data.get("author"),
                    summary=data.get("summary") or data.get("context", "")[:200],
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return artifacts


def _scan_markdown_artifacts(
    directory: Path,
    artifact_type: ArtifactType,
    search_query: str | None,
) -> list[ArtifactSummary]:
    """Scan markdown artifacts (Discussions, Plans).

    Args:
        directory: Directory to scan.
        artifact_type: Type of artifact.
        search_query: Optional text search.

    Returns:
        List of ArtifactSummary objects.
    """
    artifacts: list[ArtifactSummary] = []

    extension = ".md" if artifact_type == ArtifactType.DISCUSSION else ".md"
    for md_file in directory.rglob(f"*{extension}"):
        if md_file.name.startswith(".") or md_file.name == "AGENTS.md":
            continue

        try:
            with md_file.open(encoding="utf-8") as f:
                content = f.read()

            artifact_id = _extract_id_from_filename(md_file.stem)
            title = _extract_title_from_markdown(content) or md_file.stem

            if search_query and search_query.lower() not in title.lower():
                continue

            rel_path = md_file.relative_to(PROJECT_ROOT).as_posix()

            artifacts.append(
                ArtifactSummary(
                    id=artifact_id,
                    type=artifact_type,
                    title=title,
                    status=ArtifactStatus.DRAFT,
                    file_path=rel_path,
                    summary=content[:200] if content else None,
                )
            )
        except Exception:
            continue

    return artifacts


def _scan_contracts(
    directory: Path,
    search_query: str | None,
) -> list[ArtifactSummary]:
    """Scan Python contract files.

    Args:
        directory: Directory to scan.
        search_query: Optional text search.

    Returns:
        List of ArtifactSummary objects.
    """
    artifacts: list[ArtifactSummary] = []

    for py_file in directory.rglob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "__init__.py":
            continue

        try:
            with py_file.open(encoding="utf-8") as f:
                content = f.read()

            title = py_file.stem.replace("_", " ").title()

            if search_query and search_query.lower() not in title.lower():
                continue

            rel_path = py_file.relative_to(PROJECT_ROOT).as_posix()

            version = _extract_version_from_python(content)

            artifacts.append(
                ArtifactSummary(
                    id=py_file.stem,
                    type=ArtifactType.CONTRACT,
                    title=title,
                    status=ArtifactStatus.ACTIVE,
                    file_path=rel_path,
                    summary=f"Contract v{version}" if version else "Contract",
                )
            )
        except Exception:
            continue

    return artifacts


def build_artifact_graph(artifacts: list[ArtifactSummary]) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build relationship graph from artifacts.

    Args:
        artifacts: List of artifacts to analyze.

    Returns:
        Tuple of (nodes, edges).
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for artifact in artifacts:
        tier = _determine_tier(artifact.type)
        nodes.append(
            GraphNode(
                id=artifact.id,
                type=artifact.type,
                label=artifact.title,
                status=artifact.status,
                file_path=artifact.file_path,
                tier=tier,
            )
        )

        edges.extend(_extract_references(artifact))

    return nodes, edges


def _extract_references(artifact: ArtifactSummary) -> list[GraphEdge]:
    """Extract references from artifact content.

    Args:
        artifact: Artifact to analyze.

    Returns:
        List of graph edges.
    """
    edges: list[GraphEdge] = []

    try:
        file_path = PROJECT_ROOT / artifact.file_path
        if not file_path.exists():
            return edges

        if artifact.type in (ArtifactType.ADR, ArtifactType.SPEC, ArtifactType.PLAN):
            with file_path.open(encoding="utf-8") as f:
                data = json.load(f)

            if "implements_adr" in data:
                adr_ids = data["implements_adr"]
                if isinstance(adr_ids, str):
                    adr_ids = [adr_ids]
                for adr_id in adr_ids:
                    edges.append(
                        GraphEdge(
                            source=artifact.id,
                            target=adr_id,
                            relationship=RelationshipType.IMPLEMENTS,
                        )
                    )

            if "source_discussion" in data:
                disc_id = data["source_discussion"]
                edges.append(
                    GraphEdge(
                        source=artifact.id,
                        target=disc_id,
                        relationship=RelationshipType.REFERENCES,
                    )
                )

            if "source_references" in data:
                refs = data["source_references"]
                for ref in refs:
                    if isinstance(ref, dict) and "id" in ref:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=ref["id"],
                                relationship=RelationshipType.REFERENCES,
                            )
                        )

            if "supersedes" in data:
                superseded_ids = data["supersedes"]
                if isinstance(superseded_ids, str):
                    superseded_ids = [superseded_ids]
                for superseded_id in superseded_ids:
                    edges.append(
                        GraphEdge(
                            source=artifact.id,
                            target=superseded_id,
                            relationship=RelationshipType.SUPERSEDES,
                        )
                    )

    except Exception:
        pass

    return edges


def _normalize_status(status: str) -> ArtifactStatus:
    """Normalize status string to ArtifactStatus enum.

    Args:
        status: Raw status string.

    Returns:
        ArtifactStatus enum value.
    """
    status_map = {
        "draft": ArtifactStatus.DRAFT,
        "active": ArtifactStatus.ACTIVE,
        "proposed": ArtifactStatus.PROPOSED,
        "accepted": ArtifactStatus.ACCEPTED,
        "deprecated": ArtifactStatus.DEPRECATED,
        "superseded": ArtifactStatus.SUPERSEDED,
        "pending": ArtifactStatus.PENDING,
        "in_progress": ArtifactStatus.IN_PROGRESS,
        "completed": ArtifactStatus.COMPLETED,
    }
    return status_map.get(status.lower(), ArtifactStatus.DRAFT)


def _determine_tier(artifact_type: ArtifactType) -> int:
    """Determine workflow tier for artifact type per ADR-0041.

    Args:
        artifact_type: Type of artifact.

    Returns:
        Tier number (0-5).
    """
    tier_map = {
        ArtifactType.DISCUSSION: 0,
        ArtifactType.ADR: 1,
        ArtifactType.SPEC: 2,
        ArtifactType.CONTRACT: 3,
        ArtifactType.PLAN: 4,
    }
    return tier_map.get(artifact_type, 0)


def _extract_id_from_filename(filename: str) -> str:
    """Extract artifact ID from filename.

    Args:
        filename: File name without extension.

    Returns:
        Artifact ID.
    """
    parts = filename.split("_", 1)
    return parts[0] if parts else filename


def _extract_title_from_markdown(content: str) -> str | None:
    """Extract title from markdown content.

    Args:
        content: Markdown content.

    Returns:
        Title or None.
    """
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _extract_version_from_python(content: str) -> str | None:
    """Extract __version__ from Python file.

    Args:
        content: Python file content.

    Returns:
        Version string or None.
    """
    for line in content.split("\n"):
        if line.startswith("__version__"):
            parts = line.split("=")
            if len(parts) == 2:
                return parts[1].strip().strip('"').strip("'")
    return None
