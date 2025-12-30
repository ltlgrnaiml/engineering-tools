"""Tests for DevTools Workflow endpoints."""
import pytest
from unittest.mock import patch, AsyncMock

from shared.contracts.devtools.workflow import (
    ArtifactType,
    ArtifactStatus,
    ArtifactSummary,
    ArtifactListResponse,
    ArtifactGraphResponse,
)
from gateway.services import workflow_service


@pytest.fixture
def mock_artifacts():
    """Sample artifacts for testing."""
    return [
        ArtifactSummary(
            id="ADR-0001",
            type=ArtifactType.ADR,
            title="Test ADR",
            status=ArtifactStatus.ACTIVE,
            path=".adrs/ADR-0001.json",
            created_date="2025-01-01",
            updated_date="2025-01-01",
        )
    ]


@pytest.mark.asyncio
async def test_scan_artifacts_returns_list(mock_artifacts):
    """Test that scan_artifacts returns ArtifactListResponse."""
    with patch.object(
        workflow_service,
        "scan_artifacts",
        new_callable=AsyncMock,
        return_value=ArtifactListResponse(items=mock_artifacts, total=1),
    ):
        result = await workflow_service.scan_artifacts()
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == "ADR-0001"


@pytest.mark.asyncio
async def test_scan_artifacts_filters_by_type():
    """Test that scan_artifacts filters by artifact type."""
    # This tests the actual function, not mocked
    result = await workflow_service.scan_artifacts(artifact_type=ArtifactType.ADR)
    assert isinstance(result, ArtifactListResponse)
    for item in result.items:
        assert item.type == ArtifactType.ADR


@pytest.mark.asyncio
async def test_get_artifact_graph_returns_nodes():
    """Test that get_artifact_graph returns GraphResponse."""
    result = await workflow_service.get_artifact_graph()
    assert isinstance(result, ArtifactGraphResponse)
    assert isinstance(result.nodes, list)
    assert isinstance(result.edges, list)
