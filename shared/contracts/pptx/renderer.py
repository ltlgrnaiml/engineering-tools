"""PPTX Renderer contracts - pluggable shape rendering interface.

Per ADR-0022: PPTX uses a pluggable renderer system with a common interface.
Per ADR-0029: Renderers SHOULD consume RenderSpec contracts from shared rendering.

This module defines contracts for:
- Base renderer interface and registry
- Shape-specific render configurations
- Render operation results and errors
- Integration with unified rendering engine

Renderers are selected based on shape category from the naming convention.
Failed renders log errors but do not abort generation (graceful degradation).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


# =============================================================================
# Renderer Categories and Types
# =============================================================================


class RendererCategory(str, Enum):
    """Categories of shape renderers.

    Per ADR-0019: Shape categories from naming convention.
    """

    TEXT = "text"  # Text boxes, labels, titles
    CHART = "chart"  # Charts and visualizations
    TABLE = "table"  # Data tables
    IMAGE = "image"  # Images, logos, icons
    METRIC = "metric"  # Single numeric metric displays
    DIMENSION = "dimension"  # Categorical dimension labels


class RenderStatus(str, Enum):
    """Status of a render operation."""

    SUCCESS = "success"  # Rendered successfully
    PARTIAL = "partial"  # Rendered with warnings
    SKIPPED = "skipped"  # Intentionally skipped
    FAILED = "failed"  # Render failed (graceful degradation)


# =============================================================================
# Renderer Configuration Contracts
# =============================================================================


class TextRenderConfig(BaseModel):
    """Configuration for text shape rendering.

    Defines how text content is formatted and styled.
    """

    content: str = Field(..., description="Text content to render")
    font_name: str | None = Field(None, description="Font family name")
    font_size_pt: float | None = Field(None, ge=1.0, le=144.0, description="Font size in points")
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str | None = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Text color (hex)",
    )
    alignment: Literal["left", "center", "right", "justify"] | None = None
    vertical_alignment: Literal["top", "middle", "bottom"] | None = None

    # Template substitution
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Variables for template substitution in content",
    )

    # Auto-fit behavior
    auto_fit: bool = Field(True, description="Auto-fit text to shape")
    shrink_on_overflow: bool = Field(True, description="Shrink text if too large")


class ChartRenderConfig(BaseModel):
    """Configuration for chart shape rendering.

    Per ADR-0029: Delegates to unified rendering engine for chart generation.
    """

    chart_type: str = Field(
        ...,
        description="Chart type (bar, line, pie, scatter, etc.)",
    )
    data_source: str = Field(
        ...,
        description="Column or expression for chart data",
    )
    title: str | None = Field(None, description="Chart title")
    subtitle: str | None = None

    # Axes
    x_axis_label: str | None = None
    y_axis_label: str | None = None
    x_axis_column: str | None = Field(None, description="Column for X axis")
    y_axis_columns: list[str] = Field(
        default_factory=list,
        description="Columns for Y axis (series)",
    )

    # Series configuration
    series_names: list[str] | None = Field(
        None,
        description="Custom names for data series",
    )
    series_colors: list[str] | None = Field(
        None,
        description="Colors for each series (hex)",
    )

    # Legend
    show_legend: bool = True
    legend_position: Literal["top", "bottom", "left", "right"] | None = None

    # Data labels
    show_data_labels: bool = False
    data_label_format: str | None = Field(
        None,
        description="Number format for data labels",
    )

    # Style
    style_preset: str | None = Field(
        None,
        description="Named style preset from domain config",
    )

    # Size (in EMUs - English Metric Units)
    width_emu: int | None = Field(None, ge=0, description="Chart width in EMUs")
    height_emu: int | None = Field(None, ge=0, description="Chart height in EMUs")


class TableRenderConfig(BaseModel):
    """Configuration for table shape rendering."""

    columns: list[str] = Field(
        ...,
        min_length=1,
        description="Column names to include in table",
    )
    column_headers: list[str] | None = Field(
        None,
        description="Custom header labels (defaults to column names)",
    )
    column_widths: list[float] | None = Field(
        None,
        description="Relative column widths (proportional)",
    )

    # Row limits
    max_rows: int = Field(50, ge=1, le=500, description="Maximum rows to display")
    show_row_numbers: bool = Field(False, description="Show row index column")

    # Formatting
    number_format: str | None = Field(
        None,
        description="Default number format for numeric columns",
    )
    date_format: str | None = Field(
        None,
        description="Default date format",
    )
    null_display: str = Field("—", description="Display value for nulls")

    # Style
    header_style: dict[str, Any] = Field(
        default_factory=dict,
        description="Style for header row (font, color, etc.)",
    )
    row_style: dict[str, Any] = Field(
        default_factory=dict,
        description="Style for data rows",
    )
    alternating_rows: bool = Field(True, description="Use alternating row colors")
    alternating_color: str | None = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Alternating row color (hex)",
    )
    border_style: Literal["none", "thin", "medium", "thick"] = "thin"

    # Sorting
    sort_by: str | None = Field(None, description="Column to sort by")
    sort_ascending: bool = True


class ImageRenderConfig(BaseModel):
    """Configuration for image shape rendering."""

    source_type: Literal["file", "url", "dataset", "generated"] = Field(
        ...,
        description="Source type for the image",
    )
    source_path: str | None = Field(
        None,
        description="Relative path to image file",
    )
    source_url: str | None = Field(
        None,
        description="URL to fetch image from",
    )
    source_column: str | None = Field(
        None,
        description="Dataset column containing image data",
    )

    # Sizing
    maintain_aspect_ratio: bool = Field(True, description="Preserve aspect ratio")
    fit_mode: Literal["fit", "fill", "stretch", "center"] = "fit"
    max_width_px: int | None = Field(None, ge=1, description="Maximum width in pixels")
    max_height_px: int | None = Field(None, ge=1, description="Maximum height in pixels")

    # Quality
    quality: int = Field(85, ge=1, le=100, description="JPEG quality (1-100)")
    format: Literal["png", "jpeg", "svg"] = "png"

    # Placeholder
    placeholder_path: str | None = Field(
        None,
        description="Fallback image if source unavailable",
    )

    @field_validator("source_path", "placeholder_path")
    @classmethod
    def validate_relative_path(cls, v: str | None) -> str | None:
        """Ensure paths are relative (per ADR-0018 path-safety)."""
        if v is None:
            return v
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"Absolute paths not allowed: {v}")
        return v


class MetricRenderConfig(BaseModel):
    """Configuration for single metric display rendering."""

    value_source: str = Field(..., description="Column or expression for metric value")
    label: str | None = Field(None, description="Metric label text")
    format_type: Literal["number", "percent", "currency", "integer"] = "number"
    decimal_places: int = Field(2, ge=0, le=10)
    prefix: str | None = Field(None, description="Value prefix (e.g., '$')")
    suffix: str | None = Field(None, description="Value suffix (e.g., '%')")

    # Comparison
    compare_to: str | None = Field(
        None,
        description="Column for comparison value (shows delta)",
    )
    show_delta: bool = Field(False, description="Show change indicator")
    delta_format: Literal["absolute", "percent", "both"] = "percent"

    # Styling
    value_font_size_pt: float = Field(24.0, ge=8.0, le=144.0)
    label_font_size_pt: float = Field(12.0, ge=6.0, le=72.0)
    positive_color: str = Field("#22C55E", pattern=r"^#[0-9A-Fa-f]{6}$")
    negative_color: str = Field("#EF4444", pattern=r"^#[0-9A-Fa-f]{6}$")
    neutral_color: str = Field("#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")


# =============================================================================
# Render Context and Input
# =============================================================================


class ShapeRenderContext(BaseModel):
    """Context provided to renderers for shape population.

    Contains all information needed to render a shape.
    """

    # Shape identification
    shape_name: str = Field(..., description="Shape name from template")
    shape_category: RendererCategory
    slide_index: int = Field(..., ge=0, description="0-indexed slide position")

    # Shape geometry (from template)
    left_emu: int = Field(..., description="Left position in EMUs")
    top_emu: int = Field(..., description="Top position in EMUs")
    width_emu: int = Field(..., description="Width in EMUs")
    height_emu: int = Field(..., description="Height in EMUs")

    # Configuration (category-specific)
    config: TextRenderConfig | ChartRenderConfig | TableRenderConfig | ImageRenderConfig | MetricRenderConfig

    # Data context
    data_row: dict[str, Any] | None = Field(
        None,
        description="Current data row for iteration",
    )
    data_index: int | None = Field(
        None,
        ge=0,
        description="Index in data iteration",
    )
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional variables for substitution",
    )


class RenderInput(BaseModel):
    """Complete input for a render operation."""

    template_id: str
    project_id: str
    contexts: list[ShapeRenderContext] = Field(
        ...,
        description="All shape render contexts for this operation",
    )
    global_variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Variables available to all shapes",
    )


# =============================================================================
# Render Results
# =============================================================================


class ShapeRenderResult(BaseModel):
    """Result of rendering a single shape.

    Per ADR-0022: Failed renders log errors but do not abort generation.
    """

    shape_name: str
    shape_category: RendererCategory
    slide_index: int
    status: RenderStatus
    render_duration_ms: float = Field(0.0, ge=0.0)

    # Error information (for failed/partial renders)
    error_code: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)

    # Output metadata
    output_type: str | None = Field(
        None,
        description="Type of content rendered (text, chart, etc.)",
    )
    bytes_rendered: int | None = Field(None, ge=0)


class RendererResult(BaseModel):
    """Complete result from a renderer operation."""

    renderer_id: str
    renderer_category: RendererCategory
    shapes_processed: int = Field(0, ge=0)
    shapes_succeeded: int = Field(0, ge=0)
    shapes_failed: int = Field(0, ge=0)
    shapes_skipped: int = Field(0, ge=0)
    total_duration_ms: float = Field(0.0, ge=0.0)

    results: list[ShapeRenderResult] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.shapes_processed == 0:
            return 100.0
        return (self.shapes_succeeded / self.shapes_processed) * 100.0


# =============================================================================
# Renderer Registry
# =============================================================================


class RendererMetadata(BaseModel):
    """Metadata about a renderer for registry.

    Per ADR-0022: Renderers are registered in RendererRegistry.
    """

    renderer_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique renderer identifier",
    )
    name: str = Field(..., min_length=1, max_length=100)
    category: RendererCategory
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Renderer version (semver)",
    )
    description: str = Field("", max_length=500)

    # Capabilities
    supports_batch: bool = Field(
        False,
        description="Can render multiple shapes in one call",
    )
    supports_async: bool = Field(
        True,
        description="Supports async rendering",
    )
    max_concurrent: int = Field(
        1,
        ge=1,
        description="Maximum concurrent renders",
    )

    # Dependencies
    requires_data: bool = Field(
        True,
        description="Whether renderer needs data context",
    )
    uses_unified_engine: bool = Field(
        False,
        description="Whether renderer delegates to shared/rendering/",
    )


class RendererRegistryEntry(BaseModel):
    """Entry in the renderer registry."""

    renderer_id: str
    metadata: RendererMetadata
    registered_at: datetime
    is_builtin: bool = True


class RendererRegistryState(BaseModel):
    """Serializable state of the renderer registry."""

    renderers: list[RendererRegistryEntry] = Field(default_factory=list)
    category_map: dict[str, str] = Field(
        default_factory=dict,
        description="Category -> renderer_id mapping",
    )
    last_updated: datetime | None = None


# =============================================================================
# Base Renderer Interface (Abstract)
# =============================================================================


class BaseRenderer(ABC):
    """Base class for all shape renderers.

    Per ADR-0022: All renderers MUST implement this interface.
    Renderers MUST NOT raise exceptions that abort generation.

    Implementation notes:
    - All render methods are async for FastAPI compatibility
    - Methods should catch exceptions and return failed RenderResult
    - Failed renders should log errors but continue (graceful degradation)

    Example implementation:
        class TextRenderer(BaseRenderer):
            @property
            def metadata(self) -> RendererMetadata:
                return RendererMetadata(
                    renderer_id="text",
                    name="Text Renderer",
                    category=RendererCategory.TEXT,
                    version="1.0.0",
                )

            async def render(self, context: ShapeRenderContext, shape: Any) -> ShapeRenderResult:
                # Implementation using python-pptx
                ...
    """

    @property
    @abstractmethod
    def metadata(self) -> RendererMetadata:
        """Return renderer metadata for registry.

        Returns:
            RendererMetadata with renderer ID, capabilities, etc.
        """
        ...

    @abstractmethod
    async def render(
        self,
        context: ShapeRenderContext,
        shape: Any,  # python-pptx shape object
    ) -> ShapeRenderResult:
        """Render content into a shape.

        Per ADR-0022: MUST NOT raise exceptions that abort generation.
        Catch all exceptions and return failed ShapeRenderResult.

        Args:
            context: Render context with configuration and data.
            shape: python-pptx shape object to populate.

        Returns:
            ShapeRenderResult with status and any errors/warnings.
        """
        ...

    @abstractmethod
    async def validate_config(
        self,
        config: TextRenderConfig | ChartRenderConfig | TableRenderConfig | ImageRenderConfig | MetricRenderConfig,
    ) -> list[str]:
        """Validate renderer configuration before rendering.

        Args:
            config: Configuration to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        ...

    def can_handle(self, category: RendererCategory) -> bool:
        """Check if this renderer handles a category.

        Args:
            category: Shape category to check.

        Returns:
            True if this renderer handles the category.
        """
        return self.metadata.category == category


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "RendererCategory",
    "RenderStatus",
    # Render configurations
    "TextRenderConfig",
    "ChartRenderConfig",
    "TableRenderConfig",
    "ImageRenderConfig",
    "MetricRenderConfig",
    # Context and input
    "ShapeRenderContext",
    "RenderInput",
    # Results
    "ShapeRenderResult",
    "RendererResult",
    # Registry
    "RendererMetadata",
    "RendererRegistryEntry",
    "RendererRegistryState",
    # Base class
    "BaseRenderer",
]
