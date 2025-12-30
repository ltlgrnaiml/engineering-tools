"""Tests for DevTools Workflow Manager endpoints.

Per PLAN-001 M1: Backend API Foundation.
"""

import pytest

from gateway.services.workflow_service import build_artifact_graph, scan_artifacts
from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    GraphResponse,
)


class TestScanArtifacts:
    """Tests for scan_artifacts function."""

    def test_scan_all_artifacts(self) -> None:
        """Scan should return artifacts from all directories."""
        results = scan_artifacts()
        assert isinstance(results, list)
        # Should find at least some artifacts in the repo
        assert len(results) > 0

    def test_scan_by_type_adr(self) -> None:
        """Scan should filter by ADR type."""
        results = scan_artifacts(artifact_type=ArtifactType.ADR)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.ADR

    def test_scan_by_type_spec(self) -> None:
        """Scan should filter by SPEC type."""
        results = scan_artifacts(artifact_type=ArtifactType.SPEC)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.SPEC

    def test_scan_by_type_plan(self) -> None:
        """Scan should filter by PLAN type."""
        results = scan_artifacts(artifact_type=ArtifactType.PLAN)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.PLAN

    def test_scan_with_search(self) -> None:
        """Scan should filter by search term."""
        # Search for "workflow" which should match ADR-0043, SPEC-0040, etc.
        results = scan_artifacts(search="workflow")
        assert isinstance(results, list)
        # All results should contain the search term in title or id
        for artifact in results:
            assert (
                "workflow" in artifact.title.lower()
                or "workflow" in artifact.id.lower()
            )

    def test_artifact_summary_structure(self) -> None:
        """Each artifact should have required fields."""
        results = scan_artifacts()
        if results:
            artifact = results[0]
            assert isinstance(artifact, ArtifactSummary)
            assert artifact.id is not None
            assert artifact.type is not None
            assert artifact.title is not None
            assert artifact.status is not None
            assert artifact.file_path is not None


class TestBuildArtifactGraph:
    """Tests for build_artifact_graph function."""

    def test_graph_structure(self) -> None:
        """Graph should have nodes and edges lists."""
        graph = build_artifact_graph()
        assert isinstance(graph, GraphResponse)
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)

    def test_graph_has_nodes(self) -> None:
        """Graph should have at least one node."""
        graph = build_artifact_graph()
        assert len(graph.nodes) > 0

    def test_node_structure(self) -> None:
        """Each node should have required fields."""
        graph = build_artifact_graph()
        for node in graph.nodes:
            assert node.id is not None
            assert node.type is not None
            assert node.label is not None
            assert node.status is not None
            assert node.file_path is not None

    def test_edge_structure(self) -> None:
        """Each edge should have required fields."""
        graph = build_artifact_graph()
        for edge in graph.edges:
            assert edge.source is not None
            assert edge.target is not None
            assert edge.relationship is not None

    def test_graph_relationships_exist(self) -> None:
        """Graph should have some relationships (edges)."""
        graph = build_artifact_graph()
        # We have ADR-0043 -> SPEC-0040, so should have at least 1 edge
        assert len(graph.edges) > 0
