"""Pydantic models for request/response validation."""

# Existing models
from apps.pptx_generator.backend.models.data import AssetMapping, DataFile, DataMapping

# TOM v2 models
from apps.pptx_generator.backend.models.drm import (
    AggregationType,
    DataLevelCardinality,
    DerivedRequirementsManifest,
    MappingSourceType,
    RequiredContext,
    RequiredDataLevel,
    RequiredMetric,
    RequiredRenderer,
)
from apps.pptx_generator.backend.models.environment_profile import (
    DataRoots,
    EnvironmentProfile,
    JobContext,
    SourceType,
)
from apps.pptx_generator.backend.models.generation import GenerationRequest, GenerationResponse, GenerationStatus
from apps.pptx_generator.backend.models.mapping_manifest import (
    ContextMapping,
    CoverageReport,
    MappingManifest,
    MappingSuggestion,
    MetricMapping,
)
from apps.pptx_generator.backend.models.plan_artifacts import (
    LookupJSON,
    PlanArtifacts,
    PlanManifest,
    RequestGraph,
    RequestGraphPartition,
)
from apps.pptx_generator.backend.models.project import Project, ProjectCreate, ProjectStatus
from apps.pptx_generator.backend.models.template import ShapeInfo, ShapeMap, Template
from apps.pptx_generator.backend.models.validation_report import (
    BarStatus,
    FourBarsStatus,
    ValidationStatus,
    ValidationWarning,
)

__all__ = [
    # Existing
    "Project",
    "ProjectCreate",
    "ProjectStatus",
    "Template",
    "ShapeInfo",
    "ShapeMap",
    "DataFile",
    "DataMapping",
    "AssetMapping",
    "GenerationRequest",
    "GenerationResponse",
    "GenerationStatus",
    # TOM v2 - DRM
    "DerivedRequirementsManifest",
    "RequiredContext",
    "RequiredMetric",
    "RequiredDataLevel",
    "RequiredRenderer",
    "MappingSourceType",
    "AggregationType",
    "DataLevelCardinality",
    # TOM v2 - Mappings
    "MappingManifest",
    "ContextMapping",
    "MetricMapping",
    "MappingSuggestion",
    "CoverageReport",
    # TOM v2 - Environment
    "EnvironmentProfile",
    "JobContext",
    "DataRoots",
    "SourceType",
    # TOM v2 - Validation
    "FourBarsStatus",
    "BarStatus",
    "ValidationStatus",
    "ValidationWarning",
    # TOM v2 - Plan
    "PlanArtifacts",
    "PlanManifest",
    "LookupJSON",
    "RequestGraph",
    "RequestGraphPartition",
]
