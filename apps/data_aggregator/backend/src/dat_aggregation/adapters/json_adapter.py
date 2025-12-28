"""JSON file adapter for nested measurement data.

Per ADR-0011: Adapters are selected via handles-first registry.
Supports profile-driven extraction from deeply nested JSON structures.
"""
import json
from pathlib import Path
from typing import Any

import polars as pl


class JSONAdapter:
    """Adapter for JSON files with nested data structures."""
    
    EXTENSIONS = {".json"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in JSONAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        """Read JSON file and extract data.
        
        Options:
            json_path: JSONPath-like path to extract (e.g., "$.statistics")
            headers_key: Key containing column headers
            data_key: Key containing row data
            flatten: Whether to flatten nested structures
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        
        # Support both "table" (from routes) and "json_path" parameter names
        json_path = options.get("table") or options.get("json_path")
        headers_key = options.get("headers_key")
        data_key = options.get("data_key")
        
        if json_path:
            data = JSONAdapter._extract_path(data, json_path)
        
        if headers_key and data_key:
            # Headers + data format (2D array) - explicit keys provided
            return JSONAdapter._from_headers_data(data, headers_key, data_key)
        
        # Auto-detect common data patterns
        return JSONAdapter._auto_parse_structure(data)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        """Get list of extractable table paths from JSON structure."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        
        tables = []
        JSONAdapter._find_tables(data, "", tables)
        return tables if tables else [path.stem]
    
    @staticmethod
    def get_preview(path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        """Get preview of table data."""
        options = {}
        if table and table != path.stem:
            options["json_path"] = table
        
        df = JSONAdapter.read(path, **options)
        return df.head(rows)
    
    @staticmethod
    def _extract_path(data: Any, json_path: str) -> Any:
        """Extract data at a JSONPath-like path.
        
        Supports: $.key, $.key.subkey, $.array[0], $.array[*]
        """
        if not json_path or json_path == "$":
            return data
        
        # Remove leading $. if present
        path = json_path.lstrip("$").lstrip(".")
        
        current = data
        for part in path.split("."):
            if not part:
                continue
            
            # Handle array indexing
            if "[" in part:
                key = part[:part.index("[")]
                idx_str = part[part.index("[") + 1:part.index("]")]
                
                if key:
                    current = current.get(key, {})
                
                if idx_str == "*":
                    # Return all items in array
                    return current if isinstance(current, list) else []
                else:
                    idx = int(idx_str)
                    current = current[idx] if isinstance(current, list) and len(current) > idx else {}
            else:
                current = current.get(part, {}) if isinstance(current, dict) else {}
        
        return current
    
    @staticmethod
    def _from_headers_data(
        data: dict | list,
        headers_key: str,
        data_key: str,
    ) -> pl.DataFrame:
        """Convert headers + data format to DataFrame."""
        if isinstance(data, dict):
            headers = data.get(headers_key, [])
            rows = data.get(data_key, [])
        else:
            # Assume first item contains headers
            headers = []
            rows = []
            for item in data:
                if isinstance(item, dict):
                    h = item.get(headers_key, [])
                    r = item.get(data_key, [])
                    if h and not headers:
                        headers = h
                    rows.extend(r if isinstance(r, list) and r and isinstance(r[0], list) else [r])
        
        if not headers or not rows:
            return pl.DataFrame()
        
        # Build DataFrame from 2D array
        return pl.DataFrame(rows, schema=headers, orient="row")
    
    @staticmethod
    def _auto_parse_structure(data: Any) -> pl.DataFrame:
        """Auto-detect and parse common JSON data patterns.
        
        Supports:
        - {columns: [...], values: [...]} - column names + 2D array
        - {columns: [...], data: [...]} - same pattern
        - {headers: [...], bins: [...]} - histogram format
        - {headers: [...], rows: [...]} - row-based format
        - [{headers: [...], bins: [...]}] - array of histogram objects
        - [obj1, obj2, ...] - array of flat objects
        - {key: value, ...} - single flat object
        """
        if isinstance(data, dict):
            # Check for columns + values/data pattern
            if "columns" in data:
                for data_key in ["values", "data", "rows"]:
                    if data_key in data:
                        return JSONAdapter._from_headers_data(data, "columns", data_key)
            
            # Check for headers + various data patterns
            if "headers" in data:
                for data_key in ["bins", "rows", "values", "data", "items"]:
                    if data_key in data:
                        return JSONAdapter._from_headers_data(data, "headers", data_key)
            
            # Single flat object - convert to single-row DataFrame
            return pl.DataFrame([data])
        
        elif isinstance(data, list) and data:
            first = data[0]
            
            # Array of objects with headers+data structure
            if isinstance(first, dict):
                # Check if items have headers+data pattern
                if "headers" in first:
                    for data_key in ["bins", "rows", "values", "data", "items"]:
                        if data_key in first:
                            return JSONAdapter._from_headers_data(data, "headers", data_key)
                
                if "columns" in first:
                    for data_key in ["values", "data", "rows"]:
                        if data_key in first:
                            return JSONAdapter._from_headers_data(data, "columns", data_key)
                
                # Plain array of objects - try to flatten, handle mixed types gracefully
                try:
                    # Filter to only include simple scalar values
                    flat_data = []
                    for item in data:
                        flat_item = {
                            k: v for k, v in item.items()
                            if not isinstance(v, (dict, list))
                        }
                        if flat_item:
                            flat_data.append(flat_item)
                    
                    if flat_data:
                        return pl.DataFrame(flat_data)
                except Exception:
                    pass
                
                return pl.DataFrame()
            
            # Array of primitives or arrays
            return pl.DataFrame({"value": data})
        
        return pl.DataFrame()
    
    @staticmethod
    def _find_tables(data: Any, path: str, tables: list[str], depth: int = 0) -> None:
        """Recursively find extractable table paths."""
        if depth > 5:  # Limit depth to avoid infinite recursion
            return
        
        if isinstance(data, dict):
            # Check if this is a headers+data structure
            if "columns" in data or "headers" in data:
                data_keys = ["data", "values", "rows", "bins", "items"]
                if any(k in data for k in data_keys):
                    tables.append(path or "$")
                    return  # Don't recurse further - this is a complete table
            
            # Check for array of objects (potential table)
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else f"$.{key}"
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    # Array of objects - add as single table
                    tables.append(new_path)
                elif isinstance(value, dict):
                    JSONAdapter._find_tables(value, new_path, tables, depth + 1)
        
        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                tables.append(path or "$")


def extract_table_from_json(
    data: dict,
    table_config: dict,
) -> pl.DataFrame:
    """Extract a table from JSON data using profile table configuration.
    
    Args:
        data: Full JSON data dictionary
        table_config: Table configuration from profile (select, stable_columns, etc.)
        
    Returns:
        Extracted DataFrame
    """
    select = table_config.get("select", {})
    strategy = select.get("strategy", "flat_object")
    path = select.get("path", "$")
    headers_key = select.get("headers_key")
    data_key = select.get("data_key")
    repeat_over = select.get("repeat_over")
    
    if strategy == "flat_object":
        # Direct extraction of flat object
        extracted = JSONAdapter._extract_path(data, path)
        if isinstance(extracted, dict):
            return pl.DataFrame([extracted])
        return pl.DataFrame()
    
    elif strategy == "headers_data":
        if repeat_over:
            # Iterate over array and collect all data
            repeat_path = repeat_over.get("path", "")
            items = JSONAdapter._extract_path(data, repeat_path)
            
            if not isinstance(items, list):
                items = [items]
            
            all_rows = []
            headers = None
            
            for i, _ in enumerate(items):
                # Substitute index in path
                item_path = path.replace(f"{{{repeat_over.get('as', 'index')}}}", str(i))
                item_data = JSONAdapter._extract_path(data, item_path)
                
                if isinstance(item_data, dict):
                    h = item_data.get(headers_key, [])
                    r = item_data.get(data_key, [])
                    
                    if h and not headers:
                        headers = h
                    
                    if isinstance(r, list):
                        if r and isinstance(r[0], list):
                            all_rows.extend(r)
                        else:
                            all_rows.append(r)
            
            if headers and all_rows:
                return pl.DataFrame(all_rows, schema=headers, orient="row")
            return pl.DataFrame()
        else:
            # Single extraction
            extracted = JSONAdapter._extract_path(data, path)
            return JSONAdapter._from_headers_data(extracted, headers_key, data_key)
    
    return pl.DataFrame()
