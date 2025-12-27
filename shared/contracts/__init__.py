"""Tier 0: Pydantic contracts - single source of truth for all data structures.

Per ADR-0009, contracts defined here are:
- The canonical schema for all API payloads
- Auto-exported to JSON Schema via tools/codegen/gen_json_schema.py
- Used to generate OpenAPI specs via tools/codegen/gen_openapi.py
- Never duplicated in ADRs, Specs, or Guides (reference only)
"""

from shared.contracts.core.dataset import (
    ColumnMeta,
    DataSetManifest,
    DataSetRef,
)
from shared.contracts.core.pipeline import (
    Pipeline,
    PipelineStep,
    PipelineStepState,
    PipelineStepType,
)
from shared.contracts.core.artifact_registry import ArtifactRecord, ArtifactType

__all__ = [
    # Dataset
    "ColumnMeta",
    "DataSetManifest",
    "DataSetRef",
    # Pipeline
    "Pipeline",
    "PipelineStep",
    "PipelineStepState",
    "PipelineStepType",
    # Registry
    "ArtifactRecord",
    "ArtifactType",
]
