"""JSON Output Adapter for the Unified Rendering Engine.

Per ADR-0028: Output Target Adapters.

This adapter outputs render specs as JSON data suitable for
frontend charting libraries (Chart.js, Recharts, ECharts, etc.).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

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
    DataSeries,
)
from shared.rendering.adapters.base import BaseOutputAdapter

__version__ = "0.1.0"


class JSONAdapter(BaseOutputAdapter):
    """Adapter that outputs chart data as JSON for frontend libraries.

    This adapter transforms RenderSpecs into JSON structures that can be
    consumed by frontend charting libraries like Chart.js or Recharts.

    Output format is designed to be library-agnostic while providing
    all necessary data for rendering.
    """

    @property
    def target(self) -> OutputTarget:
        return OutputTarget.WEB_JSON

    async def render(
        self,
        spec: RenderSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render spec to JSON format.

        Args:
            spec: The render specification.
            style: Effective style to apply.
            output_format: Output format configuration.
            output_path: Path prefix for output file.

        Returns:
            RenderedOutput with JSON data.
        """
        if isinstance(spec, ChartSpec):
            return await self.render_chart(spec, style, output_format, output_path)
        elif isinstance(spec, TableSpec):
            return await self.render_table(spec, style, output_format, output_path)
        elif isinstance(spec, TextSpec):
            return await self.render_text(spec, style, output_format, output_path)
        elif isinstance(spec, ImageSpec):
            return await self.render_image(spec, style, output_format, output_path)
        else:
            raise ValueError(f"Unsupported spec type: {type(spec)}")

    async def render_chart(
        self,
        spec: ChartSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render chart spec to JSON.

        Returns JSON structure suitable for frontend charting libraries.
        """
        output_id = str(uuid4())[:8]

        # Build chart data structure
        chart_data = self._build_chart_data(spec, style)

        # Write to file if path provided
        file_path = None
        if output_path:
            file_path = Path(output_path) / f"{spec.spec_id}_{output_id}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(chart_data, f, indent=2, default=str)

        return RenderedOutput(
            output_id=output_id,
            target=OutputTarget.WEB_JSON,
            file_path=str(file_path) if file_path else None,
            data=chart_data,
            width_px=output_format.width_px,
            height_px=output_format.height_px,
            created_at=datetime.now(timezone.utc).replace(microsecond=0),
        )

    def _build_chart_data(
        self,
        spec: ChartSpec,
        style: RenderStyle,
    ) -> dict[str, Any]:
        """Build JSON chart data from spec and style."""
        # Map chart type to library-agnostic type name
        type_map = {
            ChartType.BAR: "bar",
            ChartType.LINE: "line",
            ChartType.SCATTER: "scatter",
            ChartType.PIE: "pie",
            ChartType.AREA: "area",
            ChartType.HEATMAP: "heatmap",
            ChartType.BOX: "boxplot",
            ChartType.HISTOGRAM: "histogram",
            ChartType.WATERFALL: "waterfall",
            ChartType.COMBO: "combo",
        }

        # Build datasets from series
        datasets = []
        for series in spec.series:
            dataset = self._series_to_dataset(series, style)
            datasets.append(dataset)

        # Build chart configuration
        chart_config = {
            "type": type_map.get(spec.chart_type, "bar"),
            "spec_id": spec.spec_id,
            "title": spec.title,
            "subtitle": spec.subtitle,
            "data": {
                "labels": spec.x_axis.categories if spec.x_axis and spec.x_axis.categories else [],
                "datasets": datasets,
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": True,
                "plugins": {
                    "title": {
                        "display": bool(spec.title),
                        "text": spec.title or "",
                        "font": {
                            "family": style.title_font.family,
                            "size": style.title_font.size,
                            "weight": "bold" if style.title_font.bold else "normal",
                        },
                        "color": style.title_font.color,
                    },
                    "subtitle": {
                        "display": bool(spec.subtitle),
                        "text": spec.subtitle or "",
                    },
                    "legend": {
                        "display": spec.show_legend,
                        "position": spec.legend_position or "top",
                    },
                },
                "scales": self._build_scales(spec, style),
            },
            "style": {
                "backgroundColor": style.background_color,
                "palette": style.palette.value,
                "colors": style.custom_colors or self._get_default_colors(style),
            },
            "dimensions": {
                "width": spec.width_px,
                "height": spec.height_px,
            },
        }

        return chart_config

    def _series_to_dataset(
        self,
        series: DataSeries,
        style: RenderStyle,
    ) -> dict[str, Any]:
        """Convert DataSeries to JSON dataset."""
        colors = style.custom_colors or self._get_default_colors(style)
        color_index = 0  # Would typically track index across series

        return {
            "label": series.name,
            "data": series.values,
            "backgroundColor": series.color or colors[color_index % len(colors)],
            "borderColor": series.color or colors[color_index % len(colors)],
            "borderWidth": 1,
            "fill": series.fill if hasattr(series, "fill") else False,
            "tension": 0.1,  # For line charts
            "metadata": series.metadata,
        }

    def _build_scales(
        self,
        spec: ChartSpec,
        style: RenderStyle,
    ) -> dict[str, Any]:
        """Build scales configuration from spec."""
        scales = {}

        if spec.x_axis:
            scales["x"] = {
                "title": {
                    "display": bool(spec.x_axis.title),
                    "text": spec.x_axis.title or "",
                    "font": {
                        "family": style.axis_font.family,
                        "size": style.axis_font.size,
                    },
                },
                "grid": {
                    "display": style.grid.show and style.grid.x_axis,
                    "color": style.grid.color,
                },
                "ticks": {
                    "font": {
                        "family": style.tick_font.family,
                        "size": style.tick_font.size,
                    },
                },
            }

        if spec.y_axis:
            scales["y"] = {
                "title": {
                    "display": bool(spec.y_axis.title),
                    "text": spec.y_axis.title or "",
                    "font": {
                        "family": style.axis_font.family,
                        "size": style.axis_font.size,
                    },
                },
                "grid": {
                    "display": style.grid.show and style.grid.y_axis,
                    "color": style.grid.color,
                },
                "ticks": {
                    "font": {
                        "family": style.tick_font.family,
                        "size": style.tick_font.size,
                    },
                },
                "min": spec.y_axis.min_value,
                "max": spec.y_axis.max_value,
            }

        return scales

    def _get_default_colors(self, style: RenderStyle) -> list[str]:
        """Get default color palette."""
        palettes = {
            "default": ["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5"],
            "colorblind_safe": ["#0072B2", "#E69F00", "#56B4E9", "#009E73", "#F0E442"],
            "grayscale": ["#333333", "#666666", "#999999", "#CCCCCC", "#EEEEEE"],
            "categorical": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        }
        return palettes.get(style.palette.value, palettes["default"])

    async def render_table(
        self,
        spec: TableSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render table spec to JSON."""
        output_id = str(uuid4())[:8]

        table_data = {
            "type": "table",
            "spec_id": spec.spec_id,
            "title": spec.title,
            "columns": [col.model_dump() for col in spec.columns],
            "rows": spec.rows,
            "style": {
                "headerStyle": spec.header_style.model_dump() if spec.header_style else None,
                "rowStyle": spec.row_style.model_dump() if spec.row_style else None,
                "alternateRowColors": spec.alternate_row_colors,
            },
            "options": {
                "showRowNumbers": spec.show_row_numbers,
                "sortable": spec.sortable,
                "filterable": spec.filterable,
            },
        }

        file_path = None
        if output_path:
            file_path = Path(output_path) / f"{spec.spec_id}_{output_id}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=2, default=str)

        return RenderedOutput(
            output_id=output_id,
            target=OutputTarget.WEB_JSON,
            file_path=str(file_path) if file_path else None,
            data=table_data,
            created_at=datetime.now(timezone.utc).replace(microsecond=0),
        )

    async def render_text(
        self,
        spec: TextSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render text spec to JSON."""
        output_id = str(uuid4())[:8]

        text_data = {
            "type": "text",
            "spec_id": spec.spec_id,
            "content": spec.content,
            "format": spec.text_format.value if spec.text_format else "plain",
            "style": {
                "font": style.title_font.model_dump(),
                "alignment": spec.alignment.value if spec.alignment else "left",
            },
        }

        return RenderedOutput(
            output_id=output_id,
            target=OutputTarget.WEB_JSON,
            data=text_data,
            created_at=datetime.now(timezone.utc).replace(microsecond=0),
        )

    async def render_image(
        self,
        spec: ImageSpec,
        style: RenderStyle,
        output_format: OutputFormat,
        output_path: str,
    ) -> RenderedOutput:
        """Render image spec to JSON (returns metadata)."""
        output_id = str(uuid4())[:8]

        image_data = {
            "type": "image",
            "spec_id": spec.spec_id,
            "source": spec.source,
            "alt_text": spec.alt_text,
            "dimensions": {
                "width": spec.width_px,
                "height": spec.height_px,
            },
            "fit": spec.fit.value if spec.fit else "contain",
        }

        return RenderedOutput(
            output_id=output_id,
            target=OutputTarget.WEB_JSON,
            data=image_data,
            created_at=datetime.now(timezone.utc).replace(microsecond=0),
        )
