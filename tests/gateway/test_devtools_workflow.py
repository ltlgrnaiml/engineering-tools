"""Tests for DevTools Workflow Manager endpoints."""

import pytest
from fastapi.testclient import TestClient

from gateway.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""

    return TestClient(app)


def test_artifacts_list__get(client: TestClient) -> None:
    """GET /api/devtools/artifacts should return a list response."""

    response = client.get("/api/devtools/artifacts")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    assert "items" in payload
    assert "total" in payload
    assert isinstance(payload["items"], list)
    assert isinstance(payload["total"], int)


def test_artifacts_graph__get(client: TestClient) -> None:
    """GET /api/devtools/artifacts/graph should return nodes and edges."""

    response = client.get("/api/devtools/artifacts/graph")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    assert "nodes" in payload
    assert "edges" in payload
    assert isinstance(payload["nodes"], list)
    assert isinstance(payload["edges"], list)


def test_artifacts_crud__post_put_delete_roundtrip(client: TestClient) -> None:
    """CRUD should create/update/delete an artifact under .plans/."""

    file_path = ".plans/.tests/PLAN-999_TEST.json"

    create_resp = client.post(
        "/api/devtools/artifacts",
        json={
            "type": "plan",
            "file_path": file_path,
            "format": "json",
            "content": "{\n  \"id\": \"PLAN-999\",\n  \"title\": \"Test Plan\"\n}\n",
            "create_backup": True,
        },
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["success"] is True
    assert created["file_path"] == file_path
    assert created["artifact"] is not None

    update_resp = client.put(
        "/api/devtools/artifacts",
        json={
            "type": "plan",
            "file_path": file_path,
            "format": "json",
            "content": "{\n  \"id\": \"PLAN-999\",\n  \"title\": \"Test Plan Updated\"\n}\n",
            "create_backup": True,
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["success"] is True
    assert updated["backup_path"] is not None

    delete_resp = client.request(
        "DELETE",
        "/api/devtools/artifacts",
        json={"file_path": file_path, "permanent": False},
    )
    assert delete_resp.status_code == 200
    deleted = delete_resp.json()
    assert deleted["success"] is True
    assert deleted["backup_path"] is not None
