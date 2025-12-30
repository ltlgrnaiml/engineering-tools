"""Tests for DevTools Workflow Manager endpoints.

Tests for artifact discovery, graph generation, and CRUD operations.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from gateway.main import app
from shared.contracts.devtools.workflow import (
    ArtifactListResponse,
    ArtifactType,
    ArtifactStatus,
    ArtifactSummary,
    GraphResponse,
    GraphNode,
    GraphNodeType,
)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_workflow_service():
    with patch("gateway.services.devtools_service.get_workflow_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

class TestArtifactEndpoints:
    """Tests for /api/devtools/artifacts endpoints."""

    def test_list_artifacts_returns_200(self, client, mock_workflow_service):
        """Test listing artifacts returns 200 and list."""
        # Setup mock
        mock_artifacts = [
            ArtifactSummary(
                id="DISC-001",
                type=ArtifactType.DISCUSSION,
                title="Test Discussion",
                status=ArtifactStatus.ACTIVE,
                file_path=".discussions/DISC-001.md"
            ),
            ArtifactSummary(
                id="ADR-001",
                type=ArtifactType.ADR,
                title="Test ADR",
                status=ArtifactStatus.ACCEPTED,
                file_path=".adrs/ADR-001.json"
            )
        ]
        mock_workflow_service.scan_artifacts.return_value = mock_artifacts

        # Execute
        response = client.get("/api/devtools/artifacts")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["artifacts"]) == 2
        assert data["artifacts"][0]["id"] == "DISC-001"
        mock_workflow_service.scan_artifacts.assert_called_once_with(artifact_type=None, search=None)

    def test_list_artifacts_with_filter(self, client, mock_workflow_service):
        """Test filtering artifacts by type."""
        # Setup mock
        mock_workflow_service.scan_artifacts.return_value = []

        # Execute
        response = client.get("/api/devtools/artifacts?type=adr")

        # Verify
        assert response.status_code == 200
        mock_workflow_service.scan_artifacts.assert_called_once_with(artifact_type=ArtifactType.ADR, search=None)

    def test_list_artifacts_with_search(self, client, mock_workflow_service):
        """Test searching artifacts."""
        # Setup mock
        mock_workflow_service.scan_artifacts.return_value = []

        # Execute
        response = client.get("/api/devtools/artifacts?search=test")

        # Verify
        assert response.status_code == 200
        mock_workflow_service.scan_artifacts.assert_called_once_with(artifact_type=None, search="test")

    def test_get_graph_returns_200(self, client, mock_workflow_service):
        """Test getting artifact graph."""
        # Setup mock
        mock_graph = GraphResponse(
            nodes=[
                GraphNode(
                    id="DISC-001",
                    type=GraphNodeType.DISCUSSION,
                    label="DISC-001",
                    status="active",
                    file_path=".discussions/DISC-001.md",
                    tier=0
                )
            ],
            edges=[]
        )
        mock_workflow_service.get_graph.return_value = mock_graph

        # Execute
        response = client.get("/api/devtools/artifacts/graph")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 1
        assert len(data["edges"]) == 0
        assert data["nodes"][0]["id"] == "DISC-001"

    def test_create_artifact_placeholder(self, client):
        """Test create artifact returns placeholder."""
        response = client.post(
            "/api/devtools/artifacts",
            json={
                "type": "discussion",
                "title": "New Discussion"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Not implemented" in data["message"]

    def test_update_artifact_placeholder(self, client):
        """Test update artifact returns placeholder."""
        response = client.put(
            "/api/devtools/artifacts/DISC-001",
            json={
                "content": "Updated content"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Not implemented" in data["message"]

    def test_delete_artifact_placeholder(self, client):
        """Test delete artifact returns placeholder."""
        response = client.delete("/api/devtools/artifacts/DISC-001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Not implemented" in data["message"]
