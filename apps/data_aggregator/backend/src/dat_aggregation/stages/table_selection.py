"""Table Selection stage - user selects which tables to parse.

After Table Availability identifies available tables, users select
which tables they want to include in the parse operation.
"""
from dataclasses import dataclass, field

from shared.utils.stage_id import compute_stage_id
from shared.contracts.dat.table_status import TableAvailabilityStatus
from .table_availability import TableInfo


@dataclass
class TableSelection:
    """A single table selection."""
    file_path: str
    table_name: str
    selected: bool = True


@dataclass
class TableSelectionConfig:
    """Configuration for table selection stage."""
    selections: list[TableSelection] = field(default_factory=list)
    select_all: bool = False  # If True, select all available tables


@dataclass
class TableSelectionResult:
    """Result of table selection stage."""
    selection_id: str
    selected_tables: list[TableSelection]
    total_selected: int
    completed: bool = True


async def execute_table_selection(
    run_id: str,
    available_tables: list[TableInfo],
    config: TableSelectionConfig,
) -> TableSelectionResult:
    """Execute table selection stage.
    
    Args:
        run_id: DAT run ID
        available_tables: Tables from availability stage
        config: Selection configuration
        
    Returns:
        TableSelectionResult with selected tables
    """
    selected: list[TableSelection] = []

    if config.select_all:
        # Select all available tables
        for table in available_tables:
            if table.status == TableAvailabilityStatus.AVAILABLE:
                selected.append(TableSelection(
                    file_path=table.file_path,
                    table_name=table.table_name,
                    selected=True,
                ))
    else:
        # Use explicit selections
        for sel in config.selections:
            if sel.selected:
                # Verify table is available
                matching = [
                    t for t in available_tables
                    if t.file_path == sel.file_path
                    and t.table_name == sel.table_name
                    and t.status == TableAvailabilityStatus.AVAILABLE
                ]
                if matching:
                    selected.append(sel)

    # Compute deterministic ID
    selection_inputs = {
        "run_id": run_id,
        "tables": sorted([
            f"{s.file_path}:{s.table_name}"
            for s in selected
        ]),
    }
    selection_id = compute_stage_id(selection_inputs, prefix="sel_")

    return TableSelectionResult(
        selection_id=selection_id,
        selected_tables=selected,
        total_selected=len(selected),
        completed=True,
    )


def get_selected_file_table_map(
    result: TableSelectionResult,
) -> dict[str, list[str]]:
    """Convert selection result to file -> tables mapping.
    
    Returns:
        Dict mapping file paths to list of selected table names
    """
    mapping: dict[str, list[str]] = {}

    for sel in result.selected_tables:
        if sel.file_path not in mapping:
            mapping[sel.file_path] = []
        mapping[sel.file_path].append(sel.table_name)

    return mapping
