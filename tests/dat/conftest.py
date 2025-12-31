"""Pytest configuration and fixtures for DAT tests."""
import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import polars as pl
import pytest

from apps.data_aggregator.backend.src.dat_aggregation.core.run_manager import RunManager
from apps.data_aggregator.backend.src.dat_aggregation.core.run_store import RunStore


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        (workspace / "tools" / "dat" / "runs").mkdir(parents=True)
        (workspace / "datasets").mkdir(parents=True)
        yield workspace


@pytest.fixture
def run_store(temp_workspace: Path) -> RunStore:
    """Create a RunStore with a temporary workspace."""
    return RunStore(workspace_path=temp_workspace)


@pytest.fixture
def run_manager(temp_workspace: Path) -> RunManager:
    """Create a RunManager with a temporary workspace."""
    return RunManager(workspace_path=temp_workspace)


@pytest.fixture
def sample_json_data() -> dict:
    """Create sample JSON data matching the CD-SEM schema."""
    return {
        "metadata": {
            "lot_id": "LOTTEST001",
            "wafer_id": "W01",
            "file_version": "2.1.0",
        },
        "run_info": {
            "recipe": {"name": "RCP_TEST", "version": "1.0"},
            "tool": {"tool_id": "CDSEM001", "tool_type": "Test Tool"},
            "operator": "OP001",
        },
        "summary": {
            "total_images": 10,
            "valid_images": 9,
            "mean_cd": 24.5,
            "sigma_cd": 0.8,
            "range_cd": 2.5,
        },
        "statistics": {
            "columns": ["parameter", "mean", "std_dev", "min", "max", "count"],
            "values": [
                ["CD_Average", 24.5, 0.8, 22.5, 26.5, 100],
                ["Height", 48.0, 1.2, 45.0, 51.0, 100],
            ]
        },
        "sites": [
            {
                "site_id": "SITE01",
                "x_position": 0.0,
                "y_position": 0.0,
                "cd_data": {
                    "headers": ["site_id", "x_position", "y_position", "cd_value"],
                    "rows": [["SITE01", 0.0, 0.0, 24.2]]
                }
            }
        ],
        "images": [
            {
                "image_id": "IMG_001",
                "image_name": "SITE01_LINE001",
                "metadata": {
                    "site_id": "SITE01",
                    "acquisition_time": "2025-12-27T08:00:00Z",
                },
                "measurements": {
                    "columns": ["image_id", "cd_left", "cd_right", "cd_average"],
                    "values": [["IMG_001", 24.1, 24.3, 24.2]]
                },
                "quality": {
                    "columns": ["image_id", "contrast", "sharpness"],
                    "values": [["IMG_001", 0.85, 92.5]]
                }
            }
        ],
        "diagnostics": {
            "beam_current": 8.5,
            "focus_score": 95.0,
        }
    }


@pytest.fixture
def sample_json_file(sample_json_data) -> Generator[Path, None, None]:
    """Create a temporary JSON file with sample data."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False,
        prefix="LOTTEST001_W01_CDSEM001_20251227_"
    ) as f:
        json.dump(sample_json_data, f)
        f.flush()
        yield Path(f.name)


@pytest.fixture
def sample_csv_file() -> Generator[Path, None, None]:
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,value,category\n")
        f.write("1,100,A\n")
        f.write("2,200,B\n")
        f.write("3,300,A\n")
        f.flush()
        yield Path(f.name)


@pytest.fixture
def sample_dataframe() -> pl.DataFrame:
    """Create a sample Polars DataFrame."""
    return pl.DataFrame({
        "wafer_id": ["W001", "W001", "W002", "W002"],
        "site_id": ["S1", "S2", "S1", "S2"],
        "cd_value": [24.1, 24.3, 24.5, 24.2],
        "height": [48.1, 48.3, 48.0, 48.5],
    })


@pytest.fixture
def profiles_dir() -> Path:
    """Get path to profiles directory."""
    return Path(__file__).parent.parent.parent / "apps" / "data_aggregator" / "backend" / "src" / "dat_aggregation" / "profiles"


@pytest.fixture
def examples_dir(profiles_dir) -> Path:
    """Get path to examples directory."""
    return profiles_dir / "examples"


@pytest.fixture
def cdsem_profile_path(profiles_dir) -> Path:
    """Get path to CD-SEM profile."""
    return profiles_dir / "cdsem_metrology_profile.yaml"


@pytest.fixture
def example_data_file(examples_dir) -> Path:
    """Get path to example data file."""
    return examples_dir / "LOTABC12345_W01_CDSEM001_20251227_measurement.json"
