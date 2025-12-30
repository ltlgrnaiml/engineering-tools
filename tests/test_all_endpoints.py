"""
Comprehensive endpoint tests for all tools (DAT, SOV, PPTX)
Tests gateway routing, backend mounting, and API functionality
"""
import pytest

from fastapi.testclient import TestClient

from gateway.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a TestClient for the gateway app.

    These tests validate gateway routing/mounting deterministically without relying on
    an externally running server on localhost.
    """

    return TestClient(app)

class TestGatewayHealth:
    """Test gateway and tool availability"""
    
    def test_gateway_health(self, client: TestClient):
        """Test gateway health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "tools" in data
    
    def test_gateway_docs(self, client: TestClient):
        """Test gateway OpenAPI docs are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200


class TestPPTXEndpoints:
    """Test PowerPoint Generator endpoints"""
    
    def test_pptx_health(self, client: TestClient):
        """Test PPTX backend health via gateway"""
        response = client.get("/api/pptx/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pptx-generator"
    
    def test_pptx_docs(self, client: TestClient):
        """Test PPTX OpenAPI docs accessible via gateway"""
        response = client.get("/api/pptx/docs")
        assert response.status_code == 200
    
    def test_pptx_list_projects(self, client: TestClient):
        """Test listing PPTX projects"""
        response = client.get("/api/pptx/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_pptx_create_project(self, client: TestClient):
        """Test creating a PPTX project"""
        payload = {
            "name": "Test Project",
            "description": "Automated test project"
        }
        response = client.post("/api/pptx/projects", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["name"] == "Test Project"
        return data["project_id"]


class TestDATEndpoints:
    """Test Data Aggregator endpoints"""
    
    def test_dat_health(self, client: TestClient):
        """Test DAT backend health via gateway"""
        response = client.get("/api/dat/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "data-aggregator"
    
    def test_dat_docs(self, client: TestClient):
        """Test DAT OpenAPI docs accessible via gateway"""
        response = client.get("/api/dat/docs")
        assert response.status_code == 200
    
    def test_dat_list_runs(self, client: TestClient):
        """Test listing DAT runs"""
        response = client.get("/api/dat/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dat_create_run(self, client: TestClient):
        """Test creating a DAT run"""
        response = client.post("/api/dat/runs")
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "current_stage" in data
        return data["run_id"]


class TestSOVEndpoints:
    """Test SOV Analyzer endpoints"""
    
    def test_sov_health(self, client: TestClient):
        """Test SOV backend health via gateway"""
        response = client.get("/api/sov/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sov-analyzer"
    
    def test_sov_docs(self, client: TestClient):
        """Test SOV OpenAPI docs accessible via gateway"""
        response = client.get("/api/sov/docs")
        assert response.status_code == 200
    
    def test_sov_list_analyses(self, client: TestClient):
        """Test listing SOV analyses"""
        response = client.get("/api/sov/analyses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCrossToolIntegration:
    """Test cross-tool features via gateway"""
    
    def test_list_datasets(self, client: TestClient):
        """Test listing datasets from all tools"""
        response = client.get("/api/datasets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_datasets_by_tool(self, client: TestClient):
        """Test filtering datasets by tool"""
        for tool in ["dat", "sov", "pptx"]:
            response = client.get("/api/datasets", params={"tool": tool})
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    def test_list_pipelines(self, client: TestClient):
        """Test listing pipelines"""
        response = client.get("/api/pipelines")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_tool_path(self, client: TestClient):
        """Test accessing non-existent tool"""
        response = client.get("/api/invalid/health")
        assert response.status_code == 404
    
    def test_invalid_project_id(self, client: TestClient):
        """Test accessing non-existent PPTX project"""
        response = client.get("/api/pptx/projects/nonexistent-id")
        assert response.status_code == 404
    
    def test_invalid_run_id(self, client: TestClient):
        """Test accessing non-existent DAT run"""
        response = client.get("/api/dat/runs/nonexistent-id")
        assert response.status_code == 404


if __name__ == "__main__":
    print("Running comprehensive endpoint tests...")
    print("Make sure the gateway is running: ./start.ps1")
    print()
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
