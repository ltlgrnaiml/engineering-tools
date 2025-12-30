"""Tests for DevTools Workflow endpoints.

Tests for the workflow artifact management API endpoints including
list, graph, create, update, and delete operations.
"""

import pytest
from fastapi.testclient import TestClient

from gateway.main import app
from shared.contracts.devtools.workflow import (
    ArtifactType,
    ArtifactStatus,
)


class TestArtifactListEndpoint:
    """Tests for GET /api/devtools/artifacts endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_list_artifacts_returns_200(self, client):
        """Test that listing artifacts returns 200."""
        response = client.get("/api/devtools/artifacts")
        assert response.status_code == 200

    def test_list_artifacts_returns_list_response(self, client):
        """Test that listing artifacts returns proper structure."""
        response = client.get("/api/devtools/artifacts")
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "types" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_list_artifacts_with_type_filter(self, client):
        """Test filtering artifacts by type."""
        response = client.get("/api/devtools/artifacts?type=adr")
        assert response.status_code == 200
        data = response.json()
        # All items should be ADRs if filter works
        for item in data["items"]:
            assert item["type"] == "adr"

    def test_list_artifacts_with_search(self, client):
        """Test searching artifacts by text."""
        response = client.get("/api/devtools/artifacts?search=test")
        assert response.status_code == 200

    def test_list_artifacts_returns_expected_fields(self, client):
        """Test that artifact items have expected fields."""
        response = client.get("/api/devtools/artifacts")
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "type" in item
            assert "title" in item
            assert "status" in item
            assert "file_path" in item


class TestArtifactGraphEndpoint:
    """Tests for GET /api/devtools/artifacts/graph endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_graph_returns_200(self, client):
        """Test that graph endpoint returns 200."""
        response = client.get("/api/devtools/artifacts/graph")
        assert response.status_code == 200

    def test_graph_returns_nodes_and_edges(self, client):
        """Test that graph returns nodes and edges arrays."""
        response = client.get("/api/devtools/artifacts/graph")
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "node_count" in data
        assert "edge_count" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_graph_node_structure(self, client):
        """Test that graph nodes have expected fields."""
        response = client.get("/api/devtools/artifacts/graph")
        data = response.json()
        if data["nodes"]:
            node = data["nodes"][0]
            assert "id" in node
            assert "type" in node
            assert "label" in node
            assert "status" in node
            assert "file_path" in node


class TestArtifactCRUDEndpoints:
    """Tests for artifact CRUD operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_create_artifact_endpoint_exists(self, client):
        """Test that POST /api/devtools/artifacts accepts requests."""
        response = client.post(
            "/api/devtools/artifacts",
            json={
                "type": "discussion",
                "title": "Test Discussion",
                "content": "# Test\n\nTest content",
            },
        )
        # Should return 200 with success/failure response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_update_artifact_endpoint_exists(self, client):
        """Test that PUT /api/devtools/artifacts accepts requests."""
        response = client.put(
            "/api/devtools/artifacts",
            json={
                "file_path": "nonexistent/file.md",
                "content": "Updated content",
            },
        )
        # Should return 200 with error for nonexistent file
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is False  # File doesn't exist

    def test_delete_artifact_endpoint_exists(self, client):
        """Test that DELETE /api/devtools/artifacts accepts requests."""
        response = client.request(
            "DELETE",
            "/api/devtools/artifacts",
            json={
                "file_path": "nonexistent/file.md",
            },
        )
        # Should return 200 with error for nonexistent file
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is False  # File doesn't exist


class TestWorkflowContractImports:
    """Tests for workflow contract imports."""

    def test_artifact_type_enum_values(self):
        """Test ArtifactType enum has expected values."""
        assert ArtifactType.DISCUSSION.value == "discussion"
        assert ArtifactType.ADR.value == "adr"
        assert ArtifactType.SPEC.value == "spec"
        assert ArtifactType.PLAN.value == "plan"
        assert ArtifactType.CONTRACT.value == "contract"

    def test_artifact_status_enum_values(self):
        """Test ArtifactStatus enum has expected values."""
        assert ArtifactStatus.DRAFT.value == "draft"
        assert ArtifactStatus.ACTIVE.value == "active"
        assert ArtifactStatus.DEPRECATED.value == "deprecated"
