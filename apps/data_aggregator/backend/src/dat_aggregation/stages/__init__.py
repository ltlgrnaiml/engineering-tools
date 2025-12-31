"""DAT pipeline stages."""

from shared.contracts.dat.table_status import TableAvailabilityStatus

from .context import ContextConfig, ContextResult, apply_context_to_dataframe, execute_context
from .export import execute_export
from .parse import CancellationToken, ParseConfig, ParseResult, execute_parse
from .preview import PreviewConfig, PreviewResult, TablePreview, execute_preview
from .selection import FileInfo, SelectionResult, discover_files, execute_selection
from .table_availability import (
    TableAvailabilityResult,
    TableInfo,
    execute_table_availability,
)
from .table_selection import (
    TableSelection,
    TableSelectionConfig,
    TableSelectionResult,
    execute_table_selection,
    get_selected_file_table_map,
)

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
