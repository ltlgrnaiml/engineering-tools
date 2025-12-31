"""FlatObject extraction strategy.

Per SPEC-0009: Extract flat JSON object as single-row DataFrame.
Object keys become column names, values become the single row.
"""

import logging
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class FlatObjectStrategy(ExtractionStrategy):
    """Extract flat JSON object as single-row DataFrame.
    
    Per SPEC-0009:
    - Object keys become column names
    - Values become the single row
    - Optionally flatten nested objects with separator
    
    Use cases: Summary statistics, metadata extraction, configuration objects.
    """

    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute flat_object extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with path
            context: Context dictionary (not used for extraction, but available)
            
        Returns:
            Single-row DataFrame with object keys as columns
        """
        # Navigate to path using JSONPath
        obj = self._get_at_path(data, config.path)

        if obj is None:
            logger.warning(f"No data found at path: {config.path}")
            return pl.DataFrame()

        if not isinstance(obj, dict):
            logger.warning(f"Expected dict at {config.path}, got {type(obj).__name__}")
            return pl.DataFrame()

        # Flatten if configured
        if config.flatten_nested:
            obj = self._flatten_dict(obj, config.flatten_separator)
        else:
            # Convert nested objects to JSON strings
            obj = self._stringify_nested(obj)

        # Build single-row DataFrame
        return pl.DataFrame([obj])

    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate flat_object configuration."""
        errors = []
        if not config.path:
            errors.append("flat_object strategy requires 'path'")
        return errors

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

    def _flatten_dict(
        self,
        obj: dict,
        separator: str,
        parent_key: str = "",
    ) -> dict[str, Any]:
        """Recursively flatten nested dictionary.
        
        Args:
            obj: Dictionary to flatten
            separator: Separator for nested keys (e.g., "_")
            parent_key: Current parent key prefix
            
        Returns:
            Flattened dictionary with compound keys
        """
        items: list[tuple[str, Any]] = []
        for key, value in obj.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(
                    self._flatten_dict(value, separator, new_key).items()
                )
            elif isinstance(value, list):
                # Convert lists to JSON string
                import json
                items.append((new_key, json.dumps(value)))
            else:
                items.append((new_key, value))
        return dict(items)

    def _stringify_nested(self, obj: dict) -> dict[str, Any]:
        """Convert nested objects/arrays to JSON strings."""
        import json

        result = {}
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                result[key] = json.dumps(value)
            else:
                result[key] = value
        return result
