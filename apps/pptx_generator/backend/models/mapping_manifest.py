"""Mapping Manifest models.

Models for context and metrics mappings that connect DRM requirements to actual data.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.pptx_generator.backend.models.drm import AggregationType, MappingSourceType


class ValueAlias(BaseModel):
    """Alias configuration for normalizing context values.

    Example: 'L', 'l', 'left' -> 'Left'
    """

    source_values: list[str] = Field(..., description="Values to match")
    target_value: str = Field(..., description="Normalized target value")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "source_values": ["L", "l", "left"],
            "target_value": "Left",
        }
    })


class DerivedColumn(BaseModel):
    """Configuration for creating derived columns.

    Supports regex extraction, expressions, and lookups.
    """

    name: str = Field(..., description="New column name")
    source_column: str = Field(..., description="Source column to derive from")
    derivation_type: str = Field(..., description="Type: regex, expression, lookup")
    pattern: str | None = Field(None, description="Regex pattern with named groups")
    expression: str | None = Field(None, description="Python expression")
    lookup_table: dict[str, str] | None = Field(None, description="Value lookup table")
    description: str | None = Field(None, description="Human-readable description")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "imcol",
            "source_column": "ImageName",
            "derivation_type": "regex",
            "pattern": "LC(?P<imcol>\\d+)_",
            "description": "Extract image column from ImageName",
        }
    })


class DataJoin(BaseModel):
    """Configuration for joining multiple data files."""

    secondary_file_id: UUID = Field(..., description="ID of file to join")
    join_type: str = Field(default="left", description="Join type: left, right, inner, outer")
    primary_column: str = Field(..., description="Column from primary file")
    secondary_column: str = Field(..., description="Column from secondary file")
    columns_to_include: list[str] = Field(
        default_factory=list, description="Columns to include from secondary"
    )
    suffix: str = Field(default="_joined", description="Suffix for duplicate columns")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "secondary_file_id": "123e4567-e89b-12d3-a456-426614174002",
            "join_type": "left",
            "primary_column": "Condition",
            "secondary_column": "ConditionID",
            "columns_to_include": ["Value", "Category"],
        }
    })


class ContextMapping(BaseModel):
    """Mapping configuration for a context dimension.

    Attributes:
        context_name: Name of the context (e.g., 'side', 'wafer').
        source_type: How the context is derived.
        source_column: Column name if source_type is COLUMN.
        regex_pattern: Regex pattern if source_type is REGEX.
        default_value: Default value if source_type is DEFAULT.
        description: Human-readable description.
    """

    context_name: str = Field(..., description="Context dimension name")
    source_type: MappingSourceType = Field(..., description="Mapping source type")
    source_column: str | None = Field(None, description="Source column name")
    regex_pattern: str | None = Field(None, description="Regex extraction pattern")
    default_value: str | None = Field(None, description="Default value")
    description: str | None = Field(None, description="Human-readable description")

    @field_validator("source_column")
    @classmethod
    def validate_source_column(cls, v, info):
        """Validate source_column is provided when source_type is COLUMN."""
        if info.data.get("source_type") == MappingSourceType.COLUMN and not v:
            raise ValueError("source_column required when source_type is COLUMN")
        return v

    @field_validator("regex_pattern")
    @classmethod
    def validate_regex_pattern(cls, v, info):
        """Validate regex_pattern is provided when source_type is REGEX."""
        if info.data.get("source_type") == MappingSourceType.REGEX and not v:
            raise ValueError("regex_pattern required when source_type is REGEX")
        return v

    @field_validator("default_value")
    @classmethod
    def validate_default_value(cls, v, info):
        """Validate default_value is provided when source_type is DEFAULT."""
        if info.data.get("source_type") == MappingSourceType.DEFAULT and not v:
            raise ValueError("default_value required when source_type is DEFAULT")
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "context_name": "side",
            "source_type": "column",
            "source_column": "SpaceCD_Side",
            "description": "Side dimension from SpaceCD_Side column",
        }
    })


class MetricMapping(BaseModel):
    """Mapping configuration for a metric.

    Attributes:
        metric_name: Name of the metric (e.g., 'CD', 'LWR').
        source_column: Source column in data file.
        rename_to: Target metric name (may differ from source).
        aggregation_semantics: How to aggregate this metric.
        data_type: Expected data type.
        unit: Measurement unit.
        description: Human-readable description.
    """

    metric_name: str = Field(..., description="Metric name from DRM")
    source_column: str = Field(..., description="Source column in data")
    rename_to: str | None = Field(None, description="Target metric name")
    aggregation_semantics: AggregationType = Field(..., description="Aggregation method")
    data_type: str = Field(default="float", description="Data type")
    unit: str | None = Field(None, description="Measurement unit")
    description: str | None = Field(None, description="Human-readable description")

    def get_target_name(self) -> str:
        """Get the target metric name (rename_to if set, else metric_name).

        Returns:
            Target metric name.
        """
        return self.rename_to if self.rename_to else self.metric_name

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "metric_name": "CD",
            "source_column": "Space CD (nm)",
            "rename_to": "SpaceCD",
            "aggregation_semantics": "mean",
            "unit": "nm",
        }
    })


class MappingSuggestion(BaseModel):
    """Auto-suggested mapping with confidence score.

    Attributes:
        target_name: Name of the context/metric being mapped.
        suggested_source: Suggested source column or pattern.
        source_type: Suggested mapping type.
        confidence_score: Confidence in suggestion (0.0-1.0).
        reasoning: Explanation of why this was suggested.
    """

    target_name: str = Field(..., description="Target context/metric name")
    suggested_source: str = Field(..., description="Suggested source")
    source_type: MappingSourceType = Field(..., description="Suggested mapping type")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Why this was suggested")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "target_name": "side",
            "suggested_source": "SpaceCD_Side",
            "source_type": "column",
            "confidence_score": 0.9,
            "reasoning": "Substring match: 'side' found in 'SpaceCD_Side'",
        }
    })


class CoverageReport(BaseModel):
    """Report on mapping coverage.

    Attributes:
        total_required: Total number of required items.
        mapped_count: Number of items mapped.
        coverage_percentage: Percentage of items mapped.
        missing_items: List of items not yet mapped.
    """

    total_required: int = Field(..., ge=0, description="Total required items")
    mapped_count: int = Field(..., ge=0, description="Number mapped")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Coverage percentage")
    missing_items: list[str] = Field(default_factory=list, description="Items not mapped")

    @field_validator("coverage_percentage")
    @classmethod
    def calculate_coverage(cls, _v: float, info: Any) -> float:
        """Auto-calculate coverage if not provided."""
        total = info.data.get("total_required", 0)
        mapped = info.data.get("mapped_count", 0)
        if total > 0:
            return (mapped / total) * 100.0
        return 0.0

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_required": 5,
            "mapped_count": 4,
            "coverage_percentage": 80.0,
            "missing_items": ["wafer"],
        }
    })


class MappingManifest(BaseModel):
    """Complete manifest of context and metrics mappings.

    Attributes:
        id: Unique identifier.
        project_id: Associated project ID.
        context_mappings: List of context mappings.
        metrics_mappings: List of metrics mappings.
        context_coverage: Coverage report for contexts.
        metrics_coverage: Coverage report for metrics.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: UUID = Field(default_factory=uuid4, description="Mapping manifest ID")
    project_id: UUID = Field(..., description="Associated project ID")
    context_mappings: list[ContextMapping] = Field(
        default_factory=list, description="Context mappings"
    )
    metrics_mappings: list[MetricMapping] = Field(
        default_factory=list, description="Metrics mappings"
    )
    value_aliases: dict[str, list[ValueAlias]] = Field(
        default_factory=dict, description="Value aliases by context name"
    )
    derived_columns: list[DerivedColumn] = Field(
        default_factory=list, description="Derived column configurations"
    )
    data_joins: list[DataJoin] = Field(
        default_factory=list, description="Data file join configurations"
    )
    column_renames: dict[str, str] = Field(
        default_factory=dict, description="Column rename mappings"
    )
    context_coverage: CoverageReport | None = Field(None, description="Context coverage report")
    metrics_coverage: CoverageReport | None = Field(None, description="Metrics coverage report")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")

    def get_context_mapping(self, context_name: str) -> ContextMapping | None:
        """Get mapping for a specific context.

        Args:
            context_name: Name of context to find.

        Returns:
            ContextMapping if found, None otherwise.
        """
        for mapping in self.context_mappings:
            if mapping.context_name == context_name:
                return mapping
        return None

    def get_metric_mapping(self, metric_name: str) -> MetricMapping | None:
        """Get mapping for a specific metric.

        Args:
            metric_name: Name of metric to find.

        Returns:
            MetricMapping if found, None otherwise.
        """
        for mapping in self.metrics_mappings:
            if mapping.metric_name == metric_name:
                return mapping
        return None

    def is_complete(self) -> bool:
        """Check if all mappings are complete (100% coverage).

        Returns:
            True if both context and metrics have 100% coverage.
        """
        context_complete = (
            self.context_coverage.coverage_percentage == 100.0 if self.context_coverage else False
        )
        metrics_complete = (
            self.metrics_coverage.coverage_percentage == 100.0 if self.metrics_coverage else False
        )
        return context_complete and metrics_complete

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "context_mappings": [
                {
                    "context_name": "side",
                    "source_type": "column",
                    "source_column": "SpaceCD_Side",
                }
            ],
            "metrics_mappings": [
                {
                    "metric_name": "CD",
                    "source_column": "Space CD (nm)",
                    "aggregation_semantics": "mean",
                }
            ],
        }
    })


# Validation test
if __name__ == "__main__":
    from uuid import uuid4

    # Test ContextMapping
    ctx_mapping = ContextMapping(
        context_name="side",
        source_type=MappingSourceType.COLUMN,
        source_column="SpaceCD_Side",
    )
    assert ctx_mapping.source_column == "SpaceCD_Side"

    # Test MetricMapping
    metric_mapping = MetricMapping(
        metric_name="CD",
        source_column="Space CD (nm)",
        rename_to="SpaceCD",
        aggregation_semantics=AggregationType.MEAN,
    )
    assert metric_mapping.get_target_name() == "SpaceCD"

    # Test MappingSuggestion
    suggestion = MappingSuggestion(
        target_name="side",
        suggested_source="SpaceCD_Side",
        source_type=MappingSourceType.COLUMN,
        confidence_score=0.9,
        reasoning="Substring match",
    )
    assert 0.0 <= suggestion.confidence_score <= 1.0

    # Test CoverageReport
    coverage = CoverageReport(
        total_required=5, mapped_count=4, coverage_percentage=80.0, missing_items=["wafer"]
    )
    assert coverage.coverage_percentage == 80.0

    # Test MappingManifest
    manifest = MappingManifest(
        project_id=uuid4(),
        context_mappings=[ctx_mapping],
        metrics_mappings=[metric_mapping],
        context_coverage=CoverageReport(
            total_required=1, mapped_count=1, coverage_percentage=100.0
        ),
        metrics_coverage=CoverageReport(
            total_required=1, mapped_count=1, coverage_percentage=100.0
        ),
    )
    assert manifest.is_complete()
    assert manifest.get_context_mapping("side") == ctx_mapping
    assert manifest.get_metric_mapping("CD") == metric_mapping

    print("All mapping manifest tests passed!")
