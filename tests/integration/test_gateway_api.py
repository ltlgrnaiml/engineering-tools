"""Integration tests for Gateway API."""
import pytest
from httpx import AsyncClient, ASGITransport

from gateway.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint returns 200."""
    response = await client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


@pytest.mark.anyio
async def test_openapi_docs(client: AsyncClient):
    """Test OpenAPI docs are available."""
    response = await client.get("/docs")
    
    # Docs endpoint redirects or returns HTML
    assert response.status_code in [200, 307]


@pytest.mark.anyio
async def test_datasets_list_empty(client: AsyncClient):
    """Test listing datasets when none exist."""
    response = await client.get("/api/datasets")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_pipelines_list_empty(client: AsyncClient):
    """Test listing pipelines when none exist."""
    response = await client.get("/api/pipelines")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_create_pipeline(client: AsyncClient):
    """Test creating a new pipeline."""
    pipeline_data = {
        "name": "Test Pipeline",
        "description": "Integration test pipeline",
        "steps": [
            {
                "step_index": 0,
                "step_type": "dat:aggregate",
                "config": {"source_files": ["test.csv"]},
            }
        ],
    }
    
    response = await client.post("/api/pipelines", json=pipeline_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_id" in data
    assert data["name"] == "Test Pipeline"


@pytest.mark.anyio
async def test_get_nonexistent_dataset(client: AsyncClient):
    """Test getting a dataset that doesn't exist."""
    response = await client.get("/api/datasets/nonexistent123")
    
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_nonexistent_pipeline(client: AsyncClient):
    """Test getting a pipeline that doesn't exist."""
    response = await client.get("/api/pipelines/nonexistent123")
    
    assert response.status_code == 404
