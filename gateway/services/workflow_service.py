"""Workflow Service - Artifact scanning and graph generation.

This service scans the repository for workflow artifacts (Discussions, ADRs, SPECs, Plans, Contracts)
and manages their relationships.
"""

import json
import re
from pathlib import Path
from typing import Any

from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    GraphEdge,
    GraphEdgeType,
    GraphNode,
    GraphNodeType,
    GraphResponse,
)

# Project root (parent of gateway/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory mappings
ARTIFACT_DIRS = {
    ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
    ArtifactType.ADR: PROJECT_ROOT / ".adrs",
    ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
    ArtifactType.PLAN: PROJECT_ROOT / ".plans",
    ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
}


class WorkflowService:
    """Service for managing workflow artifacts."""

    def scan_artifacts(self, artifact_type: ArtifactType | None = None, search: str | None = None) -> list[ArtifactSummary]:
        """Scan repository for artifacts, optionally filtered by type and search query."""
        artifacts: list[ArtifactSummary] = []
        
        types_to_scan = [artifact_type] if artifact_type else list(ArtifactType)
        
        for type_ in types_to_scan:
            if type_ not in ARTIFACT_DIRS:
                continue
                
            directory = ARTIFACT_DIRS[type_]
            if not directory.exists():
                continue
                
            if type_ == ArtifactType.DISCUSSION:
                artifacts.extend(self._scan_discussions(directory))
            elif type_ == ArtifactType.ADR:
                artifacts.extend(self._scan_adrs(directory))
            elif type_ == ArtifactType.SPEC:
                artifacts.extend(self._scan_specs(directory))
            elif type_ == ArtifactType.PLAN:
                artifacts.extend(self._scan_plans(directory))
            elif type_ == ArtifactType.CONTRACT:
                artifacts.extend(self._scan_contracts(directory))
                
        # Filter by search query
        if search:
            search_lower = search.lower()
            artifacts = [
                a for a in artifacts 
                if search_lower in a.title.lower() or search_lower in a.id.lower()
            ]
            
        return sorted(artifacts, key=lambda a: a.id)

    def _scan_discussions(self, directory: Path) -> list[ArtifactSummary]:
        """Scan .discussions/ for markdown files."""
        artifacts = []
        for filepath in directory.rglob("*.md"):
            if filepath.name == "AGENTS.md" or filepath.name == "README.md":
                continue
                
            # Parse ID and Title from filename or content
            # Expected format: DISC-XXX_Title.md or similar
            filename = filepath.stem
            
            # Simple parsing strategy
            id_match = re.match(r"(DISC-\d+)", filename)
            id_ = id_match.group(1) if id_match else filename
            
            # Read file for title and status (if in frontmatter)
            title = filename
            status = ArtifactStatus.ACTIVE # Default
            
            try:
                content = filepath.read_text(encoding="utf-8")
                # Try to extract title from first header
                header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if header_match:
                    title = header_match.group(1).strip()
            except Exception:
                pass

            artifacts.append(ArtifactSummary(
                id=id_,
                type=ArtifactType.DISCUSSION,
                title=title,
                status=status,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
            ))
        return artifacts

    def _scan_adrs(self, directory: Path) -> list[ArtifactSummary]:
        """Scan .adrs/ for JSON files."""
        artifacts = []
        for filepath in directory.rglob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                artifacts.append(ArtifactSummary(
                    id=data.get("id", filepath.stem),
                    type=ArtifactType.ADR,
                    title=data.get("title", filepath.stem),
                    status=data.get("status", ArtifactStatus.PROPOSED),
                    file_path=str(filepath.relative_to(PROJECT_ROOT)),
                ))
            except Exception:
                # Fallback for malformed files
                artifacts.append(ArtifactSummary(
                    id=filepath.stem,
                    type=ArtifactType.ADR,
                    title=filepath.stem,
                    status=ArtifactStatus.DRAFT,
                    file_path=str(filepath.relative_to(PROJECT_ROOT)),
                ))
        return artifacts

    def _scan_specs(self, directory: Path) -> list[ArtifactSummary]:
        """Scan docs/specs/ for JSON files."""
        artifacts = []
        for filepath in directory.rglob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                artifacts.append(ArtifactSummary(
                    id=data.get("id", filepath.stem),
                    type=ArtifactType.SPEC,
                    title=data.get("title", filepath.stem),
                    status=data.get("status", ArtifactStatus.DRAFT),
                    file_path=str(filepath.relative_to(PROJECT_ROOT)),
                ))
            except Exception:
                pass
        return artifacts

    def _scan_plans(self, directory: Path) -> list[ArtifactSummary]:
        """Scan .plans/ for JSON files."""
        artifacts = []
        for filepath in directory.rglob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                artifacts.append(ArtifactSummary(
                    id=data.get("id", filepath.stem),
                    type=ArtifactType.PLAN,
                    title=data.get("title", filepath.stem),
                    status=data.get("status", ArtifactStatus.DRAFT),
                    file_path=str(filepath.relative_to(PROJECT_ROOT)),
                ))
            except Exception:
                pass
        return artifacts

    def _scan_contracts(self, directory: Path) -> list[ArtifactSummary]:
        """Scan shared/contracts/ for Python files."""
        artifacts = []
        for filepath in directory.rglob("*.py"):
            if filepath.name == "__init__.py":
                continue
                
            # Use filename as ID/Title for now, maybe parse docstring later
            id_ = filepath.stem
            title = filepath.stem.replace("_", " ").title()
            
            artifacts.append(ArtifactSummary(
                id=id_,
                type=ArtifactType.CONTRACT,
                title=title,
                status=ArtifactStatus.ACTIVE,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
            ))
        return artifacts
    
    def get_graph(self) -> GraphResponse:
        """Build graph of all artifacts and their relationships."""
        artifacts = self.scan_artifacts()
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        
        # Map artifact type to graph node type
        type_map = {
            ArtifactType.DISCUSSION: GraphNodeType.DISCUSSION,
            ArtifactType.ADR: GraphNodeType.ADR,
            ArtifactType.SPEC: GraphNodeType.SPEC,
            ArtifactType.PLAN: GraphNodeType.PLAN,
            ArtifactType.CONTRACT: GraphNodeType.CONTRACT,
        }
        
        # Map artifact type to tier
        tier_map = {
            ArtifactType.DISCUSSION: 0,
            ArtifactType.ADR: 1,
            ArtifactType.SPEC: 2,
            ArtifactType.CONTRACT: 3,
            ArtifactType.PLAN: 4,
        }

        for art in artifacts:
            nodes.append(GraphNode(
                id=art.id,
                type=type_map.get(art.type, GraphNodeType.DISCUSSION), # Fallback
                label=art.id, # Use ID as label for graph compactness
                status=str(art.status),
                file_path=art.file_path,
                tier=tier_map.get(art.type, 0)
            ))
            
            # TODO: Extract relationships (edges)
            # This requires reading content and parsing 'implements', 'references', etc.
            # For M1, we can start with scanning, edges can be refined in T-M1-04.
            
        return GraphResponse(nodes=nodes, edges=edges)

# Singleton instance
_service = WorkflowService()

def get_workflow_service() -> WorkflowService:
    return _service
