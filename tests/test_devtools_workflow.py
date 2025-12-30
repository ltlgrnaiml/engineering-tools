"""Tests for DevTools Workflow Manager endpoints.

Tests for the workflow artifact management API endpoints per ADR-0043.
"""

import pytest
from fastapi.testclient import TestClient

from gateway.main import app


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

    def test_list_artifacts_returns_required_fields(self, client):
        """Test that artifact list has required fields."""
        response = client.get("/api/devtools/artifacts")
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_list_artifacts_with_type_filter(self, client):
        """Test filtering artifacts by type."""
        response = client.get("/api/devtools/artifacts?type=adr")
        assert response.status_code == 200
        data = response.json()
        assert "filtered_type" in data

    def test_list_artifacts_with_search_query(self, client):
        """Test searching artifacts."""
        response = client.get("/api/devtools/artifacts?search=test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestArtifactGraphEndpoint:
    """Tests for GET /api/devtools/artifacts/graph endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_graph_endpoint_returns_200(self, client):
        """Test that graph endpoint returns 200."""
        response = client.get("/api/devtools/artifacts/graph")
        assert response.status_code == 200

    def test_graph_returns_nodes_and_edges(self, client):
        """Test that graph response has nodes and edges."""
        response = client.get("/api/devtools/artifacts/graph")
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "total_nodes" in data
        assert "total_edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_graph_with_type_filter(self, client):
        """Test graph endpoint with type filter."""
        response = client.get("/api/devtools/artifacts/graph?type=adr")
        assert response.status_code == 200


class TestArtifactReadEndpoint:
    """Tests for GET /api/devtools/artifacts/{artifact_id} endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_read_nonexistent_artifact_returns_404(self, client):
        """Test that reading nonexistent artifact returns 404."""
        response = client.get("/api/devtools/artifacts/NONEXISTENT-999")
        assert response.status_code == 404

    def test_read_artifact_requires_artifact_id(self, client):
        """Test that artifact ID is required."""
        response = client.get("/api/devtools/artifacts/")
        assert response.status_code in [200, 404, 422]


class TestArtifactCreateEndpoint:
    """Tests for POST /api/devtools/artifacts endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_create_artifact_returns_501(self, client):
        """Test that create artifact returns 501 (not implemented)."""
        response = client.post(
            "/api/devtools/artifacts",
            json={
                "type": "discussion",
                "title": "Test Discussion",
                "content": "Test content",
            },
        )
        assert response.status_code == 501


class TestArtifactUpdateEndpoint:
    """Tests for PUT /api/devtools/artifacts/{artifact_id} endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_update_artifact_returns_501(self, client):
        """Test that update artifact returns 501 (not implemented)."""
        response = client.put(
            "/api/devtools/artifacts/TEST-001",
            json={
                "file_path": "test.md",
                "content": "Updated content",
            },
        )
        assert response.status_code == 501


class TestArtifactDeleteEndpoint:
    """Tests for DELETE /api/devtools/artifacts/{artifact_id} endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_delete_artifact_returns_501(self, client):
        """Test that delete artifact returns 501 (not implemented)."""
        response = client.request(
            "DELETE",
            "/api/devtools/artifacts/TEST-001",
            json={
                "file_path": "test.md",
                "permanent": False,
            },
        )
        assert response.status_code == 501
