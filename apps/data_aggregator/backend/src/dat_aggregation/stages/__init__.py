"""DAT pipeline stages."""

from .selection import FileInfo, SelectionResult, execute_selection, discover_files
from .context import ContextConfig, ContextResult, execute_context, apply_context_to_dataframe
from .table_availability import (
    TableInfo,
    TableAvailabilityResult,
    execute_table_availability,
)
from shared.contracts.dat.table_status import TableAvailabilityStatus
from .table_selection import (
    TableSelection,
    TableSelectionConfig,
    TableSelectionResult,
    execute_table_selection,
    get_selected_file_table_map,
)
from .preview import PreviewConfig, TablePreview, PreviewResult, execute_preview
from .parse import ParseConfig, ParseResult, CancellationToken, execute_parse
from .export import execute_export

__all__ = [
    # Selection
    "FileInfo",
    "SelectionResult",
    "execute_selection",
    "discover_files",
    # Context
    "ContextConfig",
    "ContextResult",
    "execute_context",
    "apply_context_to_dataframe",
    # Table Availability
    "TableAvailabilityStatus",
    "TableInfo",
    "TableAvailabilityResult",
    "execute_table_availability",
    # Table Selection
    "TableSelection",
    "TableSelectionConfig",
    "TableSelectionResult",
    "execute_table_selection",
    "get_selected_file_table_map",
    # Preview
    "PreviewConfig",
    "TablePreview",
    "PreviewResult",
    "execute_preview",
    # Parse
    "ParseConfig",
    "ParseResult",
    "CancellationToken",
    "execute_parse",
    # Export
    "execute_export",
]
