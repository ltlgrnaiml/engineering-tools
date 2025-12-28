"""Derived Requirements Manifest (DRM) models.

The DRM contains the Four Required Lists extracted from template shapes:
1. Required Contexts - categorical dimensions (side, wafer, etc.)
2. Required Metrics - numeric measurements (CD, LWR, etc.)
3. Required Data Levels - cardinality requirements per renderer
4. Required Renderers - inventory of renderer types used
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MappingSourceType(str, Enum):
    """Source type for context mapping."""

    COLUMN = "column"
    REGEX = "regex"
    DEFAULT = "default"


class AggregationType(str, Enum):
    """Aggregation type for metrics."""

    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    COUNT = "count"
    SIGMA_3 = "3sigma"


class DataLevelCardinality(str, Enum):
    """Data cardinality requirement for renderers."""

    ONE_ROW = "one_row"
    MANY_ROWS = "many_rows"
    AGGREGATED = "aggregated"
    AGGREGATED_OR_RAW = "aggregated_or_raw"


class RequiredContext(BaseModel):
    """A required context dimension extracted from template.

    Attributes:
        name: Context dimension name (e.g., 'side', 'wafer', 'imcol').
        source_type: How this context is derived (column, regex, default).
        derivation_pattern: Regex pattern if source_type is REGEX.
        default_value: Default value if source_type is DEFAULT.
        description: Human-readable description.
    """

    name: str = Field(..., description="Context dimension name")
    source_type: MappingSourceType | None = Field(None, description="How context is derived")
    derivation_pattern: str | None = Field(None, description="Regex pattern for derivation")
    default_value: str | None = Field(None, description="Default value")
    description: str | None = Field(None, description="Human-readable description")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "side",
            "source_type": "column",
            "description": "Left or Right side dimension",
        }
    })


class RequiredMetric(BaseModel):
    """A required metric extracted from template.

    Attributes:
        name: Metric name (e.g., 'CD', 'LWR', 'LCDU').
        aggregation_type: Required aggregation (mean, 3sigma, etc.).
        data_type: Expected data type (float, int).
        unit: Measurement unit (e.g., 'nm').
        description: Human-readable description.
    """

    name: str = Field(..., description="Metric name")
    aggregation_type: AggregationType | None = Field(None, description="Required aggregation")
    data_type: str = Field(default="float", description="Expected data type")
    unit: str | None = Field(None, description="Measurement unit")
    description: str | None = Field(None, description="Human-readable description")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "CD",
            "aggregation_type": "mean",
            "data_type": "float",
            "unit": "nm",
        }
    })


class RequiredDataLevel(BaseModel):
    """Data level requirement for a renderer class.

    Attributes:
        renderer_class: Renderer type (e.g., 'plot', 'table', 'kpi').
        cardinality: Required data cardinality.
        description: Human-readable description.
    """

    renderer_class: str = Field(..., description="Renderer type")
    cardinality: DataLevelCardinality = Field(..., description="Required cardinality")
    description: str | None = Field(None, description="Human-readable description")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "renderer_class": "plot",
            "cardinality": "many_rows",
            "description": "Plots require many rows for distributions",
        }
    })


class RequiredRenderer(BaseModel):
    """A required renderer type extracted from template.

    Attributes:
        renderer_type: Type of renderer (plot, table, text, etc.).
        renderer_subtype: Specific subtype (contour, bar, summary, etc.).
        shape_references: List of shape names using this renderer.
        count: Number of shapes using this renderer.
    """

    renderer_type: str = Field(..., description="Renderer type")
    renderer_subtype: str = Field(..., description="Renderer subtype")
    shape_references: list[str] = Field(
        default_factory=list, description="Shapes using this renderer"
    )
    count: int = Field(default=0, description="Number of shapes")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "renderer_type": "plot",
            "renderer_subtype": "contour",
            "shape_references": ["plot__metrics__by_side__contour__side=left__metrics=CD"],
            "count": 1,
        }
    })


class DerivedRequirementsManifest(BaseModel):
    """Complete manifest of requirements derived from template.

    This is the core DRM model containing the Four Required Lists.

    Attributes:
        id: Unique identifier for this DRM.
        template_id: ID of the template this was derived from.
        required_contexts: List of required context dimensions.
        required_metrics: List of required metrics.
        required_data_levels: List of data level requirements.
        required_renderers: List of required renderer types.
        created_at: Timestamp when DRM was created.
        version: DRM schema version.
    """

    id: UUID = Field(default_factory=uuid4, description="DRM ID")
    template_id: UUID = Field(..., description="Associated template ID")
    required_contexts: list[RequiredContext] = Field(
        default_factory=list, description="Required context dimensions"
    )
    required_metrics: list[RequiredMetric] = Field(
        default_factory=list, description="Required metrics"
    )
    required_data_levels: list[RequiredDataLevel] = Field(
        default_factory=list, description="Data level requirements"
    )
    required_renderers: list[RequiredRenderer] = Field(
        default_factory=list, description="Required renderer types"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    version: str = Field(default="1.0", description="DRM schema version")

    def get_all_metrics(self) -> list[str]:
        """Get list of all metric names.

        Returns:
            List of metric names.
        """
        return [metric.name for metric in self.required_metrics]

    def get_all_contexts(self) -> list[str]:
        """Get list of all context names.

        Returns:
            List of context names.
        """
        return [context.name for context in self.required_contexts]

    def get_renderers_by_type(self, renderer_type: str) -> list[RequiredRenderer]:
        """Get renderers filtered by type.

        Args:
            renderer_type: The renderer type to filter by.

        Returns:
            List of renderers matching the type.
        """
        return [
            renderer
            for renderer in self.required_renderers
            if renderer.renderer_type == renderer_type
        ]

    def get_context_by_name(self, name: str) -> RequiredContext | None:
        """Get a specific context by name.

        Args:
            name: Context name to find.

        Returns:
            RequiredContext if found, None otherwise.
        """
        for context in self.required_contexts:
            if context.name == name:
                return context
        return None

    def get_metric_by_name(self, name: str) -> RequiredMetric | None:
        """Get a specific metric by name.

        Args:
            name: Metric name to find.

        Returns:
            RequiredMetric if found, None otherwise.
        """
        for metric in self.required_metrics:
            if metric.name == name:
                return metric
        return None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "template_id": "123e4567-e89b-12d3-a456-426614174002",
            "required_contexts": [{"name": "side"}],
            "required_metrics": [{"name": "CD", "aggregation_type": "mean"}],
            "required_data_levels": [{"renderer_class": "plot", "cardinality": "many_rows"}],
            "required_renderers": [
                {"renderer_type": "plot", "renderer_subtype": "contour", "count": 1}
            ],
            "version": "1.0",
        }
    })


# Validation test (remove after testing)
if __name__ == "__main__":
    from uuid import uuid4

    # Test DRM creation
    drm = DerivedRequirementsManifest(
        template_id=uuid4(),
        required_contexts=[
            RequiredContext(name="side", source_type=MappingSourceType.COLUMN),
            RequiredContext(name="wafer", source_type=MappingSourceType.COLUMN),
        ],
        required_metrics=[
            RequiredMetric(name="CD", aggregation_type=AggregationType.MEAN),
            RequiredMetric(name="LWR", aggregation_type=AggregationType.SIGMA_3),
        ],
        required_data_levels=[
            RequiredDataLevel(renderer_class="plot", cardinality=DataLevelCardinality.MANY_ROWS),
        ],
        required_renderers=[
            RequiredRenderer(renderer_type="plot", renderer_subtype="contour", count=2),
        ],
    )

    # Test helper methods
    assert drm.get_all_metrics() == ["CD", "LWR"]
    assert drm.get_all_contexts() == ["side", "wafer"]
    assert len(drm.get_renderers_by_type("plot")) == 1
    context = drm.get_context_by_name("side")
    assert context is not None and context.name == "side"
    metric = drm.get_metric_by_name("CD")
    assert metric is not None and metric.aggregation_type == AggregationType.MEAN

    # Test JSON serialization
    json_str = drm.model_dump_json(indent=2)
    print("DRM JSON:")
    print(json_str)

    print("\nAll validation tests passed!")
