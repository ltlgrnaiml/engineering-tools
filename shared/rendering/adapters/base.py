"""Base Output Adapter for the Unified Rendering Engine.

Per ADR-0029: Output Target Adapters.

This module defines the abstract base class for all output adapters.
Concrete adapters (PNG, SVG, PPTX, etc.) inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any

from shared.contracts.core.rendering import (
    ChartSpec,
    ChartType,
    OutputFormat,
    OutputTarget,
    RenderedOutput,
    RenderSpec,
    RenderStyle,
    TableSpec,
    TextSpec,
    ImageSpec,
)

__version__ = "0.1.0"


class BaseOutputAdapter(ABC):
    """Abstract base class for output adapters.

    Per ADR-0029: All renderers implement this interface.
    Each adapter is responsible for:
    1. Receiving a RenderSpec
    2. Applying styles
    3. Producing output in its target format

    Concrete implementations:
    - PNGAdapter: Renders to PNG via matplotlib
    - SVGAdapter: Renders to SVG via matplotlib
    - JSONAdapter: Outputs chart data as JSON for frontend
    - PPTXAdapter: Creates native PowerPoint charts
    """

    @property
    @abstractmethod
    def target(self) -> OutputTarget:
        """Return the output target this adapter handles."""
        ...

    @property
    def supported_spec_types(self) -> list[type]:
        """Return list of RenderSpec types this adapter supports.

        Override in subclasses to limit supported spec types.
        Default: supports all spec types.
        """
        return [ChartSpec, TableSpec, TextSpec, ImageSpec]

    @abstractmethod
    async def render(
        self,
        spec: RenderSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render a spec to the target format.

        Args:
            spec: The render specification.
            style: Effective style to apply.
            output_format: Output format configuration.
            output_path: Path prefix for output file.

        Returns:
            RenderedOutput with file path or data.
        """
        ...

    def can_render(self, spec: RenderSpec) -> bool:
        """Check if this adapter can render the given spec.

        Args:
            spec: The render specification to check.

        Returns:
            True if this adapter can handle the spec.
        """
        return type(spec) in self.supported_spec_types

    async def render_chart(
        self,
        spec: ChartSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render a chart spec. Override in subclasses.

        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support chart rendering"
        )

    async def render_table(
        self,
        spec: TableSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render a table spec. Override in subclasses.

        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support table rendering"
        )

    async def render_text(
        self,
        spec: TextSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render a text spec. Override in subclasses.

        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support text rendering"
        )

    async def render_image(
        self,
        spec: ImageSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render/process an image spec. Override in subclasses.

        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support image rendering"
        )


class MatplotlibAdapterMixin:
    """Mixin providing matplotlib-based chart rendering utilities.

    Used by PNG and SVG adapters that share matplotlib backend.
    """

    def _get_color_palette(self, style: RenderStyle) -> list[str]:
        """Get color palette from style.

        Returns custom colors if set, otherwise palette defaults.
        """
        if style.custom_colors:
            return style.custom_colors

        # Default color palettes
        palettes = {
            "default": ["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5"],
            "colorblind_safe": ["#0072B2", "#E69F00", "#56B4E9", "#009E73", "#F0E442"],
            "grayscale": ["#333333", "#666666", "#999999", "#CCCCCC", "#EEEEEE"],
            "categorical": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        }

        return palettes.get(style.palette.value, palettes["default"])

    def _apply_style_to_figure(
        self,
        fig: Any,
        ax: Any,
        style: RenderStyle,
    ) -> None:
        """Apply RenderStyle to matplotlib figure and axes.

        Args:
            fig: matplotlib Figure object
            ax: matplotlib Axes object
            style: RenderStyle to apply
        """
        # Background colors
        fig.patch.set_facecolor(style.background_color)
        ax.set_facecolor(style.background_color)

        # Grid
        if style.grid.show:
            ax.grid(
                True,
                color=style.grid.color,
                linestyle={"solid": "-", "dashed": "--", "dotted": ":"}[style.grid.style],
                alpha=style.grid.alpha,
                axis="both" if style.grid.x_axis and style.grid.y_axis else
                     "x" if style.grid.x_axis else "y",
            )
        else:
            ax.grid(False)

        # Tick fonts
        ax.tick_params(
            axis="both",
            labelsize=style.tick_font.size,
            colors=style.tick_font.color,
        )

    def _get_chart_type_kwargs(self, chart_type: ChartType) -> dict[str, Any]:
        """Get matplotlib kwargs for chart type."""
        type_configs = {
            ChartType.BAR: {"kind": "bar"},
            ChartType.LINE: {"kind": "line", "marker": "o"},
            ChartType.SCATTER: {"kind": "scatter"},
            ChartType.AREA: {"kind": "area", "alpha": 0.5},
            ChartType.BOX: {"kind": "box"},
            ChartType.HISTOGRAM: {"kind": "hist"},
        }
        return type_configs.get(chart_type, {})
