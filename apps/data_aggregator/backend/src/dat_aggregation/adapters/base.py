"""Base adapter protocol for file format handling.

Per ADR-0011: Adapters are selected via handles-first registry.
"""
from pathlib import Path
from typing import Protocol, runtime_checkable

import polars as pl


@runtime_checkable
class FileAdapter(Protocol):
    """Protocol for file adapters."""
    
    EXTENSIONS: set[str]
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        """Check if this adapter can handle the file."""
        ...
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        """Read file and return DataFrame."""
        ...
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        """Get list of tables/sheets in file."""
        ...
    
    @staticmethod
    def get_preview(path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        """Get preview of table data."""
        ...
