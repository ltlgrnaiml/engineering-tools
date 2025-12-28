"""Plot renderer for generating and inserting visualizations.

Per ADR-0028: Renderers consume shared RenderSpec contracts.
"""

import io
import logging
from typing import Any
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shared.contracts.core.rendering import (
    ChartSpec,
    ChartType,
    DataSeries,
    HeatmapData,
)

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext

logger = logging.getLogger(__name__)


class PlotRenderer(BaseRenderer):
    """Renderer for plot shapes that generate and insert visualizations."""

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is a plot shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is a plot type.
        """
        plot_types = ["contour", "box", "scatter", "line", "bar", "hist", "heatmap", "stacked"]
        return parsed_name.renderer in plot_types

    async def render(self, context: RenderContext) -> None:
        """Render plot into shape.

        Args:
            context: Rendering context.
        """
        shape = context.shape
        parsed_name = context.parsed_name
        data = context.data

        self.logger.info(f"[PLOT] Starting render for {shape.name}")
        self.logger.info(f"[PLOT] Input data shape: {data.shape}")
        self.logger.info(f"[PLOT] Input data columns: {list(data.columns)}")
        self.logger.info(f"[PLOT] Renderer: {parsed_name.renderer}, Filters: {parsed_name.filters}")

        # Filter data based on filters
        filtered_data = self.filter_data(data, parsed_name)

        if filtered_data.empty:
            self.logger.error(f"[PLOT] CRITICAL: Filtered data is EMPTY for {shape.name}")
            self.logger.error(f"[PLOT] Original data had {len(data)} rows")
            self.logger.error(f"[PLOT] Filter parameters: {parsed_name.filters}")
            return

        self.logger.info(f"[PLOT] Filtered data: {len(filtered_data)} rows for {shape.name}")
        self.logger.info(f"[PLOT] Filtered data columns: {list(filtered_data.columns)}")
        self.logger.info(f"[PLOT] Filtered data sample:\n{filtered_data.head()}")

        # Get metrics to plot
        metrics = self._get_metrics(parsed_name, filtered_data)

        if not metrics:
            self.logger.error(f"[PLOT] CRITICAL: No metrics found for plot {shape.name}")
            self.logger.error(f"[PLOT] Available columns: {list(filtered_data.columns)}")
            self.logger.error(f"[PLOT] Requested metrics: {parsed_name.data}")
            return

        self.logger.info(f"[PLOT] Metrics to plot: {metrics} for {shape.name}")
        # Verify metrics exist in data
        for metric in metrics:
            if metric in filtered_data.columns:
                self.logger.info(
                    f"[PLOT] Metric '{metric}' found with {filtered_data[metric].notna().sum()} non-null values"
                )
            else:
                self.logger.error(f"[PLOT] CRITICAL: Metric '{metric}' NOT FOUND in filtered data!")

        # Generate plot based on renderer type
        plot_type = parsed_name.renderer
        self.logger.info(f"[PLOT] Generating {plot_type} plot for {shape.name}")

        image_stream = self._generate_plot(
            filtered_data,
            metrics,
            plot_type,
            parsed_name,
        )

        if image_stream:
            self.logger.info(
                f"[PLOT] Plot generated successfully, stream size: {image_stream.getbuffer().nbytes} bytes"
            )
            self.logger.info(f"[PLOT] Inserting image for {shape.name}")
            # Insert image into shape
            self._insert_image(shape, image_stream)
            self.logger.info(f"[PLOT] Successfully rendered {plot_type} plot into {shape.name}")
        else:
            self.logger.error(f"[PLOT] CRITICAL: Failed to generate plot for {shape.name}")
            self.logger.error(
                f"[PLOT] Plot type: {plot_type}, Metrics: {metrics}, Data rows: {len(filtered_data)}"
            )

    def _get_metrics(
        self,
        parsed_name: ParsedShapeNameV2,
        data: pd.DataFrame,
    ) -> list[str]:
        """Get list of metrics to plot.

        Args:
            parsed_name: Parsed shape name.
            data: Data DataFrame.

        Returns:
            List of metric column names (matched from data columns).
        """
        # Get metrics from parsed name data
        metrics = parsed_name.get_metrics()

        if metrics:
            # Case-insensitive matching: map requested metrics to actual column names
            matched_metrics = []
            col_map = {col.lower(): col for col in data.columns}

            for requested_metric in metrics:
                metric_lower = requested_metric.lower()
                if metric_lower in col_map:
                    matched_metrics.append(col_map[metric_lower])
                    self.logger.debug(
                        f"Matched metric '{requested_metric}' -> '{col_map[metric_lower]}'"
                    )
                else:
                    self.logger.warning(f"Metric '{requested_metric}' not found in data columns")

            return matched_metrics

        # Default: use all numeric columns
        return data.select_dtypes(include=["number"]).columns.tolist()[:3]  # Limit to 3

    def _generate_plot(
        self,
        data: pd.DataFrame,
        metrics: list[str],
        plot_type: str,
        parsed_name: ParsedShapeNameV2,
    ) -> io.BytesIO | None:
        """Generate plot image.

        Args:
            data: Data to plot.
            metrics: Metrics to plot.
            plot_type: Type of plot (line, bar, scatter, etc.).
            parsed_name: Parsed shape name for additional parameters.

        Returns:
            BytesIO stream with plot image, or None if failed.
        """
        try:
            # Determine layout for multi-metric plots
            layout_option = parsed_name.get_option("layout", "stack")
            fig, axes = self._create_subplot_layout(metrics, layout_option)

            # Generate plot based on type
            if len(metrics) > 1 and plot_type in ["contour", "heatmap"]:
                # Multi-metric contour/heatmap: create subplots
                for i, metric in enumerate(metrics):
                    ax = axes[i] if isinstance(axes, np.ndarray) else axes
                    if plot_type == "contour":
                        self._plot_contour(ax, data, [metric])
                    elif plot_type == "heatmap":
                        self._plot_heatmap(ax, data, [metric])
                    ax.set_title(f"{metric}")
            else:
                # Single metric or overlay plots
                ax = axes[0] if isinstance(axes, np.ndarray) else axes
                if plot_type == "line":
                    self._plot_line(ax, data, metrics)
                elif plot_type == "bar":
                    self._plot_bar(ax, data, metrics)
                elif plot_type == "scatter":
                    self._plot_scatter(ax, data, metrics)
                elif plot_type == "hist":
                    self._plot_histogram(ax, data, metrics)
                elif plot_type == "box":
                    self._plot_box(ax, data, metrics)
                elif plot_type == "contour":
                    self._plot_contour(ax, data, metrics)
                elif plot_type == "heatmap":
                    self._plot_heatmap(ax, data, metrics)
                else:
                    # Default to line plot
                    self._plot_line(ax, data, metrics)

            # Customize plot
            if isinstance(axes, np.ndarray):
                for ax in axes.flat:
                    self._customize_plot(ax, parsed_name)
            else:
                self._customize_plot(axes, parsed_name)

            # Save to BytesIO
            image_stream = io.BytesIO()
            plt.tight_layout()
            plt.savefig(image_stream, format="png", dpi=self._get_dpi(), bbox_inches="tight")
            plt.close(fig)

            image_stream.seek(0)
            return image_stream

        except Exception as e:
            self.logger.error(f"Failed to generate plot: {e}", exc_info=True)
            return None

    def _create_subplot_layout(self, metrics: list[str], layout_option: str | None) -> tuple:
        """Create subplot layout for multi-metric plots.

        Args:
            metrics: List of metrics to plot.
            layout_option: Layout specification (stack, row, grid, MxN, overlay).

        Returns:
            Tuple of (fig, axes).
        """
        n_metrics = len(metrics)

        if n_metrics == 1:
            fig, ax = plt.subplots(figsize=(8, 6))
            return fig, [ax]

        if layout_option == "overlay":
            fig, ax = plt.subplots(figsize=(8, 6))
            return fig, [ax]

        if layout_option == "stack" or layout_option is None:
            rows, cols = n_metrics, 1
        elif layout_option == "row":
            rows, cols = 1, n_metrics
        elif layout_option == "grid":
            cols = int(np.ceil(np.sqrt(n_metrics)))
            rows = int(np.ceil(n_metrics / cols))
        elif "x" in layout_option:
            try:
                parts = layout_option.split("x")
                rows, cols = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                rows, cols = n_metrics, 1
        else:
            rows, cols = n_metrics, 1

        fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 6 * rows))
        axes = np.atleast_1d(axes).flatten()
        return fig, axes

    def _plot_line(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate line plot."""
        for metric in metrics:
            if metric in data.columns:
                ax.plot(data.index, data[metric], marker="o", label=metric)
        ax.legend()

    def _plot_bar(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate bar plot."""
        x = range(len(data))
        width = 0.8 / len(metrics)

        for i, metric in enumerate(metrics):
            if metric in data.columns:
                offset = width * i - (width * len(metrics) / 2)
                ax.bar([xi + offset for xi in x], data[metric], width, label=metric)

        ax.set_xticks(x)
        ax.legend()

    def _plot_scatter(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate scatter plot."""
        if len(metrics) >= 2:
            ax.scatter(data[metrics[0]], data[metrics[1]], alpha=0.6)
            ax.set_xlabel(metrics[0])
            ax.set_ylabel(metrics[1])
        elif len(metrics) == 1:
            ax.scatter(data.index, data[metrics[0]], alpha=0.6)
            ax.set_ylabel(metrics[0])

    def _plot_histogram(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate histogram."""
        for metric in metrics:
            if metric in data.columns:
                ax.hist(data[metric].dropna(), bins=20, alpha=0.6, label=metric)
        ax.legend()

    def _plot_box(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate box plot."""
        plot_data = [data[m].dropna() for m in metrics if m in data.columns]
        ax.boxplot(plot_data, labels=metrics)

    def _plot_contour(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate contour plot."""
        # For contour, we need X, Y, Z
        # This is a simplified version - may need more sophisticated logic
        self.logger.info(f"[PLOT_CONTOUR] Attempting contour plot with {len(data)} rows")
        self.logger.info(f"[PLOT_CONTOUR] Metrics: {metrics}")
        self.logger.info(
            f"[PLOT_CONTOUR] Has imcol: {'imcol' in data.columns}, Has imrow: {'imrow' in data.columns}"
        )

        if len(metrics) >= 1 and "imcol" in data.columns and "imrow" in data.columns:
            # Pivot data for contour
            try:
                self.logger.info(f"[PLOT_CONTOUR] Pivoting data for metric: {metrics[0]}")
                pivot = data.pivot_table(
                    values=metrics[0], index="imrow", columns="imcol", aggfunc="mean"
                )
                self.logger.info(f"[PLOT_CONTOUR] Pivot shape: {pivot.shape}")
                self.logger.info(f"[PLOT_CONTOUR] Pivot:\n{pivot}")

                X, Y = pivot.columns, pivot.index
                Z = pivot.values

                contour = ax.contourf(X, Y, Z, levels=15, cmap=self._get_colormap())
                plt.colorbar(contour, ax=ax, label=metrics[0])
                ax.set_xlabel("Image Column")
                ax.set_ylabel("Image Row")
                self.logger.info("[PLOT_CONTOUR] Contour plot generated successfully")
            except Exception as e:
                self.logger.error(f"[PLOT_CONTOUR] Contour plot failed: {e}", exc_info=True)
                self.logger.warning("[PLOT_CONTOUR] Falling back to scatter plot")
                self._plot_scatter(ax, data, metrics)
        else:
            self.logger.warning(
                "[PLOT_CONTOUR] Missing required columns for contour, using scatter"
            )
            self.logger.warning(f"[PLOT_CONTOUR] Available columns: {list(data.columns)}")
            # Fallback to scatter
            self._plot_scatter(ax, data, metrics)

    def _plot_heatmap(self, ax: Any, data: pd.DataFrame, metrics: list[str]) -> None:
        """Generate heatmap plot."""
        if len(metrics) >= 1 and "imcol" in data.columns and "imrow" in data.columns:
            try:
                pivot = data.pivot_table(
                    values=metrics[0], index="imrow", columns="imcol", aggfunc="mean"
                )
                im = ax.imshow(pivot.values, cmap=self._get_colormap(), aspect="auto")
                plt.colorbar(im, ax=ax, label=metrics[0])
                ax.set_xlabel("Image Column")
                ax.set_ylabel("Image Row")
            except Exception as e:
                self.logger.error(f"Heatmap plot failed: {e}", exc_info=True)
                self._plot_scatter(ax, data, metrics)
        else:
            self._plot_scatter(ax, data, metrics)

    def _customize_plot(self, ax: Any, parsed_name: ParsedShapeNameV2) -> None:
        """Customize plot appearance.

        Args:
            ax: Matplotlib axes object.
            parsed_name: Parsed shape name with options.
        """
        # Set title if specified in options
        title = parsed_name.get_option("title")
        if title:
            ax.set_title(title)

        # Set axis labels if specified in options
        xlabel = parsed_name.get_option("xlabel")
        if xlabel:
            ax.set_xlabel(xlabel)

        ylabel = parsed_name.get_option("ylabel")
        if ylabel:
            ax.set_ylabel(ylabel)

        # Grid
        ax.grid(True, alpha=0.3)

    def _get_plotting_config(self):
        """Get plotting config from domain config.

        Returns:
            PlottingConfig or None if unavailable.
        """
        try:
            from apps.pptx_generator.backend.core.domain_config_service import get_domain_config
            return get_domain_config().plotting
        except Exception:
            return None

    def _get_dpi(self) -> int:
        """Get figure DPI from config.

        Returns:
            DPI value, defaults to 150.
        """
        config = self._get_plotting_config()
        return config.figure_dpi if config else 150

    def _get_colormap(self) -> str:
        """Get colormap from config.

        Returns:
            Colormap name, defaults to 'viridis'.
        """
        config = self._get_plotting_config()
        return config.colormap if config else "viridis"

    def _get_job_context_color(self, context_value: str) -> str | None:
        """Get color for a job context value.

        Args:
            context_value: Job context value (e.g., 'Left', 'Right').

        Returns:
            Hex color string or None.
        """
        config = self._get_plotting_config()
        if config and config.job_context_colors:
            return config.job_context_colors.get(context_value)
        return None

    def _insert_image(self, shape: Any, image_stream: io.BytesIO) -> None:
        """Insert image into PowerPoint shape.

        Args:
            shape: PowerPoint shape.
            image_stream: BytesIO stream with image data.
        """
        try:
            # Get shape position and size
            left = shape.left
            top = shape.top
            width = shape.width
            height = shape.height
            shape_name = shape.name

            self.logger.info(f"[PLOT_INSERT] Inserting image for {shape_name}")
            self.logger.info(
                f"[PLOT_INSERT] Position: left={left}, top={top}, width={width}, height={height}"
            )
            self.logger.info(
                f"[PLOT_INSERT] Image stream size: {image_stream.getbuffer().nbytes} bytes"
            )

            # Get parent slide shapes collection
            # shape._parent is already the SlideShapes collection
            slide_shapes = shape._parent

            # Remove old shape
            sp = shape.element
            sp.getparent().remove(sp)
            self.logger.info("[PLOT_INSERT] Original shape removed")

            # Add image as picture
            pic = slide_shapes.add_picture(image_stream, left, top, width=width, height=height)
            self.logger.info("[PLOT_INSERT] Picture added to slide")

            # Copy name
            pic.name = shape_name
            self.logger.info(f"[PLOT_INSERT] Shape name restored: {shape_name}")

        except Exception as e:
            self.logger.error(f"[PLOT_INSERT] CRITICAL: Failed to insert image: {e}", exc_info=True)

    def build_chart_spec(
        self,
        data: pd.DataFrame,
        name: str,
        chart_type: str,
        metrics: list[str],
        title: str | None = None,
    ) -> ChartSpec:
        """Build a ChartSpec from DataFrame per ADR-0028.

        This method bridges the PPTX renderer with the shared rendering contract.

        Args:
            data: DataFrame containing data.
            name: Spec name/identifier.
            chart_type: Type of chart (contour, box, scatter, etc.).
            metrics: Metric columns to plot.
            title: Optional chart title.

        Returns:
            ChartSpec conforming to shared rendering contract.
        """
        # Map renderer type to ChartType enum
        type_mapping = {
            "contour": ChartType.CONTOUR,
            "box": ChartType.BOX,
            "scatter": ChartType.SCATTER,
            "line": ChartType.LINE,
            "bar": ChartType.BAR,
            "hist": ChartType.HISTOGRAM,
            "heatmap": ChartType.HEATMAP,
            "stacked": ChartType.STACKED_BAR,
        }
        chart_type_enum = type_mapping.get(chart_type, ChartType.LINE)

        # Build series from data
        series: list[DataSeries] = []
        for metric in metrics:
            if metric in data.columns:
                values = data[metric].dropna().tolist()
                series.append(DataSeries(
                    name=metric,
                    values=values,
                ))

        # Handle heatmap data specially
        heatmap_data = None
        if chart_type_enum in [ChartType.HEATMAP, ChartType.CONTOUR]:
            if len(metrics) >= 1 and metrics[0] in data.columns:
                # Pivot data for heatmap
                try:
                    pivot = data.pivot_table(
                        values=metrics[0],
                        aggfunc="mean",
                    )
                    heatmap_data = HeatmapData(
                        values=pivot.values.tolist(),
                        row_labels=[str(r) for r in pivot.index.tolist()],
                        column_labels=[str(c) for c in pivot.columns.tolist()],
                    )
                except Exception:
                    pass

        return ChartSpec(
            spec_id=f"chart_{uuid4().hex[:8]}",
            name=name,
            title=title,
            chart_type=chart_type_enum,
            series=series,
            heatmap_data=heatmap_data,
            source_tool="pptx",
        )
