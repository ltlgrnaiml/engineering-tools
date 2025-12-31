"""PPTX Domain Configuration contracts - domain-specific report settings.

Per ADR-0021: Domain configuration defines job contexts, canonical metrics,
and rendering rules. Config is validated at startup (fail-fast) and immutable
at runtime.

This module defines contracts for:
- Job context dimensions (for report filtering)
- Canonical metrics with alias resolution
- Domain-specific rendering rules
- Configuration validation results

Configuration is loaded from YAML and validated against these Pydantic models.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


# =============================================================================
# Metric Configuration
# =============================================================================


class MetricCategory(str, Enum):
    """Categories for organizing metrics."""

    YIELD = "yield"
    DEFECT = "defect"
    THROUGHPUT = "throughput"
    CYCLE_TIME = "cycle_time"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class MetricAggregation(str, Enum):
    """Aggregation methods for metrics."""

    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"


class MetricFormat(str, Enum):
    """Display format types for metrics."""

    NUMBER = "number"
    PERCENT = "percent"
    CURRENCY = "currency"
    SCIENTIFIC = "scientific"
    INTEGER = "integer"


class CanonicalMetric(BaseModel):
    """Definition of a canonical metric with aliases.

    Per ADR-0021: All metric aliases resolve to canonical names.
    """

    canonical_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Canonical metric name (used internally)",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable display name",
    )
    category: MetricCategory = MetricCategory.CUSTOM
    description: str = Field(
        "",
        max_length=500,
        description="Metric description for documentation",
    )

    # Aliases that map to this canonical metric
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names that resolve to this metric",
    )

    # Aggregation behavior
    default_aggregation: MetricAggregation = MetricAggregation.MEAN
    allowed_aggregations: list[MetricAggregation] = Field(
        default_factory=lambda: list(MetricAggregation),
        description="Aggregations allowed for this metric",
    )

    # Display formatting
    format_type: MetricFormat = MetricFormat.NUMBER
    decimal_places: int = Field(2, ge=0, le=10)
    unit: str | None = Field(None, description="Unit label (e.g., '%', 'nm', 'ms')")
    prefix: str | None = Field(None, description="Prefix for display (e.g., '$')")
    suffix: str | None = Field(None, description="Suffix for display (e.g., '/hr')")

    # Thresholds for coloring
    warning_threshold: float | None = Field(
        None,
        description="Value below which to show warning (yellow)",
    )
    critical_threshold: float | None = Field(
        None,
        description="Value below which to show critical (red)",
    )
    higher_is_better: bool = Field(
        True,
        description="Whether higher values are desirable",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list)

    @field_validator("aliases")
    @classmethod
    def normalize_aliases(cls, v: list[str]) -> list[str]:
        """Normalize aliases to lowercase for matching."""
        return [alias.lower().strip() for alias in v if alias.strip()]


class MetricRegistry(BaseModel):
    """Registry of all canonical metrics in a domain.

    Per ADR-0021: All metric aliases MUST resolve to canonical metrics.
    """

    metrics: list[CanonicalMetric] = Field(
        ...,
        min_length=1,
        description="All canonical metrics",
    )

    # Computed at validation time
    _alias_map: dict[str, str] = {}

    @model_validator(mode="after")
    def build_alias_map(self) -> "MetricRegistry":
        """Build alias -> canonical name lookup map."""
        alias_map: dict[str, str] = {}
        for metric in self.metrics:
            # Map canonical name to itself
            alias_map[metric.canonical_name.lower()] = metric.canonical_name
            # Map all aliases
            for alias in metric.aliases:
                if alias in alias_map:
                    raise ValueError(
                        f"Duplicate alias '{alias}' - already maps to "
                        f"'{alias_map[alias]}', cannot also map to '{metric.canonical_name}'"
                    )
                alias_map[alias] = metric.canonical_name
        object.__setattr__(self, "_alias_map", alias_map)
        return self

    def resolve_metric(self, name: str) -> str | None:
        """Resolve a metric name or alias to canonical name.

        Args:
            name: Metric name or alias to resolve.

        Returns:
            Canonical metric name, or None if not found.
        """
        return self._alias_map.get(name.lower().strip())

    def get_metric(self, canonical_name: str) -> CanonicalMetric | None:
        """Get metric definition by canonical name.

        Args:
            canonical_name: Canonical metric name.

        Returns:
            Metric definition, or None if not found.
        """
        for metric in self.metrics:
            if metric.canonical_name == canonical_name:
                return metric
        return None


# =============================================================================
# Job Context Configuration
# =============================================================================


class ContextDimensionType(str, Enum):
    """Types of context dimensions."""

    CATEGORICAL = "categorical"  # Fixed set of values
    DATE = "date"  # Date values
    DATETIME = "datetime"  # Datetime values
    NUMERIC = "numeric"  # Numeric values
    TEXT = "text"  # Free-form text


class ContextDimension(BaseModel):
    """Definition of a job context dimension.

    Context dimensions define how reports can be filtered/grouped.
    """

    dimension_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique dimension identifier",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name",
    )
    dimension_type: ContextDimensionType = ContextDimensionType.CATEGORICAL
    description: str = Field("", max_length=500)

    # For categorical dimensions
    allowed_values: list[str] | None = Field(
        None,
        description="Fixed set of allowed values (categorical only)",
    )
    default_value: str | None = Field(
        None,
        description="Default value if not specified",
    )

    # Validation
    required: bool = Field(True, description="Whether dimension must be provided")
    min_length: int | None = Field(None, ge=1, description="Min length for text")
    max_length: int | None = Field(None, ge=1, description="Max length for text")

    # Display
    display_order: int = Field(0, description="Order in UI (lower = first)")
    hidden: bool = Field(False, description="Hide from UI but still available")

    @model_validator(mode="after")
    def validate_allowed_values(self) -> "ContextDimension":
        """Validate allowed_values is set for categorical dimensions."""
        if self.dimension_type == ContextDimensionType.CATEGORICAL:
            if not self.allowed_values:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' is categorical but has no allowed_values"
                )
            if self.default_value and self.default_value not in self.allowed_values:
                raise ValueError(
                    f"Default value '{self.default_value}' not in allowed_values"
                )
        return self


class JobContext(BaseModel):
    """Definition of a job context (report filter configuration).

    A job context specifies which dimensions are required/optional
    for a particular type of report.
    """

    context_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique context identifier",
    )
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)

    # Required dimensions for this context
    required_dimensions: list[str] = Field(
        default_factory=list,
        description="Dimension IDs that must be provided",
    )
    optional_dimensions: list[str] = Field(
        default_factory=list,
        description="Dimension IDs that may be provided",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list)
    display_order: int = Field(0)


# =============================================================================
# Rendering Rules Configuration
# =============================================================================


class ChartType(str, Enum):
    """Supported chart types for rendering."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    COMBO = "combo"
    WATERFALL = "waterfall"
    HEATMAP = "heatmap"
    BOX = "box"


class RenderingRule(BaseModel):
    """Rule for how to render a metric in reports.

    Defines chart types, colors, and presentation options.
    """

    rule_id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    applies_to_metrics: list[str] = Field(
        default_factory=list,
        description="Canonical metric names this rule applies to",
    )
    applies_to_categories: list[MetricCategory] = Field(
        default_factory=list,
        description="Metric categories this rule applies to",
    )

    # Chart configuration
    preferred_chart_type: ChartType = ChartType.BAR
    allowed_chart_types: list[ChartType] = Field(
        default_factory=lambda: list(ChartType),
    )

    # Colors
    primary_color: str | None = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Primary color (hex)",
    )
    secondary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    gradient: bool = Field(False, description="Use gradient fill")

    # Layout
    show_legend: bool = Field(True)
    show_data_labels: bool = Field(True)
    show_gridlines: bool = Field(True)
    title_template: str | None = Field(
        None,
        description="Template for chart title (supports {metric_name}, {context})",
    )


# =============================================================================
# Complete Domain Configuration
# =============================================================================


class DomainConfig(BaseModel):
    """Complete domain configuration for PPTX Generator.

    Per ADR-0021: Validated at startup, immutable at runtime.
    """

    # Identity
    domain_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_-]*$",
        description="Unique domain identifier",
    )
    domain_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=1000)
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Domain config version (semver)",
    )

    # Core configuration
    metrics: MetricRegistry
    dimensions: list[ContextDimension] = Field(
        ...,
        min_length=1,
        description="Available context dimensions",
    )
    job_contexts: list[JobContext] = Field(
        ...,
        min_length=1,
        description="Configured job contexts",
    )
    rendering_rules: list[RenderingRule] = Field(
        default_factory=list,
        description="Rendering rules for metrics",
    )

    # Defaults
    default_job_context: str | None = Field(
        None,
        description="Default job context ID",
    )
    default_chart_type: ChartType = ChartType.BAR
    default_date_format: str = Field("%Y-%m-%d", description="Date format string")
    default_datetime_format: str = Field(
        "%Y-%m-%d %H:%M",
        description="Datetime format string",
    )

    # Metadata
    created_at: datetime | None = None
    updated_at: datetime | None = None
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "DomainConfig":
        """Validate all cross-references are valid."""
        # Build dimension ID set
        dimension_ids = {d.dimension_id for d in self.dimensions}

        # Validate job context dimension references
        for ctx in self.job_contexts:
            for dim_id in ctx.required_dimensions + ctx.optional_dimensions:
                if dim_id not in dimension_ids:
                    raise ValueError(
                        f"Job context '{ctx.context_id}' references unknown "
                        f"dimension '{dim_id}'"
                    )

        # Validate default job context
        if self.default_job_context:
            context_ids = {ctx.context_id for ctx in self.job_contexts}
            if self.default_job_context not in context_ids:
                raise ValueError(
                    f"Default job context '{self.default_job_context}' not found"
                )

        # Validate rendering rule metric references
        canonical_names = {m.canonical_name for m in self.metrics.metrics}
        for rule in self.rendering_rules:
            for metric_name in rule.applies_to_metrics:
                if metric_name not in canonical_names:
                    raise ValueError(
                        f"Rendering rule '{rule.rule_id}' references unknown "
                        f"metric '{metric_name}'"
                    )

        return self

    def get_dimension(self, dimension_id: str) -> ContextDimension | None:
        """Get dimension by ID.

        Args:
            dimension_id: Dimension identifier.

        Returns:
            Dimension definition, or None if not found.
        """
        for dim in self.dimensions:
            if dim.dimension_id == dimension_id:
                return dim
        return None

    def get_job_context(self, context_id: str) -> JobContext | None:
        """Get job context by ID.

        Args:
            context_id: Job context identifier.

        Returns:
            Job context definition, or None if not found.
        """
        for ctx in self.job_contexts:
            if ctx.context_id == context_id:
                return ctx
        return None


class DomainConfigRef(BaseModel):
    """Lightweight reference for domain config list responses."""

    domain_id: str
    domain_name: str
    version: str
    metric_count: int
    dimension_count: int
    context_count: int
    created_at: datetime | None = None


class DomainConfigValidationResult(BaseModel):
    """Result of validating a domain configuration.

    Per ADR-0021: Invalid config causes startup failure (fail-fast).
    """

    valid: bool
    domain_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validation_duration_ms: float = Field(0.0, ge=0.0)


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "MetricCategory",
    "MetricAggregation",
    "MetricFormat",
    "ContextDimensionType",
    "ChartType",
    # Metric configuration
    "CanonicalMetric",
    "MetricRegistry",
    # Context configuration
    "ContextDimension",
    "JobContext",
    # Rendering configuration
    "RenderingRule",
    # Complete config
    "DomainConfig",
    "DomainConfigRef",
    "DomainConfigValidationResult",
]
