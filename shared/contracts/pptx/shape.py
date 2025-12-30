"""PPTX Shape contracts - shape discovery and data binding.

Per ADR-0019: Shapes are discovered from templates automatically.
Per ADR-0020: Guided workflow assists binding configuration.
Per ADR-0022: Renderer architecture handles shape-specific rendering.
Per ADR-0029: Unified Rendering Engine - PPTX uses shared RenderSpec contracts.

This module defines PPTX-specific contracts for:
- Shape discovery (what shapes exist in a template)
- Shape bindings (how data maps to shapes)
- PPTX-specific rendering configurations

Chart and table rendering configurations extend the shared contracts
from core/rendering.py for cross-tool compatibility.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.contracts.core.rendering import (
    AxisConfig,
    ChartSpec,
    ChartType,
    ColorPalette,
    DataSeries,
    HeatmapData,
    OutputTarget,
    RenderResult,
    RenderSpec,
    RenderState,
    RenderStyle,
    TableData,
    TableSpec,
)

__version__ = "0.2.0"


class ShapeType(str, Enum):
    """Types of shapes that can be bound to data."""

    TEXT = "text"  # Text placeholder or text box
    TABLE = "table"  # Table shape
    CHART = "chart"  # Chart shape (bar, line, pie, etc.)
    IMAGE = "image"  # Picture placeholder
    SHAPE = "shape"  # Generic shape (for formatting)
    GROUP = "group"  # Group of shapes
    SMART_ART = "smart_art"  # SmartArt diagram
    UNKNOWN = "unknown"  # Unrecognized shape type


# Re-export ChartType from core for backward compatibility
# ChartType is now imported from shared.contracts.core.rendering


class DataBindingType(str, Enum):
    """How data is bound to a shape."""

    DIRECT = "direct"  # Single value binding
    COLUMN = "column"  # Bind to a DataFrame column
    ROW = "row"  # Bind to a DataFrame row
    AGGREGATE = "aggregate"  # Aggregate function result
    EXPRESSION = "expression"  # Computed expression
    TEMPLATE = "template"  # String template with placeholders
    STATIC = "static"  # Static value (no data binding)


class ShapePosition(BaseModel):
    """Position and size of a shape in EMUs (English Metric Units)."""

    left: int = Field(..., description="Left position in EMUs")
    top: int = Field(..., description="Top position in EMUs")
    width: int = Field(..., description="Width in EMUs")
    height: int = Field(..., description="Height in EMUs")

    @property
    def left_inches(self) -> float:
        """Convert left position to inches."""
        return self.left / 914400

    @property
    def top_inches(self) -> float:
        """Convert top position to inches."""
        return self.top / 914400

    @property
    def width_inches(self) -> float:
        """Convert width to inches."""
        return self.width / 914400

    @property
    def height_inches(self) -> float:
        """Convert height to inches."""
        return self.height / 914400


class ShapePlaceholder(BaseModel):
    """A discovered placeholder in a slide layout.

    Placeholders are special shapes that indicate where content
    should be inserted (title, content, footer, etc.).
    """

    placeholder_id: int = Field(..., description="PowerPoint placeholder ID")
    placeholder_type: str = Field(
        ...,
        description="Placeholder type (TITLE, BODY, PICTURE, etc.)",
    )
    name: str = Field(..., description="Shape name in PowerPoint")
    idx: int | None = Field(None, description="Placeholder index")

    # Position
    position: ShapePosition | None = None

    # Content hints
    has_text_frame: bool = False
    has_table: bool = False
    has_chart: bool = False

    # Current content (for preview)
    current_text: str | None = None


class DiscoveredShape(BaseModel):
    """A shape discovered during template analysis.

    Contains all information needed to configure data binding.
    """

    shape_id: int = Field(..., description="Unique shape ID within slide")
    shape_name: str = Field(..., description="Shape name in PowerPoint")
    shape_type: ShapeType

    # Position and size
    position: ShapePosition

    # Placeholder info (if this shape is a placeholder)
    is_placeholder: bool = False
    placeholder: ShapePlaceholder | None = None

    # Type-specific info
    chart_type: ChartType | None = None
    table_rows: int | None = Field(None, ge=0)
    table_cols: int | None = Field(None, ge=0)

    # Current content
    current_text: str | None = None
    has_text_frame: bool = False

    # Hierarchy
    parent_group_id: int | None = None
    child_shape_ids: list[int] = Field(default_factory=list)


class ShapeDiscoveryResult(BaseModel):
    """Result of discovering shapes in a template.

    This is the hand-off contract from template analysis to
    the guided binding configuration workflow.
    """

    template_id: str
    template_path: str
    discovery_timestamp: datetime

    # Slide-level discovery
    slide_count: int = Field(0, ge=0)
    layout_count: int = Field(0, ge=0)

    # Shape counts by type
    total_shapes: int = Field(0, ge=0)
    text_shapes: int = Field(0, ge=0)
    table_shapes: int = Field(0, ge=0)
    chart_shapes: int = Field(0, ge=0)
    image_shapes: int = Field(0, ge=0)
    other_shapes: int = Field(0, ge=0)

    # Discovered shapes per slide (slide_index -> shapes)
    shapes_by_slide: dict[int, list[DiscoveredShape]] = Field(default_factory=dict)

    # Placeholders per layout (layout_name -> placeholders)
    placeholders_by_layout: dict[str, list[ShapePlaceholder]] = Field(
        default_factory=dict
    )

    # Discovery metrics
    discovery_duration_ms: float = Field(0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TextConfig(BaseModel):
    """Configuration for text shape rendering."""

    # Data binding
    binding_type: DataBindingType = DataBindingType.DIRECT
    source_column: str | None = Field(
        None,
        description="Column name for COLUMN binding type",
    )
    source_expression: str | None = Field(
        None,
        description="Expression for EXPRESSION binding type",
    )
    template_string: str | None = Field(
        None,
        description="Template string with {column} placeholders",
    )
    static_value: str | None = Field(
        None,
        description="Static text for STATIC binding type",
    )
    aggregate_function: str | None = Field(
        None,
        description="Aggregation function (sum, mean, count, etc.)",
    )

    # Formatting
    font_name: str | None = None
    font_size: float | None = Field(None, ge=1.0, le=200.0)
    font_bold: bool | None = None
    font_italic: bool | None = None
    font_color: str | None = Field(
        None,
        description="Hex color code (e.g., '#FF0000')",
    )
    alignment: Literal["left", "center", "right", "justify"] | None = None

    # Number formatting
    number_format: str | None = Field(
        None,
        description="Python format string (e.g., '{:.2f}', '{:,.0f}')",
    )
    prefix: str | None = None
    suffix: str | None = None

    @model_validator(mode="after")
    def validate_binding_config(self) -> "TextConfig":
        """Ensure binding configuration is complete."""
        if self.binding_type == DataBindingType.COLUMN and not self.source_column:
            raise ValueError("source_column required for COLUMN binding")
        if self.binding_type == DataBindingType.EXPRESSION and not self.source_expression:
            raise ValueError("source_expression required for EXPRESSION binding")
        if self.binding_type == DataBindingType.TEMPLATE and not self.template_string:
            raise ValueError("template_string required for TEMPLATE binding")
        if self.binding_type == DataBindingType.STATIC and not self.static_value:
            raise ValueError("static_value required for STATIC binding")
        if self.binding_type == DataBindingType.AGGREGATE and not self.aggregate_function:
            raise ValueError("aggregate_function required for AGGREGATE binding")
        return self


class TableConfig(BaseModel):
    """Configuration for table shape rendering."""

    # Data binding
    source_columns: list[str] = Field(
        ...,
        min_length=1,
        description="Columns to include in table",
    )
    header_row: bool = Field(True, description="Include header row")
    header_labels: list[str] | None = Field(
        None,
        description="Custom header labels (default: column names)",
    )

    # Filtering and sorting
    filter_expression: str | None = None
    sort_by: list[str] = Field(default_factory=list)
    sort_ascending: bool = True
    limit_rows: int | None = Field(None, ge=1, le=1000)

    # Formatting
    column_widths: list[float] | None = Field(
        None,
        description="Column widths in inches",
    )
    row_height: float | None = Field(None, ge=0.1, le=5.0)
    font_size: float = Field(10.0, ge=6.0, le=24.0)

    # Number formatting per column
    column_formats: dict[str, str] = Field(
        default_factory=dict,
        description="Column name -> format string",
    )

    # Styling
    header_fill_color: str | None = None
    alternate_row_color: str | None = None
    border_color: str | None = None

    @model_validator(mode="after")
    def validate_header_labels(self) -> "TableConfig":
        """Ensure header labels match column count if specified."""
        if self.header_labels and len(self.header_labels) != len(self.source_columns):
            raise ValueError(
                f"header_labels count ({len(self.header_labels)}) must match "
                f"source_columns count ({len(self.source_columns)})"
            )
        return self


class ChartSeriesConfig(BaseModel):
    """Configuration for a single chart series."""

    name: str = Field(..., description="Series name (shown in legend)")
    y_column: str = Field(..., description="Column for Y values")
    x_column: str | None = Field(None, description="Column for X values (optional)")
    color: str | None = Field(None, description="Series color (hex)")
    marker_style: str | None = None
    line_style: str | None = None


class ChartConfig(BaseModel):
    """Configuration for chart shape rendering."""

    chart_type: ChartType = ChartType.COLUMN

    # Data binding
    series: list[ChartSeriesConfig] = Field(
        ...,
        min_length=1,
        description="Chart series configurations",
    )
    category_column: str | None = Field(
        None,
        description="Column for category labels (X-axis)",
    )

    # Filtering
    filter_expression: str | None = None
    limit_points: int | None = Field(None, ge=1, le=10000)

    # Titles
    chart_title: str | None = None
    x_axis_title: str | None = None
    y_axis_title: str | None = None

    # Legend
    show_legend: bool = True
    legend_position: Literal["right", "left", "top", "bottom"] = "right"

    # Axis configuration
    y_axis_min: float | None = None
    y_axis_max: float | None = None
    y_axis_format: str | None = None
    x_axis_format: str | None = None

    # Grid
    show_gridlines: bool = True
    gridline_color: str | None = None

    # Data labels
    show_data_labels: bool = False
    data_label_format: str | None = None


class ImageConfig(BaseModel):
    """Configuration for image shape rendering."""

    # Source options (one must be set)
    source_path: str | None = Field(
        None,
        description="Relative path to image file",
    )
    source_column: str | None = Field(
        None,
        description="Column containing image paths",
    )
    source_url: str | None = Field(
        None,
        description="URL to fetch image from",
    )
    chart_render: ChartConfig | None = Field(
        None,
        description="Render chart as image",
    )

    # Sizing
    fit_mode: Literal["stretch", "contain", "cover", "none"] = "contain"
    maintain_aspect_ratio: bool = True

    # Quality
    max_width_px: int = Field(1920, ge=100, le=4096)
    max_height_px: int = Field(1080, ge=100, le=4096)
    quality: int = Field(85, ge=1, le=100)

    # Fallback
    fallback_path: str | None = Field(
        None,
        description="Image to use if source fails",
    )

    @model_validator(mode="after")
    def validate_source(self) -> "ImageConfig":
        """Ensure exactly one source is specified."""
        sources = [
            self.source_path is not None,
            self.source_column is not None,
            self.source_url is not None,
            self.chart_render is not None,
        ]
        if sum(sources) == 0:
            raise ValueError("One of source_path, source_column, source_url, or chart_render must be set")
        if sum(sources) > 1:
            raise ValueError("Only one source type can be specified")
        return self


class ShapeBinding(BaseModel):
    """Complete binding configuration for a shape.

    This is the primary contract for configuring how data
    flows from datasets to shapes in the rendered output.
    """

    # Identity
    binding_id: str = Field(
        ...,
        description="Unique identifier for this binding",
    )
    shape_name: str = Field(..., description="Target shape name")
    slide_index: int = Field(..., ge=0, description="Target slide index")

    # Shape type determines which config is used
    shape_type: ShapeType

    # Type-specific configuration (exactly one should be set)
    text_config: TextConfig | None = None
    table_config: TableConfig | None = None
    chart_config: ChartConfig | None = None
    image_config: ImageConfig | None = None

    # Data source
    dataset_id: str | None = Field(
        None,
        description="Source dataset (if not using default)",
    )
    row_filter: str | None = Field(
        None,
        description="Row filter expression",
    )
    row_index: int | None = Field(
        None,
        ge=0,
        description="Specific row index to use",
    )

    # Conditional rendering
    condition: str | None = Field(
        None,
        description="Render only if this expression is truthy",
    )

    # Metadata
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_config_matches_type(self) -> "ShapeBinding":
        """Ensure configuration matches shape type."""
        type_config_map = {
            ShapeType.TEXT: self.text_config,
            ShapeType.TABLE: self.table_config,
            ShapeType.CHART: self.chart_config,
            ShapeType.IMAGE: self.image_config,
        }

        expected = type_config_map.get(self.shape_type)
        if self.shape_type in type_config_map and expected is None:
            raise ValueError(f"Missing {self.shape_type.value}_config for {self.shape_type} shape")

        return self


class ShapeBindingRef(BaseModel):
    """Lightweight reference to a shape binding."""

    binding_id: str
    shape_name: str
    slide_index: int
    shape_type: ShapeType
    dataset_id: str | None = None


class CreateBindingRequest(BaseModel):
    """Request to create a new shape binding."""

    template_id: str
    shape_name: str
    slide_index: int
    shape_type: ShapeType
    text_config: TextConfig | None = None
    table_config: TableConfig | None = None
    chart_config: ChartConfig | None = None
    image_config: ImageConfig | None = None
    dataset_id: str | None = None
    description: str | None = None


class UpdateBindingRequest(BaseModel):
    """Request to update an existing binding."""

    text_config: TextConfig | None = None
    table_config: TableConfig | None = None
    chart_config: ChartConfig | None = None
    image_config: ImageConfig | None = None
    dataset_id: str | None = None
    condition: str | None = None
    description: str | None = None
