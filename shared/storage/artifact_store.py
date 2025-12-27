"""ArtifactStore - unified I/O for DataSets and artifacts.

Provides read/write operations for:
- DataSets (Parquet data + JSON manifest)
- Pipeline definitions
- Other artifacts

Per ADR-0014: Uses Parquet for data, JSON for metadata.
Per ADR-0017#path-safety: All external paths are relative.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from pydantic import BaseModel

from shared.contracts.core.dataset import DataSetManifest, DataSetRef
from shared.contracts.core.artifact_registry import ArtifactRecord, ArtifactType

if TYPE_CHECKING:
    pass

__version__ = "0.1.0"


def get_workspace_path() -> Path:
    """Get the workspace directory path.
    
    Defaults to ./workspace relative to the repo root.
    Can be overridden via ENGINEERING_TOOLS_WORKSPACE env var.
    """
    import os
    
    workspace = os.environ.get("ENGINEERING_TOOLS_WORKSPACE")
    if workspace:
        return Path(workspace)
    
    # Default: workspace/ in repo root
    # Find repo root by looking for pyproject.toml
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current / "workspace"
        current = current.parent
    
    # Fallback to cwd/workspace
    return Path.cwd() / "workspace"


class ArtifactStore:
    """Unified artifact storage for all tools.
    
    Directory structure:
        workspace/
        ├── datasets/{dataset_id}/
        │   ├── data.parquet
        │   └── manifest.json
        ├── pipelines/{pipeline_id}/
        │   ├── pipeline.json
        │   └── steps/
        └── tools/{tool}/runs/{run_id}/
    """
    
    def __init__(self, workspace_path: Path | None = None) -> None:
        self.workspace = workspace_path or get_workspace_path()
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (self.workspace / "datasets").mkdir(exist_ok=True)
        (self.workspace / "pipelines").mkdir(exist_ok=True)
    
    # === DataSet Operations ===
    
    async def write_dataset(
        self,
        dataset_id: str,
        data: pl.DataFrame,
        manifest: DataSetManifest,
    ) -> Path:
        """Write a DataSet to storage.
        
        Args:
            dataset_id: Unique identifier for the dataset
            data: Polars DataFrame to store
            manifest: DataSet manifest with schema and provenance
            
        Returns:
            Relative path to the dataset directory
        """
        dataset_dir = self.workspace / "datasets" / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Write Parquet data
        data_path = dataset_dir / "data.parquet"
        data.write_parquet(data_path)
        
        # Update manifest with size
        manifest_dict = manifest.model_dump(mode="json")
        manifest_dict["size_bytes"] = data_path.stat().st_size
        
        # Write manifest JSON
        manifest_path = dataset_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_dict, f, indent=2, default=str)
        
        return Path("datasets") / dataset_id
    
    async def read_dataset(self, dataset_id: str) -> pl.DataFrame:
        """Read a DataSet's data from storage."""
        data_path = self.workspace / "datasets" / dataset_id / "data.parquet"
        if not data_path.exists():
            raise FileNotFoundError(f"DataSet not found: {dataset_id}")
        return pl.read_parquet(data_path)
    
    async def get_manifest(self, dataset_id: str) -> DataSetManifest:
        """Get a DataSet's manifest."""
        manifest_path = self.workspace / "datasets" / dataset_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"DataSet manifest not found: {dataset_id}")
        
        with open(manifest_path) as f:
            data = json.load(f)
        return DataSetManifest.model_validate(data)
    
    async def list_datasets(
        self,
        tool: str | None = None,
        limit: int = 50,
    ) -> list[DataSetRef]:
        """List available DataSets."""
        datasets_dir = self.workspace / "datasets"
        if not datasets_dir.exists():
            return []
        
        refs: list[DataSetRef] = []
        for ds_dir in datasets_dir.iterdir():
            if not ds_dir.is_dir():
                continue
            
            manifest_path = ds_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            
            try:
                with open(manifest_path) as f:
                    data = json.load(f)
                
                # Filter by tool if specified
                if tool and data.get("created_by_tool") != tool:
                    continue
                
                refs.append(DataSetRef(
                    dataset_id=data["dataset_id"],
                    name=data["name"],
                    created_at=data["created_at"],
                    created_by_tool=data["created_by_tool"],
                    row_count=data["row_count"],
                    column_count=len(data["columns"]),
                    parent_count=len(data.get("parent_dataset_ids", [])),
                    size_bytes=data.get("size_bytes"),
                ))
            except (json.JSONDecodeError, KeyError):
                continue
            
            if len(refs) >= limit:
                break
        
        return refs
    
    async def dataset_exists(self, dataset_id: str) -> bool:
        """Check if a DataSet exists."""
        manifest_path = self.workspace / "datasets" / dataset_id / "manifest.json"
        return manifest_path.exists()
    
    # === Utility Methods ===
    
    def get_relative_path(self, absolute_path: Path) -> str:
        """Convert absolute path to workspace-relative path.
        
        Per ADR-0017#path-safety: All public paths must be relative.
        """
        try:
            return str(absolute_path.relative_to(self.workspace))
        except ValueError:
            raise ValueError(
                f"Path {absolute_path} is not within workspace {self.workspace}"
            )
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert workspace-relative path to absolute path."""
        return self.workspace / relative_path
