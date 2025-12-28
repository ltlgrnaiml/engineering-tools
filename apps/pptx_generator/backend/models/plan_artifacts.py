"""Plan Artifacts models.

Models for frozen plan artifacts (lookup, request_graph, manifest).
"""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LookupJSON(BaseModel):
    """TOM-style lookup JSON structure.

    Attributes:
        fs_root: Filesystem root path.
        fs_dataagg: Data aggregation root path.
        job_context_folders: Per-context-value folder paths.
    """

    fs_root: str = Field(..., description="Filesystem root")
    fs_dataagg: str = Field(..., description="Data aggregation root")
    job_context_folders: dict[str, str] = Field(..., description="Folders per job context value")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fs_root": "L:/Y72U/29/XDEC Monster",
            "fs_dataagg": "L:/Y72U/29/XDEC Monster/WLREV 2.2 XDEC EB",
            "job_context_folders": {
                "Left": "L:/Y72U/29/XDEC Monster/WLREV 2.2 XDEC EB/Left",
                "Right": "L:/Y72U/29/XDEC Monster/WLREV 2.2 XDEC EB/Right",
            },
        }
    })


class RequestGraphPartition(BaseModel):
    """A partition in the request graph.

    Attributes:
        run_key: Run identifier.
        job_context_value: Value of job context dimension.
        file_paths: List of file paths for this partition.
        deduped: Whether this partition was deduplicated.
    """

    run_key: str = Field(..., description="Run identifier")
    job_context_value: str = Field(..., description="Job context value")
    file_paths: list[str] = Field(default_factory=list, description="File paths")
    deduped: bool = Field(default=False, description="Deduplicated flag")

    def get_partition_key(self) -> tuple:
        """Get unique key for this partition.

        Returns:
            Tuple of (run_key, job_context_value).
        """
        return (self.run_key, self.job_context_value)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "run_key": "DZ001",
            "job_context_value": "Left",
            "file_paths": [
                "L:/path/to/data/Left/stats.csv",
                "L:/path/to/data/Left/conditions.csv",
            ],
            "deduped": False,
        }
    })


class RequestGraph(BaseModel):
    """Complete request graph with deduped partitions.

    Attributes:
        partitions: List of request graph partitions.
        total_partitions: Total number of partitions.
        deduped_count: Number of deduplicated partitions.
    """

    partitions: list[RequestGraphPartition] = Field(
        default_factory=list, description="Request partitions"
    )
    total_partitions: int = Field(default=0, description="Total partitions")
    deduped_count: int = Field(default=0, description="Deduplicated count")

    def add_partition(self, partition: RequestGraphPartition) -> None:
        """Add a partition to the graph.

        Args:
            partition: Partition to add.
        """
        self.partitions.append(partition)
        self.total_partitions = len(self.partitions)

    def deduplicate(self) -> None:
        """Deduplicate partitions by (run_key, job_context_value)."""
        seen_keys = set()
        deduped_partitions = []

        for partition in self.partitions:
            key = partition.get_partition_key()
            if key not in seen_keys:
                seen_keys.add(key)
                deduped_partitions.append(partition)
            else:
                partition.deduped = True
                self.deduped_count += 1

        self.partitions = deduped_partitions
        self.total_partitions = len(self.partitions)

    def sort_stable(self) -> None:
        """Sort partitions for deterministic ordering."""
        self.partitions.sort(key=lambda p: (p.run_key, p.job_context_value))

    def __str__(self) -> str:
        """Return a string representation of the request graph."""
        return str(self.partitions)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "partitions": [
                {
                    "run_key": "DZ001",
                    "job_context_value": "Left",
                    "file_paths": ["path/to/data.csv"],
                }
            ],
            "total_partitions": 1,
            "deduped_count": 0,
        }
    })


class PlanManifest(BaseModel):
    """Plan manifest with SHA1 hashes for determinism.

    Attributes:
        drm_sha1: SHA1 hash of DRM.
        mappings_sha1: SHA1 hash of mappings.
        environment_sha1: SHA1 hash of environment profile.
        lookup_sha1: SHA1 hash of lookup JSON.
        request_graph_sha1: SHA1 hash of request graph.
        code_version: Version of code used to build plan.
        frozen_at: Timestamp when plan was frozen.
    """

    drm_sha1: str = Field(..., description="DRM SHA1 hash")
    mappings_sha1: str = Field(..., description="Mappings SHA1 hash")
    environment_sha1: str = Field(..., description="Environment SHA1 hash")
    lookup_sha1: str = Field(..., description="Lookup SHA1 hash")
    request_graph_sha1: str = Field(..., description="Request graph SHA1 hash")
    code_version: str = Field(..., description="Code version")
    frozen_at: datetime = Field(default_factory=datetime.utcnow, description="Freeze timestamp")

    @staticmethod
    def calculate_sha1(obj: Any) -> str:
        """Calculate SHA1 hash of an object.

        Args:
            obj: Object to hash (will be JSON serialized).

        Returns:
            SHA1 hash as hex string.
        """
        if isinstance(obj, BaseModel):
            # Convert to dict first, then handle datetime objects
            obj_dict = obj.model_dump()

            # Convert datetime and UUID objects to strings for JSON serialization
            def convert_objects(data):
                if isinstance(data, dict):
                    return {k: convert_objects(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [convert_objects(item) for item in data]
                elif isinstance(data, datetime | UUID):
                    return str(data)
                else:
                    return data

            obj_dict = convert_objects(obj_dict)
            json_str = json.dumps(obj_dict, sort_keys=True)
        else:
            json_str = json.dumps(obj, sort_keys=True, default=str)
        return hashlib.sha1(json_str.encode()).hexdigest()

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "drm_sha1": "a1b2c3d4e5f6...",
            "mappings_sha1": "f6e5d4c3b2a1...",
            "environment_sha1": "1a2b3c4d5e6f...",
            "lookup_sha1": "6f5e4d3c2b1a...",
            "request_graph_sha1": "b1c2d3e4f5a6...",
            "code_version": "2.0.0",
        }
    })


class PlanArtifacts(BaseModel):
    """Complete set of plan artifacts.

    Attributes:
        id: Unique identifier.
        project_id: Associated project ID.
        lookup: Lookup JSON.
        request_graph: Request graph.
        manifest: Plan manifest with hashes.
        created_at: Creation timestamp.
    """

    id: UUID = Field(default_factory=uuid4, description="Plan artifacts ID")
    project_id: UUID = Field(..., description="Associated project ID")
    lookup: LookupJSON = Field(..., description="Lookup JSON")
    request_graph: RequestGraph = Field(..., description="Request graph")
    manifest: PlanManifest = Field(..., description="Plan manifest")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "lookup": {
                "fs_root": "/path",
                "fs_dataagg": "/path/data",
                "job_context_folders": {},
            },
            "request_graph": {"partitions": [], "total_partitions": 0, "deduped_count": 0},
            "manifest": {
                "drm_sha1": "abc123",
                "mappings_sha1": "def456",
                "environment_sha1": "ghi789",
                "lookup_sha1": "jkl012",
                "request_graph_sha1": "mno345",
                "code_version": "2.0.0",
            },
        }
    })


# Validation test
if __name__ == "__main__":
    from uuid import uuid4

    # Test LookupJSON
    lookup = LookupJSON(
        fs_root="/root",
        fs_dataagg="/root/data",
        job_context_folders={"Left": "/root/data/Left", "Right": "/root/data/Right"},
    )
    assert lookup.fs_root == "/root"

    # Test RequestGraphPartition
    partition = RequestGraphPartition(
        run_key="DZ001", job_context_value="Left", file_paths=["file1.csv"]
    )
    assert partition.get_partition_key() == ("DZ001", "Left")

    # Test RequestGraph
    graph = RequestGraph()
    graph.add_partition(partition)
    graph.add_partition(
        RequestGraphPartition(run_key="DZ001", job_context_value="Left", file_paths=["file2.csv"])
    )
    assert graph.total_partitions == 2
    graph.deduplicate()
    assert graph.total_partitions == 1
    assert graph.deduped_count == 1

    # Test PlanManifest SHA1
    test_obj = {"key": "value"}
    sha1 = PlanManifest.calculate_sha1(test_obj)
    assert len(sha1) == 40  # SHA1 is 40 hex chars

    # Test PlanArtifacts
    manifest = PlanManifest(
        drm_sha1="abc",
        mappings_sha1="def",
        environment_sha1="ghi",
        lookup_sha1="jkl",
        request_graph_sha1="mno",
        code_version="2.0.0",
    )
    artifacts = PlanArtifacts(
        project_id=uuid4(), lookup=lookup, request_graph=graph, manifest=manifest
    )
    assert artifacts.lookup == lookup

    print("All plan artifacts tests passed!")
