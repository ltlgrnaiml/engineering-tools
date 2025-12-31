"""SOV Visualization contracts - chart and plot specifications.

Per ADR-0025: Visualization contracts define what, not how.
Per ADR-0029: Unified Rendering Engine - SOV contracts extend shared RenderSpec hierarchy.

This module defines SOV-specific visualization contracts that extend
the shared rendering primitives from core/rendering.py. This enables:
- Direct consumption by PPTX Generator without translation
- Consistent styling across all tools
- Shared output target support (PNG, SVG, web, PPTX)

SOV-specific extensions add ANOVA-related plot configurations
(interaction plots, residual plots, etc.) on top of the shared hierarchy.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from shared.contracts.core.rendering import (
    AxisConfig,
    OutputTarget,
    RenderState,
    RenderStyle,
)

__version__ = "0.2.0"


class SOVVisualizationType(str, Enum):
    """SOV-specific visualization types (extends core ChartType)."""

    # ANOVA-specific (not in core)
    INTERACTION_PLOT = "interaction_plot"
    MAIN_EFFECTS_PLOT = "main_effects_plot"
    RESIDUAL_PLOT = "residual_plot"
    NORMAL_PROBABILITY_PLOT = "normal_probability_plot"
    FITTED_VS_RESIDUAL = "fitted_vs_residual"

    # Variance components
    VARIANCE_BAR = "variance_bar"
    VARIANCE_PIE = "variance_pie"
    VARIANCE_STACKED = "variance_stacked"

    # Summary tables (rendered as images)
    ANOVA_TABLE = "anova_table"
    MEANS_TABLE = "means_table"
    POST_HOC_TABLE = "post_hoc_table"


# Re-export from core for backward compatibility
VisualizationType = SOVVisualizationType  # Alias
OutputFormat = OutputTarget  # Map to unified OutputTarget
PlotStyle = RenderStyle  # Use unified RenderStyle


class BoxPlotConfig(BaseModel):
    """Configuration for box plots."""

    # Data
    factor_column: str = Field(..., description="Factor/grouping column")
    response_column: str = Field(..., description="Numeric response column")
    color_by: str | None = Field(
        None,
        description="Optional second factor for coloring",
    )

    # Box options
    show_outliers: bool = True
    outlier_symbol: str = Field("o", description="Marker for outliers")
    show_means: bool = False
    mean_symbol: str = Field("D", description="Marker for means")
    show_notch: bool = False
    box_width: float = Field(0.5, ge=0.1, le=1.0)

    # Points overlay
    show_points: bool = False
    jitter_amount: float = Field(0.1, ge=0.0, le=0.5)
    point_alpha: float = Field(0.5, ge=0.0, le=1.0)

    # Axes
    x_axis: AxisConfig = Field(default_factory=AxisConfig)
    y_axis: AxisConfig = Field(default_factory=AxisConfig)

    # Order
    level_order: list[str] | None = Field(
        None,
        description="Custom order for factor levels",
    )
    sort_by_median: bool = False


class InteractionPlotConfig(BaseModel):
    """Configuration for interaction plots (factor A × factor B)."""

    # Data
    factor_a: str = Field(..., description="First factor (X-axis)")
    factor_b: str = Field(..., description="Second factor (lines)")
    response_column: str = Field(..., description="Numeric response")

    # Plot type
    plot_type: Literal["means", "medians"] = "means"
    show_error_bars: bool = True
    error_bar_type: Literal["se", "sd", "ci"] = "se"
    confidence_level: float = Field(0.95, gt=0, lt=1)

    # Lines
    line_style: Literal["solid", "dashed", "markers_only"] = "solid"
    marker_style: str = Field("o", description="Marker shape")
    marker_size: float = Field(8.0, ge=2.0, le=20.0)

    # Axes
    x_axis: AxisConfig = Field(default_factory=AxisConfig)
    y_axis: AxisConfig = Field(default_factory=AxisConfig)

    # Order
    factor_a_order: list[str] | None = None
    factor_b_order: list[str] | None = None


class MainEffectsPlotConfig(BaseModel):
    """Configuration for main effects plots."""

    # Data
    factors: list[str] = Field(
        ...,
        min_length=1,
        description="Factors to plot main effects for",
    )
    response_column: str

    # Plot type
    plot_type: Literal["means", "medians"] = "means"
    reference_line: Literal["grand_mean", "zero", "none"] = "grand_mean"

    # Error bars
    show_error_bars: bool = True
    error_bar_type: Literal["se", "sd", "ci"] = "se"

    # Layout
    layout: Literal["horizontal", "vertical", "grid"] = "horizontal"
    share_y_axis: bool = True

    # Axes per subplot
    y_axis: AxisConfig = Field(default_factory=AxisConfig)


class VarianceBarConfig(BaseModel):
    """Configuration for variance component bar charts."""

    # Data source
    analysis_id: str | None = Field(
        None,
        description="ANOVA or variance components analysis ID",
    )
    components: list[str] | None = Field(
        None,
        description="Specific components to show (None = all)",
    )

    # Bar options
    orientation: Literal["horizontal", "vertical"] = "horizontal"
    show_values: bool = True
    value_format: str = Field("{:.1f}%", description="Format for value labels")
    sort_by_value: bool = True

    # Colors
    use_gradient: bool = True
    bar_color: str | None = None

    # Reference
    show_total_line: bool = False


class ResidualPlotConfig(BaseModel):
    """Configuration for residual diagnostic plots."""

    # Data source
    analysis_id: str

    # Plot type
    plot_type: Literal[
        "histogram",
        "qq",
        "fitted_vs_residual",
        "residual_vs_factor",
    ] = "histogram"

    # For residual_vs_factor
    factor_column: str | None = None

    # Histogram options
    bins: int = Field(30, ge=5, le=100)
    show_normal_curve: bool = True

    # QQ options
    show_reference_line: bool = True
    show_confidence_band: bool = True

    # Fitted vs residual options
    show_zero_line: bool = True
    show_lowess: bool = False

    # Axes
    x_axis: AxisConfig = Field(default_factory=AxisConfig)
    y_axis: AxisConfig = Field(default_factory=AxisConfig)


class NormalProbabilityPlotConfig(BaseModel):
    """Configuration for normal probability (Q-Q) plots."""

    # Data
    column: str | None = Field(
        None,
        description="Column to plot (if not from analysis residuals)",
    )
    analysis_id: str | None = Field(
        None,
        description="Analysis ID to get residuals from",
    )

    # Reference line
    show_reference_line: bool = True
    reference_line_color: str = Field("#FF0000")

    # Confidence band
    show_confidence_band: bool = True
    confidence_level: float = Field(0.95, gt=0, lt=1)
    band_color: str = Field("#CCCCCC")
    band_alpha: float = Field(0.3, ge=0.0, le=1.0)

    # Points
    marker_style: str = Field("o")
    marker_size: float = Field(6.0, ge=2.0, le=20.0)

    # Axes
    x_axis: AxisConfig = Field(
        default_factory=lambda: AxisConfig(label="Theoretical Quantiles")
    )
    y_axis: AxisConfig = Field(
        default_factory=lambda: AxisConfig(label="Sample Quantiles")
    )

    @model_validator(mode="after")
    def validate_data_source(self) -> "NormalProbabilityPlotConfig":
        """Ensure exactly one data source is specified."""
        if self.column is None and self.analysis_id is None:
            raise ValueError("Either column or analysis_id must be specified")
        return self


class VisualizationSpec(BaseModel):
    """Complete specification for a visualization.

    This is the primary contract for requesting a visualization.
    It contains all information needed to render the plot.
    """

    # Identity
    spec_id: str = Field(
        ...,
        description="Unique identifier for this spec",
    )
    name: str = Field(..., description="Human-readable name")
    description: str | None = None

    # Type and configuration
    viz_type: VisualizationType

    # Type-specific config (exactly one should be set based on viz_type)
    box_plot: BoxPlotConfig | None = None
    interaction_plot: InteractionPlotConfig | None = None
    main_effects_plot: MainEffectsPlotConfig | None = None
    variance_bar: VarianceBarConfig | None = None
    residual_plot: ResidualPlotConfig | None = None
    normal_prob_plot: NormalProbabilityPlotConfig | None = None

    # Data source
    dataset_id: str | None = Field(
        None,
        description="Source dataset (if not from analysis)",
    )
    analysis_id: str | None = Field(
        None,
        description="Source analysis (for ANOVA visualizations)",
    )
    filter_expression: str | None = Field(
        None,
        description="Filter expression for data",
    )

    # Output
    output_formats: list[OutputFormat] = Field(
        default=[OutputFormat.PNG],
        min_length=1,
    )
    width: int | None = Field(None, ge=200, le=4096)
    height: int | None = Field(None, ge=200, le=4096)

    # Styling
    style: PlotStyle = Field(default_factory=PlotStyle)
    title: str | None = None
    subtitle: str | None = None

    # Metadata
    created_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_config_matches_type(self) -> "VisualizationSpec":
        """Ensure configuration matches visualization type."""
        type_config_map = {
            VisualizationType.BOX_PLOT: self.box_plot,
            VisualizationType.INTERACTION_PLOT: self.interaction_plot,
            VisualizationType.MAIN_EFFECTS_PLOT: self.main_effects_plot,
            VisualizationType.VARIANCE_BAR: self.variance_bar,
            VisualizationType.VARIANCE_PIE: self.variance_bar,
            VisualizationType.RESIDUAL_PLOT: self.residual_plot,
            VisualizationType.FITTED_VS_RESIDUAL: self.residual_plot,
            VisualizationType.NORMAL_PROBABILITY_PLOT: self.normal_prob_plot,
        }

        expected = type_config_map.get(self.viz_type)
        if self.viz_type in type_config_map and expected is None:
            raise ValueError(f"Missing config for {self.viz_type} visualization")

        return self


class VisualizationRef(BaseModel):
    """Lightweight reference for visualization list responses."""

    spec_id: str
    name: str
    viz_type: VisualizationType
    dataset_id: str | None = None
    analysis_id: str | None = None
    created_at: datetime | None = None


class RenderState(str, Enum):
    """State of a visualization render operation."""

    PENDING = "pending"
    LOADING_DATA = "loading_data"
    RENDERING = "rendering"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderedOutput(BaseModel):
    """A single rendered output file."""

    format: OutputFormat
    output_path: str = Field(..., description="Relative path to output file")
    size_bytes: int = Field(..., ge=0)
    width_px: int = Field(..., ge=0)
    height_px: int = Field(..., ge=0)


class VisualizationResult(BaseModel):
    """Result of rendering a visualization."""

    # Request tracking
    spec_id: str
    render_id: str = Field(..., description="Unique render operation ID")

    # State
    state: RenderState = RenderState.PENDING
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Outputs
    outputs: list[RenderedOutput] = Field(default_factory=list)

    # Metrics
    render_duration_ms: float = Field(0.0, ge=0.0)
    data_points_plotted: int = Field(0, ge=0)

    # Errors
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if render completed successfully."""
        return self.state == RenderState.COMPLETED and self.error_message is None


class CreateVisualizationRequest(BaseModel):
    """Request to create a new visualization spec."""

    name: str
    viz_type: VisualizationType
    dataset_id: str | None = None
    analysis_id: str | None = None
    description: str | None = None

    # Config (one should be set based on type)
    box_plot: BoxPlotConfig | None = None
    interaction_plot: InteractionPlotConfig | None = None
    main_effects_plot: MainEffectsPlotConfig | None = None
    variance_bar: VarianceBarConfig | None = None
    residual_plot: ResidualPlotConfig | None = None
    normal_prob_plot: NormalProbabilityPlotConfig | None = None

    # Output preferences
    output_formats: list[OutputFormat] = Field(default=[OutputFormat.PNG])
    width: int | None = None
    height: int | None = None

    # Styling
    style: PlotStyle | None = None
    title: str | None = None

    # Auto-render
    auto_render: bool = Field(
        False,
        description="Immediately render after creation",
    )


class RenderVisualizationRequest(BaseModel):
    """Request to render an existing visualization spec."""

    spec_id: str
    output_formats: list[OutputFormat] | None = Field(
        None,
        description="Override spec output formats",
    )
    output_path_prefix: str | None = Field(
        None,
        description="Custom output path prefix",
    )
    width: int | None = None
    height: int | None = None
    style_overrides: PlotStyle | None = None
