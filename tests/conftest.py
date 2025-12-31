"""Pytest configuration and shared fixtures."""
import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio

from shared.storage.artifact_store import ArtifactStore
from shared.storage.registry_db import RegistryDB


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        yield workspace


@pytest.fixture
def artifact_store(temp_workspace: Path) -> ArtifactStore:
    """Create an ArtifactStore with a temporary workspace."""
    return ArtifactStore(workspace_path=temp_workspace)


@pytest_asyncio.fixture
async def registry_db(temp_workspace: Path) -> AsyncGenerator[RegistryDB, None]:
    """Create a RegistryDB with a temporary database."""
    db_path = temp_workspace / ".registry.db"
    registry = RegistryDB(db_path=db_path)
    await registry.initialize()
    yield registry
    await registry.close()


@pytest.fixture
def sample_dataframe():
    """Create a sample polars DataFrame for testing."""
    import polars as pl

    return pl.DataFrame({
        "wafer_id": ["W001", "W001", "W002", "W002"],
        "site": [1, 2, 1, 2],
        "measurement": [1.5, 1.6, 1.4, 1.7],
        "tool": ["A", "A", "B", "B"],
    })
