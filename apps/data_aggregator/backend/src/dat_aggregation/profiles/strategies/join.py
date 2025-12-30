"""Join extraction strategy.

Per SPEC-0009: Join data from two different JSONPath locations.
Useful for enriching data with metadata from another part of the document.
"""

import logging
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class JoinStrategy(ExtractionStrategy):
    """Join data from two different JSONPath locations.
    
    Per SPEC-0009:
    - left: Left table source (path + key)
    - right: Right table source (path + key)
    - how: Join type (left, right, inner, outer)
    
    Use cases: Enriching measurements with metadata, combining related tables.
    """
    
    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute join extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with join settings
            context: Context dictionary
            
        Returns:
            Joined DataFrame
        """
        if not config.left or not config.right:
            logger.error("join strategy requires 'left' and 'right' config")
            return pl.DataFrame()
        
        # Get left data
        left_arr = self._get_at_path(data, config.left.path)
        if left_arr is None:
            logger.warning(f"No data found at left path: {config.left.path}")
            return pl.DataFrame()
        
        # Get right data
        right_arr = self._get_at_path(data, config.right.path)
        if right_arr is None:
            logger.warning(f"No data found at right path: {config.right.path}")
            return pl.DataFrame()
        
        # Convert to DataFrames
        left_df = self._to_dataframe(left_arr)
        right_df = self._to_dataframe(right_arr)
        
        if left_df.is_empty():
            return pl.DataFrame()
        
        if right_df.is_empty():
            return left_df
        
        # Validate join keys exist
        left_key = config.left.key
        right_key = config.right.key
        
        if left_key not in left_df.columns:
            logger.error(f"Left key '{left_key}' not found in left DataFrame")
            return left_df
        
        if right_key not in right_df.columns:
            logger.error(f"Right key '{right_key}' not found in right DataFrame")
            return left_df
        
        # Perform join
        how = config.how or "left"
        
        # Handle key column name conflicts
        if left_key != right_key:
            # Rename right key to match left for join
            right_df = right_df.rename({right_key: left_key})
        
        return left_df.join(
            right_df,
            on=left_key,
            how=how,  # type: ignore
        )
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate join configuration."""
        errors = []
        if not config.left:
            errors.append("join strategy requires 'left' config")
        elif not config.left.path or not config.left.key:
            errors.append("join strategy requires 'left.path' and 'left.key'")
        
        if not config.right:
            errors.append("join strategy requires 'right' config")
        elif not config.right.path or not config.right.key:
            errors.append("join strategy requires 'right.path' and 'right.key'")
        
        if config.how and config.how not in ("left", "right", "inner", "outer"):
            errors.append(f"Invalid join type: {config.how}")
        
        return errors
    
    def _get_at_path(self, data: Any, path: str) -> Any:
        """Navigate to JSONPath and return value."""
        # Handle [*] suffix
        path = path.rstrip("[*]") if path.endswith("[*]") else path
        
        if path == "$" or path == "":
            return data
        
        try:
            expr = jsonpath_parse(path)
            matches = expr.find(data)
            if matches:
                if len(matches) > 1:
                    return [m.value for m in matches]
                return matches[0].value
            return None
        except Exception as e:
            logger.error(f"JSONPath error for '{path}': {e}")
            return None
    
    def _to_dataframe(self, arr: Any) -> pl.DataFrame:
        """Convert array/dict to DataFrame."""
        if isinstance(arr, list):
            if not arr:
                return pl.DataFrame()
            return pl.DataFrame(arr)
        elif isinstance(arr, dict):
            return pl.DataFrame([arr])
        else:
            return pl.DataFrame()
