"""Base renderer interface and context for shape rendering."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pptx.shapes.base import BaseShape

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2

logger = logging.getLogger(__name__)


@dataclass
class RenderContext:
    """Context information for rendering a shape.

    Attributes:
        shape: PowerPoint shape to render into.
        parsed_name: Parsed shape name with renderer type, scope, etc.
        data: Full dataset as pandas DataFrame.
        shape_data: Filtered/aggregated data specific to this shape.
        output_dir: Directory for temporary files (plots, images).
        metadata: Additional metadata (run info, etc.).
    """

    shape: BaseShape
    parsed_name: ParsedShapeNameV2
    data: pd.DataFrame
    shape_data: pd.DataFrame | None = None
    output_dir: Path | None = None
    metadata: dict[str, Any] | None = None


class BaseRenderer(ABC):
    """Abstract base class for all shape renderers.

    Each renderer is responsible for populating a specific type of shape
    (plot, table, text, KPI, etc.) based on the parsed shape name and data.
    """

    def __init__(self) -> None:
        """Initialize the renderer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this renderer can handle the given shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if this renderer can handle this shape type.
        """
        pass

    @abstractmethod
    async def render(self, context: RenderContext) -> None:
        """Render data into the shape.

        Args:
            context: Rendering context with shape, data, and metadata.

        Raises:
            ValueError: If shape or data is invalid.
            RuntimeError: If rendering fails.
        """
        pass

    def filter_data(
        self,
        data: pd.DataFrame,
        parsed_name: ParsedShapeNameV2,
    ) -> pd.DataFrame:
        """Filter data based on shape filters.

        Args:
            data: Full dataset.
            parsed_name: Parsed shape name with filters.

        Returns:
            Filtered DataFrame.
        """
        filtered = data.copy()

        self.logger.debug(f"Filtering data with {len(filtered)} rows")
        self.logger.debug(f"Available columns: {list(filtered.columns)}")
        self.logger.debug(f"Filter parameters: {parsed_name.filters}")

        # Apply filters
        for filter_name, filter_value in parsed_name.filters.items():
            if filter_name in filtered.columns:
                # Handle special values like "both", "all", "any"
                if isinstance(filter_value, str) and filter_value.lower() in ["both", "all", "any"]:
                    # Don't filter - include all values
                    self.logger.debug(
                        f"Skipping filter for {filter_name}={filter_value} (include all)"
                    )
                    continue

                # Case-insensitive comparison for string values
                if filtered[filter_name].dtype == "object" and isinstance(filter_value, str):
                    filtered = filtered[filtered[filter_name].str.lower() == filter_value.lower()]
                else:
                    filtered = filtered[filtered[filter_name] == filter_value]
                self.logger.debug(
                    f"After filtering {filter_name}={filter_value}: {len(filtered)} rows"
                )
            else:
                self.logger.debug(f"Column '{filter_name}' not in data, skipping filter")

        self.logger.debug(f"Final filtered data: {len(filtered)} rows")
        return filtered

    def aggregate_data(
        self,
        data: pd.DataFrame,
        grouping: str | list[str],
        metrics: list[str],
        agg_func: str = "mean",
    ) -> pd.DataFrame:
        """Aggregate data by grouping dimensions.

        Args:
            data: Data to aggregate.
            grouping: Grouping pattern (e.g., 'by_side', 'by_wafer') or list of columns.
            metrics: List of metric columns to aggregate.
            agg_func: Aggregation function ('mean', 'sum', 'count', etc.).

        Returns:
            Aggregated DataFrame.
        """
        # Parse grouping pattern or use provided columns
        group_cols = grouping if isinstance(grouping, list) else self._parse_grouping(grouping)

        # Filter to only existing columns
        group_cols = [col for col in group_cols if col in data.columns]
        metrics = [m for m in metrics if m in data.columns]

        if not group_cols or not metrics:
            return data

        # Perform aggregation
        try:
            aggregated = data.groupby(group_cols)[metrics].agg(agg_func).reset_index()
            return aggregated
        except Exception as e:
            self.logger.warning(f"Aggregation failed: {e}, returning original data")
            return data

    def _parse_grouping(self, grouping: str) -> list[str]:
        """Parse grouping pattern into column names.

        Args:
            grouping: Grouping pattern (e.g., 'by_side', 'contexts').

        Returns:
            List of column names to group by.
        """
        # Handle common grouping patterns
        if grouping == "by_side":
            return ["side"]
        elif grouping == "by_wafer":
            return ["wafer"]
        elif grouping == "by_side_wafer":
            return ["side", "wafer"]
        elif grouping == "contexts":
            # Group by all context columns
            return ["side", "wafer", "imcol"]
        elif grouping == "none":
            return []
        else:
            # Try to extract column name from pattern
            if grouping.startswith("by_"):
                return [grouping[3:]]
            return []
