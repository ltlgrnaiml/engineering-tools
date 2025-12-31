"""Selection stage - file discovery and selection."""
from dataclasses import dataclass
from pathlib import Path

from apps.data_aggregator.backend.adapters import create_default_registry


@dataclass
class FileInfo:
    """Information about a discovered file."""
    path: Path
    name: str
    extension: str
    size_bytes: int
    tables: list[str]


@dataclass
class SelectionResult:
    """Result of selection stage."""
    discovered_files: list[FileInfo]
    selected_files: list[Path]
    completed: bool = True


async def _get_tables_for_file(adapter, file_path: Path) -> list[str]:
    """Get tables/sheets from a file using async probe_schema.
    
    For multi-sheet formats (Excel), returns sheet names.
    For single-table formats, returns the filename.
    """
    if adapter.metadata.capabilities.supports_multiple_sheets:
        result = await adapter.probe_schema(str(file_path))
        if result.sheets:
            return [sheet.sheet_name for sheet in result.sheets]
    return [file_path.name]


async def discover_files(
    source_paths: list[Path],
    recursive: bool = True,
) -> list[FileInfo]:
    """Discover supported files in source paths.
    
    Args:
        source_paths: List of paths to search (files or directories)
        recursive: Whether to search recursively in directories
        
    Returns:
        List of discovered file information
    """
    registry = create_default_registry()

    # Get supported extensions from all registered adapters
    supported: set[str] = set()
    for meta in registry.list_adapters():
        supported.update(meta.file_extensions)

    discovered: list[FileInfo] = []

    for source in source_paths:
        if source.is_file():
            if source.suffix.lower() in supported:
                adapter = registry.get_adapter_for_file(str(source))
                tables = await _get_tables_for_file(adapter, source)
                discovered.append(FileInfo(
                    path=source,
                    name=source.name,
                    extension=source.suffix.lower(),
                    size_bytes=source.stat().st_size,
                    tables=tables,
                ))
        elif source.is_dir():
            pattern = "**/*" if recursive else "*"
            for file_path in source.glob(pattern):
                if file_path.is_file() and file_path.suffix.lower() in supported:
                    try:
                        adapter = registry.get_adapter_for_file(str(file_path))
                        tables = await _get_tables_for_file(adapter, file_path)
                        discovered.append(FileInfo(
                            path=file_path,
                            name=file_path.name,
                            extension=file_path.suffix.lower(),
                            size_bytes=file_path.stat().st_size,
                            tables=tables,
                        ))
                    except Exception:
                        # Skip files that can't be read
                        continue

    return discovered


async def execute_selection(
    source_paths: list[Path],
    selected_files: list[Path] | None = None,
    recursive: bool = True,
) -> SelectionResult:
    """Execute selection stage.
    
    Args:
        source_paths: Paths to search for files
        selected_files: Optional pre-selected files
        recursive: Whether to search recursively
        
    Returns:
        SelectionResult with discovered and selected files
    """
    discovered = await discover_files(source_paths, recursive)

    if selected_files is None:
        # Default: select all discovered files
        selected_files = [f.path for f in discovered]

    return SelectionResult(
        discovered_files=discovered,
        selected_files=selected_files,
        completed=True,
    )
