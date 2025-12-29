"""HeadersData extraction strategy.

Per SPEC-DAT-0012: Extract headers + data arrays as DataFrame.
Headers are in one array, data rows are in another.
"""

import logging
from typing import Any

import polars as pl
from jsonpath_ng import parse as jsonpath_parse

from .base import ExtractionStrategy, SelectConfig

logger = logging.getLogger(__name__)


class HeadersDataStrategy(ExtractionStrategy):
    """Extract headers + data arrays as DataFrame.
    
    Per SPEC-DAT-0012:
    - headers_key contains column names array
    - data_key contains data rows array
    - Handles mismatched lengths gracefully
    
    Use cases: Statistics tables, measurement data with explicit headers.
    """
    
    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute headers_data extraction.
        
        Args:
            data: Source data (parsed JSON)
            config: Selection configuration with path, headers_key, data_key
            context: Context dictionary (not used for extraction)
            
        Returns:
            Multi-row DataFrame with headers as columns
        """
        # Navigate to path
        obj = self._get_at_path(data, config.path)
        
        if obj is None:
            logger.warning(f"No data found at path: {config.path}")
            return pl.DataFrame()
        
        if not isinstance(obj, dict):
            logger.warning(f"Expected dict at {config.path}, got {type(obj).__name__}")
            return pl.DataFrame()
        
        # Get headers
        headers = self._get_headers(obj, config)
        if not headers:
            logger.warning(f"No headers found for {config.path}")
            return pl.DataFrame()
        
        # Get data rows
        rows = self._get_data_rows(obj, config)
        if not rows:
            logger.debug(f"No data rows found for {config.path}")
            return pl.DataFrame(schema={h: pl.Utf8 for h in headers})
        
        # Build DataFrame
        return self._build_dataframe(headers, rows)
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate headers_data configuration."""
        errors = []
        if not config.path:
            errors.append("headers_data strategy requires 'path'")
        if not config.headers_key and not config.infer_headers:
            errors.append(
                "headers_data strategy requires 'headers_key' or 'infer_headers'"
            )
        if not config.data_key:
            errors.append("headers_data strategy requires 'data_key'")
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
    
    def _get_headers(self, obj: dict, config: SelectConfig) -> list[str]:
        """Extract headers from object."""
        if config.headers_key and config.headers_key in obj:
            headers = obj[config.headers_key]
            if isinstance(headers, list):
                return [str(h) for h in headers]
        
        if config.infer_headers and config.data_key in obj:
            rows = obj[config.data_key]
            if rows and isinstance(rows[0], list):
                return [f"col_{i}" for i in range(len(rows[0]))]
        
        if config.default_headers:
            return config.default_headers
        
        return []
    
    def _get_data_rows(self, obj: dict, config: SelectConfig) -> list[list[Any]]:
        """Extract data rows from object."""
        if not config.data_key or config.data_key not in obj:
            return []
        
        rows = obj[config.data_key]
        if not isinstance(rows, list):
            return []
        
        # Ensure all rows are lists
        result = []
        for row in rows:
            if isinstance(row, list):
                result.append(row)
            elif isinstance(row, dict):
                # If dict, extract values in order
                result.append(list(row.values()))
            else:
                result.append([row])
        
        return result
    
    def _build_dataframe(
        self,
        headers: list[str],
        rows: list[list[Any]],
    ) -> pl.DataFrame:
        """Build DataFrame from headers and rows."""
        # Handle mismatched lengths
        num_cols = len(headers)
        
        normalized_rows = []
        for row in rows:
            if len(row) < num_cols:
                # Pad with None
                row = row + [None] * (num_cols - len(row))
            elif len(row) > num_cols:
                # Truncate
                row = row[:num_cols]
            normalized_rows.append(row)
        
        # Build column-wise data
        columns = {
            headers[i]: [row[i] for row in normalized_rows]
            for i in range(num_cols)
        }
        
        return pl.DataFrame(columns)
