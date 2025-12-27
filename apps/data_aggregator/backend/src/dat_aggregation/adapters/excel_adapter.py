"""Excel file adapter."""
from pathlib import Path

import polars as pl


class ExcelAdapter:
    """Adapter for Excel files (.xlsx, .xls, .xlsm)."""
    
    EXTENSIONS = {".xlsx", ".xls", ".xlsm"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in ExcelAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        sheet = options.get("sheet", 0)
        return pl.read_excel(path, sheet_name=sheet)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        sheets = wb.sheetnames
        wb.close()
        return sheets
    
    @staticmethod
    def get_preview(path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        sheet = table or 0
        df = pl.read_excel(path, sheet_name=sheet)
        return df.head(rows)
