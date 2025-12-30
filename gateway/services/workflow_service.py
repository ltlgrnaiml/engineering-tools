"""Workflow Service - Artifact discovery and management for AI Development Workflow.

This service scans project directories for workflow artifacts (discussions, ADRs,
SPECs, plans, contracts) and provides CRUD operations for managing them.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    GraphEdge,
    GraphNode,
    RelationshipType,
)

# Get project root (parent of gateway/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory mappings for each artifact type
ARTIFACT_DIRECTORIES: dict[ArtifactType, Path] = {
    ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
    ArtifactType.ADR: PROJECT_ROOT / ".adrs",
    ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
    ArtifactType.PLAN: PROJECT_ROOT / ".plans",
    ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
}


def scan_artifacts(
    artifact_type: ArtifactType | None = None,
    search: str | None = None,
) -> list[ArtifactSummary]:
    """Scan directories for workflow artifacts.

    Args:
        artifact_type: Optional filter by artifact type.
        search: Optional text search filter.

    Returns:
        List of ArtifactSummary objects.
    """
    artifacts: list[ArtifactSummary] = []

    types_to_scan = [artifact_type] if artifact_type else list(ArtifactType)

    for atype in types_to_scan:
        directory = ARTIFACT_DIRECTORIES.get(atype)
        if not directory or not directory.exists():
            continue

        if atype == ArtifactType.CONTRACT:
            artifacts.extend(_scan_contracts(directory, search))
        elif atype in (ArtifactType.ADR, ArtifactType.SPEC):
            artifacts.extend(_scan_json_artifacts(directory, atype, search))
        else:
            artifacts.extend(_scan_markdown_artifacts(directory, atype, search))

    return artifacts


def _scan_json_artifacts(
    directory: Path,
    artifact_type: ArtifactType,
    search: str | None,
) -> list[ArtifactSummary]:
    """Scan for JSON-based artifacts (ADRs, SPECs)."""
    artifacts = []
    for filepath in sorted(directory.rglob("*.json")):
        # Skip index files
        if filepath.name.lower() in ("index.json", "schema.json"):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            artifact_id = data.get("id", filepath.stem)
            title = data.get("title", "Untitled")
            status_str = data.get("status", "draft")

            # Map status string to enum
            status = _parse_status(status_str)

            summary = ArtifactSummary(
                id=artifact_id,
                type=artifact_type,
                title=title,
                status=status,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
                created_date=data.get("date") or data.get("created_date"),
                updated_date=data.get("updated_date"),
            )

            if search and not _matches_search(summary, search):
                continue

            artifacts.append(summary)
        except (json.JSONDecodeError, KeyError):
            # Skip malformed files
            continue

    return artifacts


def _scan_markdown_artifacts(
    directory: Path,
    artifact_type: ArtifactType,
    search: str | None,
) -> list[ArtifactSummary]:
    """Scan for markdown-based artifacts (discussions, plans)."""
    artifacts = []
    for filepath in sorted(directory.rglob("*.md")):
        # Skip AGENTS.md and other meta files
        if filepath.name in ("AGENTS.md", "README.md", "INDEX.md"):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(2048)  # Read first 2KB for metadata

            # Extract ID from filename (e.g., DISC-001_Title.md -> DISC-001)
            artifact_id = filepath.stem.split("_")[0]

            # Extract title from first H1 header
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else filepath.stem

            # Try to extract status from frontmatter or content
            status_match = re.search(r"status:\s*(\w+)", content, re.IGNORECASE)
            status = _parse_status(status_match.group(1) if status_match else "draft")

            summary = ArtifactSummary(
                id=artifact_id,
                type=artifact_type,
                title=title,
                status=status,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
                created_date=None,
                updated_date=None,
            )

            if search and not _matches_search(summary, search):
                continue

            artifacts.append(summary)
        except (OSError, UnicodeDecodeError):
            continue

    return artifacts


def _scan_contracts(
    directory: Path,
    search: str | None,
) -> list[ArtifactSummary]:
    """Scan for Python contract files."""
    artifacts = []
    for filepath in sorted(directory.rglob("*.py")):
        # Skip __init__.py and test files
        if filepath.name.startswith("__") or filepath.name.startswith("test_"):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(1024)  # Read first 1KB for docstring

            # Extract module docstring
            docstring_match = re.search(r'^"""(.+?)"""', content, re.DOTALL)
            title = filepath.stem
            if docstring_match:
                first_line = docstring_match.group(1).strip().split("\n")[0]
                if first_line:
                    title = first_line

            # Generate ID from path
            rel_path = filepath.relative_to(directory)
            artifact_id = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")

            summary = ArtifactSummary(
                id=f"contract:{artifact_id}",
                type=ArtifactType.CONTRACT,
                title=title,
                status=ArtifactStatus.ACTIVE,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
                created_date=None,
                updated_date=None,
            )

            if search and not _matches_search(summary, search):
                continue

            artifacts.append(summary)
        except (OSError, UnicodeDecodeError):
            continue

    return artifacts


def _parse_status(status_str: str) -> ArtifactStatus:
    """Parse status string to ArtifactStatus enum."""
    status_map = {
        "draft": ArtifactStatus.DRAFT,
        "active": ArtifactStatus.ACTIVE,
        "accepted": ArtifactStatus.ACTIVE,
        "proposed": ArtifactStatus.DRAFT,
        "deprecated": ArtifactStatus.DEPRECATED,
        "superseded": ArtifactStatus.SUPERSEDED,
        "completed": ArtifactStatus.COMPLETED,
    }
    return status_map.get(status_str.lower(), ArtifactStatus.DRAFT)


def _matches_search(artifact: ArtifactSummary, search: str) -> bool:
    """Check if artifact matches search query."""
    search_lower = search.lower()
    return (
        search_lower in artifact.id.lower()
        or search_lower in artifact.title.lower()
        or search_lower in artifact.file_path.lower()
    )


def build_artifact_graph(
    artifacts: list[ArtifactSummary] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build a graph of artifact relationships.

    Args:
        artifacts: Optional list of artifacts. If None, scans all.

    Returns:
        Tuple of (nodes, edges).
    """
    if artifacts is None:
        artifacts = scan_artifacts()

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    artifact_ids = {a.id for a in artifacts}

    for artifact in artifacts:
        # Create node
        nodes.append(
            GraphNode(
                id=artifact.id,
                type=artifact.type,
                label=artifact.title,
                status=artifact.status,
                file_path=artifact.file_path,
            )
        )

        # Extract references from file content
        refs = _extract_references(artifact)
        for ref_id, rel_type in refs:
            if ref_id in artifact_ids:
                edges.append(
                    GraphEdge(
                        source=artifact.id,
                        target=ref_id,
                        relationship=rel_type,
                    )
                )

    return nodes, edges


def _extract_references(
    artifact: ArtifactSummary,
) -> list[tuple[str, RelationshipType]]:
    """Extract references from artifact content."""
    refs: list[tuple[str, RelationshipType]] = []
    filepath = PROJECT_ROOT / artifact.file_path

    if not filepath.exists():
        return refs

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if artifact.file_path.endswith(".json"):
            data = json.loads(content)
            # ADR/SPEC references - handle both string and list values
            if "implements_adr" in data:
                val = data["implements_adr"]
                if isinstance(val, str):
                    refs.append((val, RelationshipType.IMPLEMENTS))
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            refs.append((v, RelationshipType.IMPLEMENTS))
            if "source_discussion" in data:
                val = data["source_discussion"]
                if isinstance(val, str):
                    refs.append((val, RelationshipType.REFERENCES))
            if "supersedes" in data:
                val = data["supersedes"]
                if isinstance(val, str):
                    refs.append((val, RelationshipType.SUPERSEDES))
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            refs.append((v, RelationshipType.SUPERSEDES))
            # Check source_references array
            for ref in data.get("source_references", []):
                if isinstance(ref, dict) and "id" in ref:
                    ref_id = ref["id"]
                    if isinstance(ref_id, str):
                        refs.append((ref_id, RelationshipType.REFERENCES))
        else:
            # Markdown - look for reference patterns
            adr_refs = re.findall(r"ADR-(\d{4})", content)
            for adr_num in adr_refs:
                refs.append((f"ADR-{adr_num}", RelationshipType.REFERENCES))

            spec_refs = re.findall(r"SPEC-(\d{3,4})", content)
            for spec_num in spec_refs:
                refs.append((f"SPEC-{spec_num}", RelationshipType.REFERENCES))

            disc_refs = re.findall(r"DISC-(\d{3})", content)
            for disc_num in disc_refs:
                refs.append((f"DISC-{disc_num}", RelationshipType.REFERENCES))

    except (OSError, json.JSONDecodeError):
        pass

    return refs
