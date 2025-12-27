"""Text and KPI renderers for simple value display."""

import logging
from typing import Any

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext

logger = logging.getLogger(__name__)


class TextRenderer(BaseRenderer):
    """Renderer for text shapes that display single values or labels."""

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is a text shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is 'text'.
        """
        return parsed_name.renderer == "text"

    async def render(self, context: RenderContext) -> None:
        """Render text value into shape.

        Args:
            context: Rendering context.
        """
        shape = context.shape

        # Check if shape has text frame
        if not hasattr(shape, "has_text_frame") or not shape.has_text_frame:
            self.logger.warning(f"Shape {shape.name} is not a text shape")
            return

        # Get value from parameters or metadata
        value = self._get_text_value(context)

        if value is not None:
            # Set text
            if shape.text_frame.paragraphs:
                shape.text_frame.paragraphs[0].text = str(value)
            else:
                shape.text = str(value)

            self.logger.debug(f"Rendered text: {value} into {shape.name}")

    def _get_text_value(self, context: RenderContext) -> str | None:
        """Extract text value from context.

        Args:
            context: Rendering context.

        Returns:
            Text value to display.
        """
        parsed_name = context.parsed_name

        # Check for label option
        label = parsed_name.get_option("label")
        if label:
            return label

        # Check for text in data (first element)
        if parsed_name.data:
            return parsed_name.data[0]

        # Check for value in metadata by shape name
        if context.metadata:
            return context.metadata.get(parsed_name.renderer)

        return None


class KPIRenderer(BaseRenderer):
    """Renderer for KPI shapes that display calculated metrics."""

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is a KPI shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is 'kpi'.
        """
        return parsed_name.renderer == "kpi"

    async def render(self, context: RenderContext) -> None:
        """Render KPI value into shape.

        Args:
            context: Rendering context.
        """
        shape = context.shape
        parsed_name = context.parsed_name
        data = context.data

        # Check if shape has text frame
        if not hasattr(shape, "has_text_frame") or not shape.has_text_frame:
            self.logger.warning(f"Shape {shape.name} is not a text shape")
            return

        # Filter data based on parameters
        filtered_data = self.filter_data(data, parsed_name)

        # Calculate KPI value
        value = self._calculate_kpi(filtered_data, parsed_name)

        if value is not None:
            # Format value
            formatted_value = self._format_kpi_value(value, parsed_name)

            # Set text
            if shape.text_frame.paragraphs:
                shape.text_frame.paragraphs[0].text = formatted_value
            else:
                shape.text = formatted_value

            self.logger.debug(f"Rendered KPI: {formatted_value} into {shape.name}")

    def _calculate_kpi(
        self,
        data: Any,
        parsed_name: ParsedShapeNameV2,
    ) -> float | None:
        """Calculate KPI value from data.

        Args:
            data: Filtered data.
            parsed_name: Parsed shape name.

        Returns:
            Calculated KPI value.
        """
        if data.empty:
            return None

        # Get metric name from data (first metric in list)
        if not parsed_name.data:
            return None
        metric = parsed_name.data[0]

        # Case-insensitive column matching
        col_map = {col.lower(): col for col in data.columns}
        metric_lower = metric.lower()

        if metric_lower not in col_map:
            self.logger.warning(f"Metric '{metric}' not found in data columns")
            return None

        # Use actual column name from data
        metric = col_map[metric_lower]

        # Get aggregation function from option
        agg_func = parsed_name.get_option("agg", "mean") or "mean"

        # Calculate
        try:
            if agg_func == "mean":
                return float(data[metric].mean())
            elif agg_func == "sum":
                return float(data[metric].sum())
            elif agg_func == "count":
                return float(data[metric].count())
            elif agg_func == "min":
                return float(data[metric].min())
            elif agg_func == "max":
                return float(data[metric].max())
            else:
                return float(data[metric].mean())
        except Exception as e:
            self.logger.error(f"Failed to calculate KPI: {e}")
            return None

    def _format_kpi_value(
        self,
        value: float,
        parsed_name: ParsedShapeNameV2,
    ) -> str:
        """Format KPI value for display.

        Args:
            value: KPI value.
            parsed_name: Parsed shape name.

        Returns:
            Formatted string.
        """
        # Get format from options
        fmt = parsed_name.get_option("format", ".2f") or ".2f"

        try:
            return f"{value:{fmt}}"
        except Exception:
            return f"{value:.2f}"
