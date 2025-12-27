"""Adapter factory for multi-format file parsing.

Per ADR-0011: Adapters are selected via handles-first registry.
"""
from pathlib import Path
from typing import Type

import polars as pl

from .base import FileAdapter
from .csv_adapter import CSVAdapter
from .excel_adapter import ExcelAdapter
from .parquet_adapter import ParquetAdapter


# Adapter registry - order matters (first match wins)
ADAPTERS: list[Type] = [
    ParquetAdapter,
    ExcelAdapter,
    CSVAdapter,
]


class AdapterFactory:
    """Factory for selecting and using file adapters."""
    
    @classmethod
    def get_adapter(cls, path: Path) -> Type:
        """Get appropriate adapter for file.
        
        Args:
            path: Path to the file
            
        Returns:
            Adapter class that can handle the file
            
        Raises:
            ValueError: If no adapter can handle the file
        """
        for adapter in ADAPTERS:
            if adapter.can_handle(path):
                return adapter
        raise ValueError(f"No adapter found for: {path}")
    
    @classmethod
    def read_file(cls, path: Path, **options) -> pl.DataFrame:
        """Read file using appropriate adapter.
        
        Args:
            path: Path to the file
            **options: Additional options passed to adapter
            
        Returns:
            DataFrame with file contents
        """
        adapter = cls.get_adapter(path)
        return adapter.read(path, **options)
    
    @classmethod
    def get_tables(cls, path: Path) -> list[str]:
        """Get tables/sheets from file.
        
        Args:
            path: Path to the file
            
        Returns:
            List of table/sheet names
        """
        adapter = cls.get_adapter(path)
        return adapter.get_tables(path)
    
    @classmethod
    def get_preview(cls, path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        """Get preview of table data.
        
        Args:
            path: Path to the file
            table: Optional table/sheet name
            rows: Number of rows to preview
            
        Returns:
            DataFrame with preview data
        """
        adapter = cls.get_adapter(path)
        return adapter.get_preview(path, table, rows)
    
    @classmethod
    def get_supported_extensions(cls) -> set[str]:
        """Get all supported file extensions."""
        extensions: set[str] = set()
        for adapter in ADAPTERS:
            extensions.update(adapter.EXTENSIONS)
        return extensions
