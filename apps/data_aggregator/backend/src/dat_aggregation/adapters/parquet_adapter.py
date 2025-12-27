"""Parquet file adapter."""
from pathlib import Path

import polars as pl


class ParquetAdapter:
    """Adapter for Parquet files."""
    
    EXTENSIONS = {".parquet", ".pq"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in ParquetAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        return pl.read_parquet(path)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        return [path.stem]
    
    @staticmethod
    def get_preview(path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        return pl.read_parquet(path).head(rows)
