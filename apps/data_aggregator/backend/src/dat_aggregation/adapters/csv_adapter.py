"""CSV/TSV file adapter."""
from pathlib import Path

import polars as pl


class CSVAdapter:
    """Adapter for CSV/TSV files."""

    EXTENSIONS = {".csv", ".tsv", ".txt"}

    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in CSVAdapter.EXTENSIONS

    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        separator = options.get("separator", ",")
        if path.suffix.lower() == ".tsv":
            separator = "\t"
        return pl.read_csv(path, separator=separator)

    @staticmethod
    def get_tables(path: Path) -> list[str]:
        return [path.stem]

    @staticmethod
    def get_preview(path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        separator = ","
        if path.suffix.lower() == ".tsv":
            separator = "\t"
        return pl.read_csv(path, separator=separator, n_rows=rows)
