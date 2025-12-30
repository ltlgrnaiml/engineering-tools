"""Unpivot extraction strategy.

Per SPEC-0009: Transform wide-format data to long-format.
Converts multiple value columns into parameter/value pairs.
"""

import logging
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class UnpivotStrategy(ExtractionStrategy):
    """Transform wide-format data to long-format by unpivoting.
    
    Per SPEC-0009:
    - id_vars: Columns to keep as identifiers
    - value_vars: Columns to unpivot
    - var_name: Name for parameter column (default: "variable")
    - value_name: Name for value column (default: "value")
    
    Use cases: Parameter tables, wide-to-long transformation, normalization.
    """
    
    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute unpivot extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with unpivot settings
            context: Context dictionary
            
        Returns:
            Long-format DataFrame with parameter/value columns
        """
        # First get the data as a DataFrame
        arr = self._get_at_path(data, config.path)
        
        if arr is None:
            logger.warning(f"No data found at path: {config.path}")
            return pl.DataFrame()
        
        # Convert to DataFrame
        if isinstance(arr, list):
            df = pl.DataFrame(arr)
        elif isinstance(arr, dict):
            df = pl.DataFrame([arr])
        else:
            logger.warning(f"Expected list/dict at {config.path}, got {type(arr).__name__}")
            return pl.DataFrame()
        
        if df.is_empty():
            return df
        
        # Validate columns exist
        id_vars = config.id_vars or []
        value_vars = config.value_vars or []
        
        # Filter to existing columns
        existing_id_vars = [c for c in id_vars if c in df.columns]
        existing_value_vars = [c for c in value_vars if c in df.columns]
        
        if not existing_value_vars:
            logger.warning("No value_vars columns found in data")
            return df
        
        # Perform unpivot (melt in polars)
        return df.unpivot(
            on=existing_value_vars,
            index=existing_id_vars,
            variable_name=config.var_name,
            value_name=config.value_name,
        )
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate unpivot configuration."""
        errors = []
        if not config.path:
            errors.append("unpivot strategy requires 'path'")
        if not config.value_vars:
            errors.append("unpivot strategy requires 'value_vars'")
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
