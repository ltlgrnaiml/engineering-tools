"""
Comprehensive endpoint tests for all tools (DAT, SOV, PPTX)
Tests gateway routing, backend mounting, and API functionality
"""
import pytest
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

class TestGatewayHealth:
    """Test gateway and tool availability"""
    
    def test_gateway_health(self):
        """Test gateway health endpoint"""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "tools" in data
    
    def test_gateway_docs(self):
        """Test gateway OpenAPI docs are accessible"""
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        assert response.status_code == 200


class TestPPTXEndpoints:
    """Test PowerPoint Generator endpoints"""
    
    def test_pptx_health(self):
        """Test PPTX backend health via gateway"""
        response = requests.get(f"{BASE_URL}/api/pptx/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pptx-generator"
    
    def test_pptx_docs(self):
        """Test PPTX OpenAPI docs accessible via gateway"""
        response = requests.get(f"{BASE_URL}/api/pptx/docs", timeout=TIMEOUT)
        assert response.status_code == 200
    
    def test_pptx_list_projects(self):
        """Test listing PPTX projects"""
        response = requests.get(f"{BASE_URL}/api/pptx/projects", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_pptx_create_project(self):
        """Test creating a PPTX project"""
        payload = {
            "name": "Test Project",
            "description": "Automated test project"
        }
        response = requests.post(
            f"{BASE_URL}/api/pptx/projects",
            json=payload,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["name"] == "Test Project"
        return data["project_id"]


class TestDATEndpoints:
    """Test Data Aggregator endpoints"""
    
    def test_dat_health(self):
        """Test DAT backend health via gateway"""
        response = requests.get(f"{BASE_URL}/api/dat/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "data-aggregator"
    
    def test_dat_docs(self):
        """Test DAT OpenAPI docs accessible via gateway"""
        response = requests.get(f"{BASE_URL}/api/dat/docs", timeout=TIMEOUT)
        assert response.status_code == 200
    
    def test_dat_list_runs(self):
        """Test listing DAT runs"""
        response = requests.get(f"{BASE_URL}/api/dat/runs", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dat_create_run(self):
        """Test creating a DAT run"""
        response = requests.post(
            f"{BASE_URL}/api/dat/runs",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "current_stage" in data
        return data["run_id"]


class TestSOVEndpoints:
    """Test SOV Analyzer endpoints"""
    
    def test_sov_health(self):
        """Test SOV backend health via gateway"""
        response = requests.get(f"{BASE_URL}/api/sov/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sov-analyzer"
    
    def test_sov_docs(self):
        """Test SOV OpenAPI docs accessible via gateway"""
        response = requests.get(f"{BASE_URL}/api/sov/docs", timeout=TIMEOUT)
        assert response.status_code == 200
    
    def test_sov_list_analyses(self):
        """Test listing SOV analyses"""
        response = requests.get(f"{BASE_URL}/api/sov/analyses", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCrossToolIntegration:
    """Test cross-tool features via gateway"""
    
    def test_list_datasets(self):
        """Test listing datasets from all tools"""
        response = requests.get(f"{BASE_URL}/api/datasets", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_datasets_by_tool(self):
        """Test filtering datasets by tool"""
        for tool in ["dat", "sov", "pptx"]:
            response = requests.get(
                f"{BASE_URL}/api/datasets",
                params={"tool": tool},
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    def test_list_pipelines(self):
        """Test listing pipelines"""
        response = requests.get(f"{BASE_URL}/api/pipelines", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_tool_path(self):
        """Test accessing non-existent tool"""
        response = requests.get(f"{BASE_URL}/api/invalid/health", timeout=TIMEOUT)
        assert response.status_code == 404
    
    def test_invalid_project_id(self):
        """Test accessing non-existent PPTX project"""
        response = requests.get(
            f"{BASE_URL}/api/pptx/projects/nonexistent-id",
            timeout=TIMEOUT
        )
        assert response.status_code == 404
    
    def test_invalid_run_id(self):
        """Test accessing non-existent DAT run"""
        response = requests.get(
            f"{BASE_URL}/api/dat/runs/nonexistent-id",
            timeout=TIMEOUT
        )
        assert response.status_code == 404


if __name__ == "__main__":
    print("Running comprehensive endpoint tests...")
    print("Make sure the gateway is running: ./start.ps1")
    print()
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
