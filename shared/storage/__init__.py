"""Shared artifact storage - unified I/O for DataSets and artifacts.

This module provides:
- ArtifactStore: Read/write DataSets (Parquet + JSON manifest)
- RegistryDB: SQLite-backed artifact registry

Per ADR-0014: Data tables stored as Parquet, metadata as JSON.
Per ADR-0017#path-safety: All paths are relative to workspace/.
"""

__version__ = "0.1.0"

from shared.storage.artifact_store import ArtifactStore
from shared.storage.registry_db import RegistryDB

__all__ = ["ArtifactStore", "RegistryDB"]
