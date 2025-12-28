"""Table Availability stage - probe available tables from selected files.

Per ADR-0006: Table availability uses a deterministic status model:
- available: Table exists and has data
- partial: Table exists but may have issues (missing columns, etc.)
- missing: Table not found in file
- empty: Table exists but has no data
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from shared.utils.stage_id import compute_stage_id


class TableStatus(str, Enum):
    """Status of a table in a source file."""
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"
    EMPTY = "empty"
    ERROR = "error"


@dataclass
class TableInfo:
    """Information about a single table."""
    file_path: str
    table_name: str
    status: TableStatus
    row_count: int | None = None
    column_count: int | None = None
    columns: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class TableAvailabilityResult:
    """Result of table availability probe."""
    availability_id: str
    tables: list[TableInfo]
    total_files: int
    total_tables: int
    available_tables: int
    completed: bool = True


async def execute_table_availability(
    run_id: str,
    selected_files: list[Path],
    expected_columns: list[str] | None = None,
) -> TableAvailabilityResult:
    """Probe available tables from selected files.

    Per ADR-0006: Uses deterministic probe logic to identify tables.
    Tables with missing expected columns are marked as PARTIAL.

    Args:
        run_id: DAT run ID.
        selected_files: List of file paths to probe.
        expected_columns: Optional list of expected column names.
            If provided, tables missing any of these columns will be
            marked as PARTIAL status per ADR-0006.

    Returns:
        TableAvailabilityResult with discovered tables.
    """
    from dat_aggregation.adapters.factory import AdapterFactory

    tables: list[TableInfo] = []

    for file_path in selected_files:
        try:
            adapter = AdapterFactory.get_adapter(file_path)
            table_names = adapter.get_tables(file_path)

            for table_name in table_names:
                try:
                    # Try to read a sample to get metadata
                    df = adapter.read(file_path, sheet=table_name)

                    # Determine status per ADR-0006
                    if len(df) == 0:
                        status = TableStatus.EMPTY
                        missing_cols: list[str] = []
                    elif expected_columns:
                        # Check for missing expected columns per ADR-0006
                        actual_cols = set(df.columns)
                        missing_cols = [
                            col for col in expected_columns if col not in actual_cols
                        ]
                        if missing_cols:
                            status = TableStatus.PARTIAL
                        else:
                            status = TableStatus.AVAILABLE
                    else:
                        status = TableStatus.AVAILABLE
                        missing_cols = []

                    tables.append(TableInfo(
                        file_path=str(file_path),
                        table_name=table_name,
                        status=status,
                        row_count=len(df),
                        column_count=len(df.columns),
                        columns=list(df.columns),
                        missing_columns=missing_cols,
                    ))
                except Exception as e:
                    tables.append(TableInfo(
                        file_path=str(file_path),
                        table_name=table_name,
                        status=TableStatus.ERROR,
                        error_message=str(e),
                    ))
                    
        except ValueError as e:
            # No adapter found for file
            tables.append(TableInfo(
                file_path=str(file_path),
                table_name="<unknown>",
                status=TableStatus.ERROR,
                error_message=f"Unsupported file format: {e}",
            ))
    
    # Compute deterministic ID
    availability_inputs = {
        "run_id": run_id,
        "files": sorted([str(f) for f in selected_files]),
        "table_count": len(tables),
    }
    availability_id = compute_stage_id(availability_inputs, prefix="avail_")
    
    available_count = sum(1 for t in tables if t.status == TableStatus.AVAILABLE)
    
    return TableAvailabilityResult(
        availability_id=availability_id,
        tables=tables,
        total_files=len(selected_files),
        total_tables=len(tables),
        available_tables=available_count,
        completed=True,
    )


def get_tables_by_status(
    result: TableAvailabilityResult,
    status: TableStatus,
) -> list[TableInfo]:
    """Filter tables by status."""
    return [t for t in result.tables if t.status == status]
