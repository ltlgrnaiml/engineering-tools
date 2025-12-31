"""RepeatOver extraction strategy.

Per SPEC-0009: Extract with iteration over array elements.
Wraps a base strategy and applies it at each iteration.
"""

import logging
import re
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class RepeatOverStrategy(ExtractionStrategy):
    """Extract with iteration over array elements.
    
    Per SPEC-0009:
    - Iterate over array at repeat_over.path
    - Apply base strategy at each element
    - Inject context fields from parent element
    - Concatenate all results
    
    Use cases: Per-site measurements, per-image data, hierarchical data.
    """

    def __init__(self, base_strategy: ExtractionStrategy | None = None):
        """Initialize with optional base strategy.
        
        Args:
            base_strategy: Strategy to apply at each iteration.
                          If None, will be determined from config.strategy.
        """
        self._base_strategy = base_strategy

    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute repeat_over extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with repeat_over settings
            context: Context dictionary
            
        Returns:
            Combined DataFrame from all iterations with injected fields
        """
        if not config.repeat_over:
            logger.error("repeat_over strategy requires repeat_over config")
            return pl.DataFrame()

        # Get array to iterate over
        arr = self._get_at_path(data, config.repeat_over.path)

        if arr is None or not isinstance(arr, list):
            logger.warning(f"No array found at repeat_over path: {config.repeat_over.path}")
            return pl.DataFrame()

        # Get or create base strategy
        base_strategy = self._get_base_strategy(config)
        if not base_strategy:
            logger.error("Could not determine base strategy for repeat_over")
            return pl.DataFrame()

        # Iterate and collect results
        all_dfs: list[pl.DataFrame] = []
        index_var = config.repeat_over.as_var

        for i, element in enumerate(arr):
            # Substitute index in path
            element_path = self._substitute_index(config.path, index_var, i)

            # Create modified config for this iteration
            element_config = SelectConfig(
                strategy=config.strategy,
                path=element_path,
                headers_key=config.headers_key,
                data_key=config.data_key,
                fields=config.fields,
                flatten_nested=config.flatten_nested,
                flatten_separator=config.flatten_separator,
            )

            # Extract data at this element
            df = base_strategy.extract(data, element_config, context)

            if df.is_empty():
                continue

            # Inject fields from parent element
            if config.repeat_over.inject_fields and isinstance(element, dict):
                for target_col, source_path in config.repeat_over.inject_fields.items():
                    value = self._get_nested_value(element, source_path)
                    df = df.with_columns(pl.lit(value).alias(target_col))

            all_dfs.append(df)

        # Concatenate all DataFrames
        if not all_dfs:
            return pl.DataFrame()

        return pl.concat(all_dfs, how="diagonal")

    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate repeat_over configuration."""
        errors = []
        if not config.path:
            errors.append("repeat_over strategy requires 'path'")
        if not config.repeat_over:
            errors.append("repeat_over strategy requires 'repeat_over' config")
        else:
            if not config.repeat_over.path:
                errors.append("repeat_over.path is required")
            if not config.repeat_over.as_var:
                errors.append("repeat_over.as is required")
        return errors

    def _get_base_strategy(self, config: SelectConfig) -> ExtractionStrategy | None:
        """Get the base strategy to use for extraction."""
        if self._base_strategy:
            return self._base_strategy

        # Import here to avoid circular imports
        from .array_of_objects import ArrayOfObjectsStrategy
        from .flat_object import FlatObjectStrategy
        from .headers_data import HeadersDataStrategy

        # Determine base strategy from config
        if config.headers_key and config.data_key:
            return HeadersDataStrategy()
        elif config.strategy == "flat_object":
            return FlatObjectStrategy()
        elif config.strategy == "array_of_objects":
            return ArrayOfObjectsStrategy()
        else:
            # Default to headers_data
            return HeadersDataStrategy()

    def _get_at_path(self, data: Any, path: str) -> Any:
        """Navigate to JSONPath and return value."""
        if path == "$" or path == "":
            return data

        try:
            expr = jsonpath_parse(path)
            matches = expr.find(data)
            if matches:
                return matches[0].value
            return None
        except Exception as e:
            logger.error(f"JSONPath error for '{path}': {e}")
            return None

    def _substitute_index(self, path: str, var_name: str, index: int) -> str:
        """Substitute index variable in path.
        
        Example: $.sites[{site_index}].data -> $.sites[0].data
        """
        pattern = r"\{" + re.escape(var_name) + r"\}"
        return re.sub(pattern, str(index), path)

    def _get_nested_value(self, obj: dict, path: str) -> Any:
        """Get nested value from dict using simple path (e.g., $.field or field)."""
        if path.startswith("$."):
            path = path[2:]

        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
