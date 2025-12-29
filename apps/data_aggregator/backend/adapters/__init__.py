"""DAT File Adapters package.

Per ADR-0011: Profile-Driven Extraction & AdapterFactory Pattern.
Per SPEC-DAT-0003: Adapter Interface & Registry specification.

This package provides file adapters for the Data Aggregator Tool (DAT).
Adapters handle reading various file formats into Polars DataFrames.

Available Adapters:
- CSVAdapter: CSV and TSV files (.csv, .tsv)
- ExcelAdapter: Excel files (.xlsx, .xls)
- JSONAdapter: JSON and JSON Lines files (.json, .jsonl, .ndjson)
- ParquetAdapter: Parquet files (.parquet)

Usage:
    from apps.data_aggregator.backend.adapters import create_default_registry

    # Create registry with all built-in adapters
    registry = create_default_registry()

    # Auto-select adapter by file extension
    adapter = registry.get_adapter_for_file("data.csv")

    # Read file (async)
    df, result = await adapter.read_dataframe("data.csv")

    # Probe schema without reading all data (async)
    schema = await adapter.probe_schema("data.csv")

    # Or get specific adapter by ID
    csv_adapter = registry.get_adapter("csv")
"""

from apps.data_aggregator.backend.adapters.csv_adapter import CSVAdapter
from apps.data_aggregator.backend.adapters.excel_adapter import ExcelAdapter
from apps.data_aggregator.backend.adapters.json_adapter import JSONAdapter
from apps.data_aggregator.backend.adapters.parquet_adapter import ParquetAdapter
from apps.data_aggregator.backend.adapters.registry import (
    AdapterNotFoundError,
    AdapterRegistry,
)

__version__ = "1.0.0"

__all__ = [
    # Registry
    "AdapterRegistry",
    "AdapterNotFoundError",
    "create_default_registry",
    # Adapters
    "CSVAdapter",
    "ExcelAdapter",
    "JSONAdapter",
    "ParquetAdapter",
]


def create_default_registry() -> AdapterRegistry:
    """Create an AdapterRegistry with all built-in adapters registered.

    This is the recommended way to get a ready-to-use adapter registry.
    All built-in adapters (CSV, Excel, JSON, Parquet) are registered automatically.

    Returns:
        AdapterRegistry with CSV, Excel, JSON, and Parquet adapters registered.

    Example:
        >>> registry = create_default_registry()
        >>> adapter = registry.get_adapter_for_file("data.csv")
        >>> df, result = await adapter.read_dataframe("data.csv")
    """
    registry = AdapterRegistry()

    # Register all built-in adapters
    registry.register(CSVAdapter(), is_builtin=True)
    registry.register(ExcelAdapter(), is_builtin=True)
    registry.register(JSONAdapter(), is_builtin=True)
    registry.register(ParquetAdapter(), is_builtin=True)

    return registry

