"""ArrayOfObjects extraction strategy.

Per SPEC-0009: Extract array of objects as DataFrame.
Each object becomes a row, object keys become columns.
"""

import logging
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class ArrayOfObjectsStrategy(ExtractionStrategy):
    """Extract array of objects as DataFrame.
    
    Per SPEC-0009:
    - Each object in array becomes a row
    - Object keys become columns
    - Union of all keys used for columns
    - Missing keys filled with null
    
    Use cases: List of measurements, record collections, event logs.
    """
    
    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute array_of_objects extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with path
            context: Context dictionary (not used for extraction)
            
        Returns:
            Multi-row DataFrame with union of all object keys as columns
        """
        # Navigate to path - handle [*] suffix
        path = config.path.rstrip("[*]") if config.path.endswith("[*]") else config.path
        arr = self._get_at_path(data, path)
        
        if arr is None:
            logger.warning(f"No data found at path: {config.path}")
            return pl.DataFrame()
        
        if not isinstance(arr, list):
            logger.warning(f"Expected list at {config.path}, got {type(arr).__name__}")
            return pl.DataFrame()
        
        if not arr:
            return pl.DataFrame()
        
        # Filter to specific fields if configured
        if config.fields:
            arr = [
                {k: v for k, v in obj.items() if k in config.fields}
                for obj in arr
                if isinstance(obj, dict)
            ]
        
        # Build DataFrame from list of dicts
        return pl.DataFrame(arr)
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate array_of_objects configuration."""
        errors = []
        if not config.path:
            errors.append("array_of_objects strategy requires 'path'")
        return errors
    
    def _get_at_path(self, data: Any, path: str) -> Any:
        """Navigate to JSONPath and return value."""
        if path == "$" or path == "":
            return data
        
        try:
            expr = jsonpath_parse(path)
            matches = expr.find(data)
            if matches:
                # If multiple matches, return all as list
                if len(matches) > 1:
                    return [m.value for m in matches]
                return matches[0].value
            return None
        except Exception as e:
            logger.error(f"JSONPath error for '{path}': {e}")
            return None
