"""Table Availability stage - probe available tables from selected files.

Per ADR-0008: Table availability uses a deterministic status model.
Uses shared contracts from shared.contracts.dat.table_status.
"""
from pathlib import Path

from shared.contracts.dat.table_status import (
    TableAvailabilityStatus,
)
from shared.utils.stage_id import compute_stage_id
from pydantic import BaseModel, Field


class TableInfo(BaseModel):
    """Information about a single table during availability scan.
    
    This is a lightweight version used during the scan phase.
    Maps to TableAvailabilityStatus from shared contracts.
    """
    file_path: str
    table_name: str
    status: TableAvailabilityStatus
    row_count: int | None = None
    column_count: int | None = None
    columns: list[str] = Field(default_factory=list)
    missing_columns: list[str] = Field(default_factory=list)
    error_message: str | None = None


class TableAvailabilityResult(BaseModel):
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

    Per ADR-0008: Uses deterministic probe logic to identify tables.
    Tables with missing expected columns are marked as PARTIAL.

    Args:
        run_id: DAT run ID.
        selected_files: List of file paths to probe.
        expected_columns: Optional list of expected column names.
            If provided, tables missing any of these columns will be
            marked as PARTIAL status per ADR-0008.

    Returns:
        TableAvailabilityResult with discovered tables.
    """
    from apps.data_aggregator.backend.adapters import create_default_registry
    from shared.contracts.dat.adapter import ReadOptions

    registry = create_default_registry()
    tables: list[TableInfo] = []

    for file_path in selected_files:
        try:
            adapter = registry.get_adapter_for_file(str(file_path))
            
            # Get table names using async probe_schema
            if adapter.metadata.capabilities.supports_multiple_sheets:
                probe_result = await adapter.probe_schema(str(file_path))
                table_names = [s.sheet_name for s in probe_result.sheets] if probe_result.sheets else [file_path.name]
            else:
                table_names = [file_path.name]

            for table_name in table_names:
                try:
                    # Try to read a sample to get metadata using async adapter
                    options = ReadOptions(extra={"sheet_name": table_name} if table_name != file_path.name else {})
                    df, _ = await adapter.read_dataframe(str(file_path), options)

                    # Determine status per ADR-0008 using shared contracts
                    if len(df) == 0:
                        status = TableAvailabilityStatus.FAILED
                        missing_cols: list[str] = []
                    elif expected_columns:
                        # Check for missing expected columns per ADR-0008
                        actual_cols = set(df.columns)
                        missing_cols = [
                            col for col in expected_columns if col not in actual_cols
                        ]
                        if missing_cols:
                            status = TableAvailabilityStatus.PARTIAL
                        else:
                            status = TableAvailabilityStatus.AVAILABLE
                    else:
                        status = TableAvailabilityStatus.AVAILABLE
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
                        status=TableAvailabilityStatus.FAILED,
                        error_message=str(e),
                    ))

        except ValueError as e:
            # No adapter found for file
            tables.append(TableInfo(
                file_path=str(file_path),
                table_name="<unknown>",
                status=TableAvailabilityStatus.FAILED,
                error_message=f"Unsupported file format: {e}",
            ))

    # Compute deterministic ID
    availability_inputs = {
        "run_id": run_id,
        "files": sorted([str(f) for f in selected_files]),
        "table_count": len(tables),
    }
    availability_id = compute_stage_id(availability_inputs, prefix="avail_")

    available_count = sum(1 for t in tables if t.status == TableAvailabilityStatus.AVAILABLE)

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
    status: TableAvailabilityStatus,
) -> list[TableInfo]:
    """Filter tables by status."""
    return [t for t in result.tables if t.status == status]
