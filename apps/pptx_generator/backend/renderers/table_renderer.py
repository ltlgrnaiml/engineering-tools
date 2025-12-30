"""Table renderer for populating PowerPoint tables with data.

Per ADR-0029: Renderers consume shared RenderSpec contracts.
"""

import logging
from typing import Any
from uuid import uuid4

import pandas as pd
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from shared.contracts.core.rendering import TableSpec, TableData

from apps.pptx_generator.backend.core.domain_config_service import get_domain_config
from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.models.domain_config import TableDefaults
from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext

logger = logging.getLogger(__name__)


class TableRenderer(BaseRenderer):
    """Renderer for table shapes that display tabular data."""

    def __init__(self) -> None:
        """Initialize the table renderer with defaults from config."""
        super().__init__()
        self._defaults: TableDefaults | None = None

    @property
    def defaults(self) -> TableDefaults:
        """Get table defaults from config, with lazy loading."""
        if self._defaults is None:
            try:
                config = get_domain_config()
                self._defaults = config.defaults.tables
            except Exception:
                # Fallback to model defaults if config not available
                self._defaults = TableDefaults()
        return self._defaults

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is a table shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is 'table'.
        """
        return parsed_name.renderer == "table"

    async def render(self, context: RenderContext) -> None:
        """Render data into table shape.

        Args:
            context: Rendering context.
        """
        shape = context.shape
        parsed_name = context.parsed_name
        data = context.data

        # Check if shape has table
        if not hasattr(shape, "has_table") or not shape.has_table:
            self.logger.warning(f"Shape {shape.name} is not a table")
            return

        # Filter and aggregate data
        filtered_data = self.filter_data(data, parsed_name)

        # Get metrics to display
        metrics = self._get_metrics(parsed_name, filtered_data)

        # Get grouping columns
        group_cols = self._get_grouping_columns(parsed_name, filtered_data)

        # Aggregate if needed
        if group_cols:
            table_data = self.aggregate_data(filtered_data, group_cols, metrics, agg_func="mean")
        else:
            table_data = (
                filtered_data[group_cols + metrics] if group_cols else filtered_data[metrics]
            )

        # Populate table with formatting
        self._populate_table(shape.table, table_data, group_cols, metrics)

        # Apply formatting from config
        self._apply_table_formatting(shape.table)

        self.logger.debug(
            f"Rendered table with {len(table_data)} rows, {len(metrics)} metrics into {shape.name}"
        )

    def _get_metrics(
        self,
        parsed_name: ParsedShapeNameV2,
        data: pd.DataFrame,
    ) -> list[str]:
        """Get list of metrics to display in table.

        Args:
            parsed_name: Parsed shape name.
            data: Data DataFrame.

        Returns:
            List of metric column names (matched from data columns).
        """
        # Use metrics from parsed_name.data
        if parsed_name.data:
            metrics = parsed_name.data
            if not isinstance(metrics, list):
                metrics = [metrics]

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
        return data.select_dtypes(include=["number"]).columns.tolist()

    def _get_grouping_columns(
        self,
        parsed_name: ParsedShapeNameV2,
        data: pd.DataFrame,
    ) -> list[str]:
        """Get grouping columns for table rows.

        Args:
            parsed_name: Parsed shape name.
            data: Data DataFrame.

        Returns:
            List of grouping column names.
        """
        # Check for contexts filter
        contexts = parsed_name.get_filter("contexts")
        if contexts:
            if isinstance(contexts, list):
                return [c for c in contexts if c in data.columns]
            else:
                return [contexts] if contexts in data.columns else []

        # Default: no grouping
        return []

    def _populate_table(
        self,
        table: Any,
        data: pd.DataFrame,
        group_cols: list[str],
        metrics: list[str],
    ) -> None:
        """Populate PowerPoint table with data.

        Args:
            table: PowerPoint table object.
            data: Data to populate.
            group_cols: Grouping columns for rows.
            metrics: Metric columns.
        """
        if data.empty:
            self.logger.warning("No data to populate table")
            return

        # Determine columns to display
        display_cols = group_cols + metrics

        # Check if we need to add header row
        has_header = self._has_header_row(table)
        start_row = 1 if has_header else 0

        # Populate header if needed
        if has_header and len(table.rows) > 0:
            for col_idx, col_name in enumerate(display_cols):
                if col_idx < len(table.columns):
                    cell = table.cell(0, col_idx)
                    cell.text = str(col_name)

        # Populate data rows
        for row_idx, (_, row) in enumerate(data.iterrows()):
            table_row_idx = start_row + row_idx

            # Check if we need more rows
            if table_row_idx >= len(table.rows):
                # Can't add rows dynamically in python-pptx easily
                # Log warning and skip extra rows
                self.logger.warning(
                    f"Table has only {len(table.rows)} rows but needs {table_row_idx + 1}. "
                    f"Skipping remaining {len(data) - row_idx} data rows."
                )
                break

            # Populate cells
            for col_idx, col_name in enumerate(display_cols):
                if col_idx < len(table.columns):
                    cell = table.cell(table_row_idx, col_idx)
                    value = row.get(col_name, "")

                    # Format value
                    if pd.isna(value):
                        cell.text = ""
                    elif isinstance(value, float):
                        cell.text = f"{value:.2f}"
                    else:
                        cell.text = str(value)

    def _has_header_row(self, table: Any) -> bool:
        """Check if table has a header row.

        Args:
            table: PowerPoint table object.

        Returns:
            True if first row appears to be a header.
        """
        if len(table.rows) == 0:
            return False

        # Simple heuristic: check if first row has text
        first_row = table.rows[0]
        return any(cell.text.strip() for cell in first_row.cells)

    def _apply_table_formatting(self, table: Any) -> None:
        """Apply comprehensive formatting to table from config.

        Args:
            table: PowerPoint table object.
        """
        defaults = self.defaults

        # Apply column widths
        self._apply_column_widths(table)

        # Apply formatting to each cell
        for row_idx, row in enumerate(table.rows):
            is_header = row_idx == 0
            is_even_row = row_idx % 2 == 0

            for col_idx, cell in enumerate(row.cells):
                # Apply font formatting
                self._format_cell_text(cell, is_header, defaults)

                # Apply cell fill color
                self._format_cell_fill(cell, is_header, is_even_row, defaults)

                # Apply cell margins for proper spacing
                self._format_cell_margins(cell)

                # Apply text alignment
                self._format_cell_alignment(cell, is_header, col_idx)

        self.logger.debug("Applied table formatting from config")

    def _apply_column_widths(self, table: Any) -> None:
        """Apply column widths from config.

        Args:
            table: PowerPoint table object.
        """
        defaults = self.defaults
        num_cols = len(table.columns)

        if num_cols == 0:
            return

        # Calculate total width and distribute
        total_width = Inches(defaults.width_in)
        first_col_width = Inches(defaults.first_col_w_in)
        second_col_width = Inches(defaults.second_col_w_in)

        # Set first column width
        if num_cols >= 1:
            table.columns[0].width = first_col_width

        # Set second column width
        if num_cols >= 2:
            table.columns[1].width = second_col_width

        # Distribute remaining width evenly among other columns
        if num_cols > 2:
            remaining_width = total_width - first_col_width - second_col_width
            other_col_width = remaining_width // (num_cols - 2)
            for col_idx in range(2, num_cols):
                table.columns[col_idx].width = other_col_width

    def _format_cell_text(self, cell: Any, is_header: bool, defaults: TableDefaults) -> None:
        """Apply text formatting to a cell.

        Args:
            cell: PowerPoint cell object.
            is_header: Whether this is a header row cell.
            defaults: Table defaults configuration.
        """
        try:
            # Access the text frame
            tf = cell.text_frame

            # Set vertical anchor to middle
            tf.word_wrap = True

            for paragraph in tf.paragraphs:
                # Set font size
                paragraph.font.size = Pt(defaults.font_size)

                # Set font color based on header/body
                if is_header:
                    rgb = defaults.header_font_rgb
                else:
                    rgb = defaults.body_font_rgb
                paragraph.font.color.rgb = RGBColor(rgb[0], rgb[1], rgb[2])

                # Set font to bold for headers
                if is_header:
                    paragraph.font.bold = True
                else:
                    paragraph.font.bold = False

        except Exception as e:
            self.logger.debug(f"Could not format cell text: {e}")

    def _format_cell_fill(
        self, cell: Any, is_header: bool, is_even_row: bool, defaults: TableDefaults
    ) -> None:
        """Apply fill color to a cell.

        Args:
            cell: PowerPoint cell object.
            is_header: Whether this is a header row cell.
            is_even_row: Whether this is an even-numbered row.
            defaults: Table defaults configuration.
        """
        try:
            if is_header:
                rgb = defaults.header_fill_rgb
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(rgb[0], rgb[1], rgb[2])
            elif is_even_row:
                rgb = defaults.row_stripe_rgb
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(rgb[0], rgb[1], rgb[2])
            else:
                # Odd rows - no fill (white background)
                cell.fill.background()
        except Exception as e:
            self.logger.debug(f"Could not format cell fill: {e}")

    def _format_cell_margins(self, cell: Any) -> None:
        """Apply cell margins for proper text spacing.

        Args:
            cell: PowerPoint cell object.
        """
        try:
            # Set cell margins (in EMUs - 914400 EMUs = 1 inch)
            # Small margins for compact tables
            margin = Inches(0.05)  # 0.05 inch margins
            cell.margin_left = margin
            cell.margin_right = margin
            cell.margin_top = margin
            cell.margin_bottom = margin
        except Exception as e:
            self.logger.debug(f"Could not format cell margins: {e}")

    def _format_cell_alignment(self, cell: Any, is_header: bool, col_idx: int) -> None:
        """Apply text alignment to a cell.

        Args:
            cell: PowerPoint cell object.
            is_header: Whether this is a header row cell.
            col_idx: Column index.
        """
        try:
            tf = cell.text_frame

            # Vertical alignment - center
            tf.anchor = MSO_ANCHOR.MIDDLE

            for paragraph in tf.paragraphs:
                if is_header:
                    # Headers centered
                    paragraph.alignment = PP_ALIGN.CENTER
                elif col_idx == 0:
                    # First column (labels) left-aligned
                    paragraph.alignment = PP_ALIGN.LEFT
                else:
                    # Data columns right-aligned for numbers
                    paragraph.alignment = PP_ALIGN.RIGHT
        except Exception as e:
            self.logger.debug(f"Could not format cell alignment: {e}")

    def build_table_spec(
        self,
        data: pd.DataFrame,
        name: str,
        title: str | None = None,
    ) -> TableSpec:
        """Build a TableSpec from DataFrame per ADR-0029.

        This method bridges the PPTX renderer with the shared rendering contract.

        Args:
            data: DataFrame to convert.
            name: Spec name/identifier.
            title: Optional table title.

        Returns:
            TableSpec conforming to shared rendering contract.
        """
        # Convert DataFrame to TableData
        headers = list(data.columns)
        rows = data.values.tolist()

        table_data = TableData(
            headers=headers,
            rows=rows,
            column_alignments=self._infer_column_alignments(data),
        )

        # Build spec with styling from config defaults
        defaults = self.defaults
        header_rgb = defaults.header_fill_rgb
        header_hex = f"#{header_rgb[0]:02X}{header_rgb[1]:02X}{header_rgb[2]:02X}"
        header_font_rgb = defaults.header_font_rgb
        header_font_hex = f"#{header_font_rgb[0]:02X}{header_font_rgb[1]:02X}{header_font_rgb[2]:02X}"
        body_font_rgb = defaults.body_font_rgb
        body_font_hex = f"#{body_font_rgb[0]:02X}{body_font_rgb[1]:02X}{body_font_rgb[2]:02X}"
        alt_row_rgb = defaults.row_stripe_rgb
        alt_row_hex = f"#{alt_row_rgb[0]:02X}{alt_row_rgb[1]:02X}{alt_row_rgb[2]:02X}"

        return TableSpec(
            spec_id=f"table_{uuid4().hex[:8]}",
            name=name,
            title=title,
            data=table_data,
            header_background=header_hex,
            header_font_color=header_font_hex,
            body_font_color=body_font_hex,
            alternate_row_color=alt_row_hex,
            border_width=defaults.grid.body_line_pt,
            source_tool="pptx",
        )

    def _infer_column_alignments(
        self,
        data: pd.DataFrame,
    ) -> list[str]:
        """Infer column alignments from data types.

        Args:
            data: DataFrame to analyze.

        Returns:
            List of alignment strings ('left', 'center', 'right').
        """
        alignments = []
        for col in data.columns:
            dtype = data[col].dtype
            if pd.api.types.is_numeric_dtype(dtype):
                alignments.append("right")
            else:
                alignments.append("left")
        return alignments
