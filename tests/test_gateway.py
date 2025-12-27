"""Tests for Gateway endpoints.

Tests for the gateway API endpoints including health, datasets, and pipelines.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from gateway.main import app


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Test that health check returns status field."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_check_returns_version(self, client):
        """Test that health check returns version."""
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data

    def test_health_check_returns_tool_status(self, client):
        """Test that health check returns tool status."""
        response = client.get("/api/health")
        data = response.json()
        assert "tools" in data
        assert "dat" in data["tools"]
        assert "sov" in data["tools"]
        assert "pptx" in data["tools"]


class TestDataSetEndpoints:
    """Tests for /api/datasets endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_list_datasets_returns_200(self, client):
        """Test that listing datasets returns 200."""
        response = client.get("/api/datasets/v1/")
        assert response.status_code == 200

    def test_list_datasets_returns_list(self, client):
        """Test that listing datasets returns a list."""
        response = client.get("/api/datasets/v1/")
        data = response.json()
        assert isinstance(data, list)

    def test_list_datasets_with_tool_filter(self, client):
        """Test filtering datasets by tool."""
        response = client.get("/api/datasets/v1/?tool=dat")
        assert response.status_code == 200

    def test_list_datasets_with_limit(self, client):
        """Test limiting dataset results."""
        response = client.get("/api/datasets/v1/?limit=5")
        assert response.status_code == 200

    def test_get_nonexistent_dataset_returns_404(self, client):
        """Test that getting nonexistent dataset returns 404."""
        response = client.get("/api/datasets/v1/nonexistent_id")
        assert response.status_code == 404


class TestPipelineEndpoints:
    """Tests for /api/pipelines endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_list_pipelines_returns_200(self, client):
        """Test that listing pipelines returns 200."""
        response = client.get("/api/pipelines/v1/")
        assert response.status_code == 200

    def test_list_pipelines_returns_list(self, client):
        """Test that listing pipelines returns a list."""
        response = client.get("/api/pipelines/v1/")
        data = response.json()
        assert isinstance(data, list)

    def test_create_pipeline(self, client):
        """Test creating a pipeline."""
        response = client.post(
            "/api/pipelines/v1/",
            json={
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "steps": [
                    {
                        "step_index": 0,
                        "step_type": "dat:aggregate",
                        "config": {"source_files": ["test.csv"]},
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Pipeline"
        assert "pipeline_id" in data

    def test_get_created_pipeline(self, client):
        """Test getting a created pipeline."""
        # Create a pipeline first
        create_response = client.post(
            "/api/pipelines/v1/",
            json={
                "name": "Get Test Pipeline",
                "steps": [
                    {
                        "step_index": 0,
                        "step_type": "pptx:generate",
                        "config": {},
                    }
                ],
            },
        )
        pipeline_id = create_response.json()["pipeline_id"]
        
        # Get it
        response = client.get(f"/api/pipelines/v1/{pipeline_id}")
        assert response.status_code == 200
        assert response.json()["pipeline_id"] == pipeline_id

    def test_get_nonexistent_pipeline_returns_404(self, client):
        """Test that getting nonexistent pipeline returns 404."""
        response = client.get("/api/pipelines/v1/nonexistent_id")
        assert response.status_code == 404


class TestOpenAPIDocs:
    """Tests for OpenAPI documentation."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_openapi_docs_available(self, client):
        """Test that /api/docs is available."""
        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Test that /api/openapi.json is available."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
