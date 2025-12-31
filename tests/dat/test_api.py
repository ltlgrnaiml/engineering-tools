"""Tests for DAT API routes."""
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.data_aggregator.backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace" / "tools" / "dat"
        workspace.mkdir(parents=True)
        yield Path(tmpdir) / "workspace"


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["tool"] == "dat"


class TestRunEndpoints:
    """Test run management endpoints."""

    def test_create_run(self, client):
        """Test creating a new run."""
        response = client.post(
            "/runs",
            json={"name": "Test Run"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["name"] == "Test Run"
        assert "created_at" in data

    def test_create_run_with_profile(self, client):
        """Test creating a run with profile ID."""
        response = client.post(
            "/runs",
            json={"name": "Test Run", "profile_id": "cdsem-metrology-v1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == "cdsem-metrology-v1"

    def test_create_run_without_name(self, client):
        """Test creating a run without name uses default."""
        response = client.post("/runs", json={})

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        # Should have auto-generated name
        assert data["name"] is not None

    def test_list_runs(self, client):
        """Test listing runs."""
        # Create a couple runs first
        client.post("/runs", json={"name": "Run 1"})
        client.post("/runs", json={"name": "Run 2"})

        response = client.get("/runs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_run(self, client):
        """Test getting a specific run."""
        # Create run first
        create_response = client.post("/runs", json={"name": "Test Run"})
        run_id = create_response.json()["run_id"]

        response = client.get(f"/runs/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["name"] == "Test Run"
        assert "stages" in data

    def test_get_nonexistent_run(self, client):
        """Test getting a nonexistent run returns 404."""
        response = client.get("/runs/nonexistent-run-id")

        assert response.status_code == 404


class TestStageEndpoints:
    """Test stage management endpoints."""

    @pytest.fixture
    def run_id(self, client):
        """Create a run and return its ID."""
        response = client.post("/runs", json={"name": "Test Run"})
        return response.json()["run_id"]

    def test_get_stage_status(self, client, run_id):
        """Test getting stage status."""
        response = client.get(f"/runs/{run_id}/stages/selection")

        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "selection"
        assert data["state"] == "unlocked"

    def test_get_invalid_stage(self, client, run_id):
        """Test getting invalid stage returns 400."""
        response = client.get(f"/runs/{run_id}/stages/invalid_stage")

        assert response.status_code == 400

    def test_unlock_stage(self, client, run_id):
        """Test unlocking a stage."""
        response = client.post(f"/runs/{run_id}/stages/selection/unlock")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unlocked"

    def test_unlock_invalid_stage(self, client, run_id):
        """Test unlocking invalid stage returns 400."""
        response = client.post(f"/runs/{run_id}/stages/invalid_stage/unlock")

        assert response.status_code == 400


class TestSelectionEndpoint:
    """Test selection stage endpoint."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create JSON file
            json_file = tmpdir / "test_data.json"
            json.dump([{"id": 1, "value": 100}], open(json_file, "w"))

            # Create CSV file
            csv_file = tmpdir / "test_data.csv"
            csv_file.write_text("id,value\n1,100\n2,200")

            yield tmpdir

    @pytest.fixture
    def run_with_discovery(self, client, temp_files):
        """Create run and lock discovery stage first (required before selection)."""
        # Create run
        response = client.post("/runs", json={"name": "Test Run"})
        run_id = response.json()["run_id"]

        # Lock discovery first (per ADR-0004 stage dependencies)
        client.post(
            f"/runs/{run_id}/stages/discovery/lock",
            json={"folder_path": str(temp_files), "recursive": True}
        )

        return run_id

    def test_lock_selection_with_directory(self, client, run_with_discovery, temp_files):
        """Test locking selection stage with directory path."""
        run_id = run_with_discovery
        json_file = temp_files / "test_data.json"
        csv_file = temp_files / "test_data.csv"

        response = client.post(
            f"/runs/{run_id}/stages/selection/lock",
            json={
                "source_paths": [str(temp_files)],
                "selected_files": [str(json_file), str(csv_file)],
                "recursive": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "discovered_files" in data
        assert "selected_files" in data

    def test_lock_selection_with_specific_file(self, client, run_with_discovery, temp_files):
        """Test locking selection with specific file."""
        run_id = run_with_discovery
        json_file = temp_files / "test_data.json"

        response = client.post(
            f"/runs/{run_id}/stages/selection/lock",
            json={
                "selected_files": [str(json_file)],
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Discovery found all files in the directory, selection filters to just the one we chose
        assert len(data["selected_files"]) == 1
        # Check the selected file is in discovered files
        json_files = [f for f in data["discovered_files"] if f["extension"] == ".json"]
        assert len(json_files) >= 1


class TestTableSelectionEndpoint:
    """Test table selection stage endpoint."""

    @pytest.fixture
    def run_with_selection(self, client):
        """Create run with selection stage locked."""
        # Create run
        run_response = client.post("/runs", json={"name": "Test Run"})
        run_id = run_response.json()["run_id"]

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}], f)
            f.flush()

            # Lock selection
            client.post(
                f"/runs/{run_id}/stages/selection/lock",
                json={"source_paths": [f.name]}
            )

        return run_id

    def test_lock_table_selection_requires_table_availability(self, client, run_with_selection):
        """Test that table selection requires table_availability to be locked first."""
        run_id = run_with_selection

        # Try to lock table_selection without table_availability locked
        response = client.post(
            f"/runs/{run_id}/stages/table_selection/lock",
            json={
                "selected_tables": {"file1.json": ["table1", "table2"]}
            }
        )

        # Should fail because table_availability is not locked
        assert response.status_code == 400
        assert "table_availability" in response.json()["detail"].lower()


class TestPreviewEndpoint:
    """Test preview endpoint."""

    def test_preview_without_table_selection(self, client):
        """Test preview fails without table selection stage locked."""
        # Create run
        run_response = client.post("/runs", json={"name": "Test Run"})
        run_id = run_response.json()["run_id"]

        # Preview endpoint requires table_selection to be locked first
        response = client.get(f"/runs/{run_id}/stages/preview/data")

        # Should fail because table_selection is not locked
        assert response.status_code == 400


class TestAPISchemas:
    """Test API request/response schemas."""

    def test_create_run_request_validation(self, client):
        """Test that invalid create run request is handled."""
        # Empty request should work (all fields optional)
        response = client.post("/runs", json={})
        assert response.status_code == 200

    def test_selection_request_requires_source_paths(self, client):
        """Test selection request requires source_paths."""
        run_response = client.post("/runs", json={})
        run_id = run_response.json()["run_id"]

        # Missing source_paths should fail validation
        response = client.post(
            f"/runs/{run_id}/stages/selection/lock",
            json={}
        )

        assert response.status_code == 422  # Validation error
