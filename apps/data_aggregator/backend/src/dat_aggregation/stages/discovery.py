"""Discovery stage - scan and discover available files.

Per ADR-0001-DAT: Discovery is the first stage in the 8-stage pipeline,
making the implicit file scan explicit.

This stage scans a directory for supported files and returns metadata
about each discovered file.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from shared.utils.stage_id import compute_stage_id
from apps.data_aggregator.backend.adapters import create_default_registry

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


@dataclass
class DiscoveredFile:
    """Information about a discovered file."""
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_at: datetime | None
    adapter_name: str | None = None
    is_supported: bool = True
    error: str | None = None


@dataclass
class DiscoveryConfig:
    """Configuration for discovery stage."""
    root_path: Path
    recursive: bool = True
    extensions: list[str] | None = None  # None = all supported
    exclude_patterns: list[str] = field(default_factory=list)
    max_files: int | None = None


@dataclass
class DiscoveryResult:
    """Result of discovery stage."""
    discovery_id: str
    root_path: str
    files: list[DiscoveredFile]
    total_files: int
    supported_files: int
    unsupported_files: int
    total_size_bytes: int
    completed: bool = True
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


async def execute_discovery(
    run_id: str,
    config: DiscoveryConfig,
) -> DiscoveryResult:
    """Execute discovery stage to scan for files.

    Per ADR-0001-DAT: Discovery scans the root path and returns
    metadata about discovered files.

    Args:
        run_id: DAT run ID.
        config: Discovery configuration.

    Returns:
        DiscoveryResult with discovered files.
    """
    files: list[DiscoveredFile] = []
    registry = create_default_registry()
    
    # Get supported extensions from all registered adapters
    supported_extensions: set[str] = set()
    for meta in registry.list_adapters():
        supported_extensions.update(meta.file_extensions)

    # Determine which extensions to scan for
    if config.extensions:
        target_extensions = {ext.lower() for ext in config.extensions}
    else:
        target_extensions = supported_extensions

    # Scan for files
    root = config.root_path
    if not root.exists():
        logger.warning(f"Discovery root path does not exist: {root}")
        return DiscoveryResult(
            discovery_id=compute_stage_id({"run_id": run_id, "root": str(root)}, prefix="disc_"),
            root_path=str(root),
            files=[],
            total_files=0,
            supported_files=0,
            unsupported_files=0,
            total_size_bytes=0,
            completed=True,
        )

    # Get all files
    if config.recursive:
        all_files = list(root.rglob("*"))
    else:
        all_files = list(root.glob("*"))

    # Filter to files only (not directories)
    all_files = [f for f in all_files if f.is_file()]

    # Apply max_files limit if specified
    if config.max_files and len(all_files) > config.max_files:
        all_files = all_files[:config.max_files]

    total_size = 0

    for file_path in all_files:
        ext = file_path.suffix.lower()

        # Check exclusion patterns
        excluded = False
        for pattern in config.exclude_patterns:
            if pattern in str(file_path):
                excluded = True
                break

        if excluded:
            continue

        # Get file metadata
        try:
            stat = file_path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        except OSError as e:
            files.append(DiscoveredFile(
                path=str(file_path),
                name=file_path.name,
                extension=ext,
                size_bytes=0,
                modified_at=None,
                is_supported=False,
                error=str(e),
            ))
            continue

        total_size += size

        # Check if extension is supported
        is_supported = ext in target_extensions

        # Get adapter name if supported
        adapter_name = None
        if is_supported:
            try:
                adapter = registry.get_adapter_for_file(str(file_path))
                adapter_name = adapter.metadata.name
            except Exception:
                is_supported = False

        files.append(DiscoveredFile(
            path=str(file_path),
            name=file_path.name,
            extension=ext,
            size_bytes=size,
            modified_at=modified,
            adapter_name=adapter_name,
            is_supported=is_supported,
        ))

    # Compute deterministic ID
    discovery_id = compute_stage_id({
        "run_id": run_id,
        "root": str(root),
        "file_count": len(files),
        "recursive": config.recursive,
    }, prefix="disc_")

    supported_count = sum(1 for f in files if f.is_supported)

    logger.info(
        f"Discovery complete: {len(files)} files found, "
        f"{supported_count} supported"
    )

    return DiscoveryResult(
        discovery_id=discovery_id,
        root_path=str(root),
        files=files,
        total_files=len(files),
        supported_files=supported_count,
        unsupported_files=len(files) - supported_count,
        total_size_bytes=total_size,
        completed=True,
    )


def filter_supported_files(result: DiscoveryResult) -> list[DiscoveredFile]:
    """Filter discovery result to only supported files."""
    return [f for f in result.files if f.is_supported]


def get_files_by_extension(
    result: DiscoveryResult,
    extension: str,
) -> list[DiscoveredFile]:
    """Get files with a specific extension."""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return [f for f in result.files if f.extension == ext]
