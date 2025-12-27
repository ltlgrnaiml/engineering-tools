"""Unified Rendering Engine contracts.

Per ADR-0028: Unified Rendering Engine for Cross-Tool Visualization.

This module defines the core contracts for the shared rendering system:
- RenderSpec hierarchy: Abstract specifications for WHAT to render
- OutputTarget: WHERE to render (web, PNG, SVG, PPTX)
- RenderResult: Output from rendering operations
- Styling: Common theming and appearance contracts

All tools (DAT, SOV, PPTX) consume these contracts. Tool-specific
extensions (e.g., PPTX shape bindings) import from here.

The contracts are renderer-agnostic - they define data and configuration,
not implementation details like matplotlib axes or PPTX shapes.
"""

from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


# =============================================================================
# Output Targets
# =============================================================================


class OutputTarget(str, Enum):
    """Where rendered output should be directed."""

    WEB_JSON = "web_json"  # JSON for frontend charting libraries
    WEB_HTML = "web_html"  # Interactive HTML (e.g., Plotly)
    PNG = "png"  # Static PNG image
    SVG = "svg"  # Vector SVG image
    PDF = "pdf"  # PDF document
    PPTX_IMAGE = "pptx_image"  # Image for PPTX embedding
    PPTX_NATIVE = "pptx_native"  # Native PPTX chart/table (python-pptx)


class OutputFormat(BaseModel):
    """Configuration for a specific output format."""

    target: OutputTarget
    width_px: int = Field(800, ge=100, le=4096)
    height_px: int = Field(600, ge=100, le=4096)
    dpi: int = Field(150, ge=72, le=600)
    quality: int = Field(90, ge=1, le=100, description="JPEG quality if applicable")
    transparent_background: bool = False


# =============================================================================
# Color and Styling
# =============================================================================


class ColorPalette(str, Enum):
    """Pre-defined color palettes for visualizations."""

    DEFAULT = "default"
    COLORBLIND_SAFE = "colorblind_safe"
    GRAYSCALE = "grayscale"
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    CATEGORICAL = "categorical"
    SEQUENTIAL = "sequential"
    DIVERGING = "diverging"
    CORPORATE = "corporate"


class FontConfig(BaseModel):
    """Font configuration for rendered text."""

    family: str = Field("Arial", description="Font family name")
    size: float = Field(11.0, ge=6.0, le=72.0)
    weight: Literal["normal", "bold", "light"] = "normal"
    style: Literal["normal", "italic"] = "normal"
    color: str = Field("#333333", description="Hex color code")


class GridConfig(BaseModel):
    """Grid line configuration for charts."""

    show: bool = True
    color: str = Field("#E5E5E5")
    style: Literal["solid", "dashed", "dotted"] = "solid"
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    x_axis: bool = True
    y_axis: bool = True


class LegendConfig(BaseModel):
    """Legend configuration for charts."""

    show: bool = True
    position: Literal[
        "right", "left", "top", "bottom",
        "inside_top_right", "inside_top_left",
        "inside_bottom_right", "inside_bottom_left"
    ] = "right"
    font: FontConfig = Field(default_factory=lambda: FontConfig(size=10.0))
    background_color: str | None = None
    border_color: str | None = None


class AxisConfig(BaseModel):
    """Axis configuration for charts."""

    label: str | None = None
    label_font: FontConfig = Field(default_factory=lambda: FontConfig(size=11.0))
    tick_font: FontConfig = Field(default_factory=lambda: FontConfig(size=10.0))
    min_value: float | None = None
    max_value: float | None = None
    log_scale: bool = False
    invert: bool = False
    tick_rotation: float = Field(0.0, ge=-90.0, le=90.0)
    tick_format: str | None = Field(None, description="Format string for tick labels")
    show_zero_line: bool = False
    grid: GridConfig = Field(default_factory=GridConfig)


class RenderStyle(BaseModel):
    """Complete styling configuration for rendering.

    This is the single source of truth for default styling across all tools.
    Per ADR-0028: PlotStyle must be centralized.
    """

    # Colors
    palette: ColorPalette = ColorPalette.DEFAULT
    custom_colors: list[str] | None = Field(
        None,
        description="Custom hex colors (overrides palette)",
    )
    background_color: str = Field("#FFFFFF")
    foreground_color: str = Field("#333333")

    # Fonts
    title_font: FontConfig = Field(
        default_factory=lambda: FontConfig(size=14.0, weight="bold")
    )
    label_font: FontConfig = Field(default_factory=lambda: FontConfig(size=11.0))
    tick_font: FontConfig = Field(default_factory=lambda: FontConfig(size=10.0))
    annotation_font: FontConfig = Field(default_factory=lambda: FontConfig(size=9.0))

    # Grid
    grid: GridConfig = Field(default_factory=GridConfig)

    # Legend
    legend: LegendConfig = Field(default_factory=LegendConfig)

    # Axes
    x_axis: AxisConfig = Field(default_factory=AxisConfig)
    y_axis: AxisConfig = Field(default_factory=AxisConfig)

    # Margins (in inches)
    margin_top: float = Field(0.5, ge=0.0, le=2.0)
    margin_bottom: float = Field(0.5, ge=0.0, le=2.0)
    margin_left: float = Field(0.5, ge=0.0, le=2.0)
    margin_right: float = Field(0.5, ge=0.0, le=2.0)

    @field_validator("custom_colors")
    @classmethod
    def validate_hex_colors(cls, v: list[str] | None) -> list[str] | None:
        """Validate custom colors are valid hex codes."""
        if v is None:
            return None
        import re
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for color in v:
            if not hex_pattern.match(color):
                raise ValueError(f"Invalid hex color: {color}")
        return v


# =============================================================================
# Chart Types
# =============================================================================


class ChartType(str, Enum):
    """Supported chart types across all tools."""

    # Basic charts
    LINE = "line"
    BAR = "bar"
    COLUMN = "column"
    AREA = "area"
    SCATTER = "scatter"
    BUBBLE = "bubble"

    # Statistical charts
    BOX = "box"
    VIOLIN = "violin"
    HISTOGRAM = "histogram"
    DENSITY = "density"

    # Comparison charts
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    WATERFALL = "waterfall"
    PARETO = "pareto"

    # Distribution charts
    PIE = "pie"
    DONUT = "donut"
    RADAR = "radar"
    TREEMAP = "treemap"

    # Spatial charts
    HEATMAP = "heatmap"
    CONTOUR = "contour"
    WAFER_MAP = "wafer_map"

    # Statistical analysis
    QQ_PLOT = "qq_plot"
    RESIDUAL_PLOT = "residual_plot"
    INTERACTION_PLOT = "interaction_plot"
    MAIN_EFFECTS = "main_effects"

    # Composite
    COMBO = "combo"


# =============================================================================
# Data Series
# =============================================================================


class DataSeries(BaseModel):
    """A single data series for charting.

    This is the fundamental unit of chart data - a named collection
    of values with optional styling.
    """

    name: str = Field(..., description="Series name (shown in legend)")
    values: list[float | int | None] = Field(
        ...,
        description="Y values (None for missing data)",
    )
    labels: list[str] | None = Field(
        None,
        description="X labels/categories (optional)",
    )
    x_values: list[float | int] | None = Field(
        None,
        description="Numeric X values for scatter/line charts",
    )

    # Styling overrides
    color: str | None = Field(None, description="Series color (hex)")
    line_style: Literal["solid", "dashed", "dotted"] | None = None
    line_width: float | None = Field(None, ge=0.5, le=10.0)
    marker_style: str | None = Field(None, description="Marker shape (o, s, ^, etc.)")
    marker_size: float | None = Field(None, ge=1.0, le=50.0)
    alpha: float = Field(1.0, ge=0.0, le=1.0)

    # Error bars (optional)
    error_low: list[float] | None = None
    error_high: list[float] | None = None


class DataPoint(BaseModel):
    """A single labeled data point for pie/donut charts."""

    label: str
    value: float
    color: str | None = None
    explode: float = Field(0.0, ge=0.0, le=0.5, description="Pie slice offset")


class HeatmapData(BaseModel):
    """2D data for heatmap/contour rendering."""

    values: list[list[float | None]] = Field(
        ...,
        description="2D array of values (row-major)",
    )
    row_labels: list[str] | None = None
    column_labels: list[str] | None = None
    colormap: str = Field("viridis", description="Colormap name")
    vmin: float | None = None
    vmax: float | None = None
    show_values: bool = False
    value_format: str = Field("{:.2f}", description="Format for cell values")


class TableData(BaseModel):
    """Data for table rendering."""

    headers: list[str] = Field(..., description="Column headers")
    rows: list[list[Any]] = Field(..., description="Row data (list of lists)")

    # Column configuration
    column_widths: list[float] | None = Field(
        None,
        description="Column widths in inches",
    )
    column_alignments: list[Literal["left", "center", "right"]] | None = None
    column_formats: dict[str, str] = Field(
        default_factory=dict,
        description="Column name -> format string",
    )

    # Row highlighting
    highlight_rows: list[int] = Field(
        default_factory=list,
        description="Row indices to highlight",
    )
    highlight_color: str = Field("#FFFFCC")


# =============================================================================
# RenderSpec Hierarchy (Abstract Base)
# =============================================================================


class RenderSpec(BaseModel, ABC):
    """Abstract base for all render specifications.

    Per ADR-0028: RenderSpec contracts define WHAT to render,
    not HOW (renderer-agnostic).
    """

    # Identity
    spec_id: str = Field(
        ...,
        description="Unique identifier for this spec",
    )
    name: str = Field(..., description="Human-readable name")
    description: str | None = None

    # Styling
    style: RenderStyle = Field(default_factory=RenderStyle)

    # Title and labels
    title: str | None = None
    subtitle: str | None = None

    # Output preferences
    preferred_outputs: list[OutputTarget] = Field(
        default=[OutputTarget.PNG],
    )
    width_px: int = Field(800, ge=100, le=4096)
    height_px: int = Field(600, ge=100, le=4096)

    # Metadata
    created_at: datetime | None = None
    source_tool: str | None = Field(
        None,
        description="Tool that created this spec (dat, sov, pptx)",
    )
    tags: list[str] = Field(default_factory=list)


class ChartSpec(RenderSpec):
    """Specification for chart rendering.

    This is the primary contract for all chart types. Tools create
    ChartSpecs and pass them to the rendering engine.
    """

    chart_type: ChartType

    # Data
    series: list[DataSeries] = Field(
        default_factory=list,
        description="Data series to plot",
    )
    categories: list[str] | None = Field(
        None,
        description="Category labels for categorical charts",
    )

    # Pie/donut specific
    pie_data: list[DataPoint] | None = None

    # Heatmap specific
    heatmap_data: HeatmapData | None = None

    # Chart-specific options
    stacked: bool = False
    show_data_labels: bool = False
    data_label_format: str = Field("{:.1f}", description="Format for data labels")
    show_trend_line: bool = False
    trend_line_type: Literal["linear", "polynomial", "exponential"] = "linear"

    # Interaction plot specific (for ANOVA)
    factor_a_name: str | None = None
    factor_b_name: str | None = None
    show_error_bars: bool = True
    error_bar_type: Literal["se", "sd", "ci"] = "se"
    confidence_level: float = Field(0.95, gt=0, lt=1)

    @model_validator(mode="after")
    def validate_data(self) -> "ChartSpec":
        """Ensure appropriate data is provided for chart type."""
        if self.chart_type in [ChartType.PIE, ChartType.DONUT]:
            if not self.pie_data and not self.series:
                raise ValueError(f"{self.chart_type} requires pie_data or series")
        elif self.chart_type in [ChartType.HEATMAP, ChartType.CONTOUR]:
            if not self.heatmap_data:
                raise ValueError(f"{self.chart_type} requires heatmap_data")
        return self


class TableSpec(RenderSpec):
    """Specification for table rendering.

    Used by DAT for data previews and by PPTX for table shapes.
    """

    data: TableData

    # Header styling
    header_background: str = Field("#4472C4")
    header_font_color: str = Field("#FFFFFF")
    header_font_weight: Literal["normal", "bold"] = "bold"

    # Body styling
    alternate_row_color: str | None = Field("#F2F2F2")
    body_font_color: str = Field("#333333")

    # Border
    border_color: str = Field("#BFBFBF")
    border_width: float = Field(0.5, ge=0.0, le=3.0)

    # Limits
    max_rows: int = Field(100, ge=1, le=10000)
    max_columns: int = Field(50, ge=1, le=500)
    truncation_message: str = Field("... (truncated)")


class TextSpec(RenderSpec):
    """Specification for text/label rendering."""

    text: str = Field(..., description="Text content to render")
    text_type: Literal["title", "subtitle", "label", "annotation", "paragraph"] = "label"

    # Alignment
    horizontal_align: Literal["left", "center", "right"] = "left"
    vertical_align: Literal["top", "middle", "bottom"] = "middle"

    # Text styling (overrides style.label_font if set)
    font: FontConfig | None = None

    # Background
    background_color: str | None = None
    padding: float = Field(0.1, ge=0.0, le=1.0, description="Padding in inches")
    border_color: str | None = None
    border_radius: float = Field(0.0, ge=0.0, le=0.5)


class ImageSpec(RenderSpec):
    """Specification for image rendering/embedding."""

    # Source (exactly one should be set)
    source_path: str | None = Field(None, description="Relative path to image file")
    source_url: str | None = Field(None, description="URL to fetch image from")
    source_base64: str | None = Field(None, description="Base64-encoded image data")

    # Sizing
    fit_mode: Literal["stretch", "contain", "cover", "none"] = "contain"
    maintain_aspect_ratio: bool = True

    # Fallback
    fallback_path: str | None = None
    alt_text: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "ImageSpec":
        """Ensure exactly one source is specified."""
        sources = [
            self.source_path is not None,
            self.source_url is not None,
            self.source_base64 is not None,
        ]
        if sum(sources) == 0:
            raise ValueError("One of source_path, source_url, or source_base64 must be set")
        if sum(sources) > 1:
            raise ValueError("Only one source type can be specified")
        return self


class CompositeSpec(RenderSpec):
    """Specification for composite/multi-panel rendering.

    Used for layouts with multiple charts/tables arranged together.
    """

    specs: list[RenderSpec] = Field(
        ...,
        min_length=1,
        description="Child specs to render",
    )
    layout: Literal["horizontal", "vertical", "grid"] = "grid"
    grid_columns: int = Field(2, ge=1, le=10)
    spacing: float = Field(0.2, ge=0.0, le=1.0, description="Spacing between panels")
    shared_legend: bool = False


# =============================================================================
# Render Results
# =============================================================================


class RenderState(str, Enum):
    """State of a render operation."""

    PENDING = "pending"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RenderedOutput(BaseModel):
    """A single rendered output artifact."""

    target: OutputTarget
    output_path: str | None = Field(None, description="Path to output file")
    output_data: str | None = Field(None, description="Base64 data or JSON string")
    mime_type: str = Field("image/png")
    width_px: int = Field(..., ge=0)
    height_px: int = Field(..., ge=0)
    size_bytes: int = Field(..., ge=0)


class RenderResult(BaseModel):
    """Result of a render operation."""

    spec_id: str
    render_id: str = Field(..., description="Unique render operation ID")
    state: RenderState = RenderState.PENDING

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Outputs
    outputs: list[RenderedOutput] = Field(default_factory=list)

    # Metrics
    render_duration_ms: float = Field(0.0, ge=0.0)

    # Errors
    error_message: str | None = None
    error_details: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if render completed successfully."""
        return self.state == RenderState.COMPLETED and self.error_message is None


# =============================================================================
# Render Requests
# =============================================================================


class RenderRequest(BaseModel):
    """Request to render a spec to one or more outputs."""

    spec: RenderSpec
    outputs: list[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat(target=OutputTarget.PNG)],
    )
    output_path_prefix: str | None = Field(
        None,
        description="Prefix for output file paths",
    )
    style_overrides: RenderStyle | None = None

    # Metadata
    request_id: str | None = None
    source_tool: str | None = None
    job_id: str | None = Field(
        None,
        description="Parent job ID for pipeline tracking",
    )


class BatchRenderRequest(BaseModel):
    """Request to render multiple specs."""

    specs: list[RenderSpec] = Field(..., min_length=1)
    outputs: list[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat(target=OutputTarget.PNG)],
    )
    output_path_prefix: str | None = None
    style_overrides: RenderStyle | None = None

    # Parallelism
    parallel: bool = True
    max_workers: int = Field(4, ge=1, le=16)


class BatchRenderResult(BaseModel):
    """Result of a batch render operation."""

    request_id: str
    state: RenderState = RenderState.PENDING

    # Progress
    total_specs: int = Field(0, ge=0)
    completed_specs: int = Field(0, ge=0)
    failed_specs: int = Field(0, ge=0)

    # Results
    results: list[RenderResult] = Field(default_factory=list)

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: float = Field(0.0, ge=0.0)
