"""Memory manager for DAT large file streaming.

This module implements memory management for large file processing per ADR-0040
and SPEC-DAT-0004. It tracks memory usage, enforces limits, and triggers
garbage collection when needed.

Key features:
- Track current memory usage via process monitoring
- Enforce configurable memory limits (default: 200MB)
- Automatic garbage collection when approaching limits
- Spill-to-disk support for extreme cases
"""

from __future__ import annotations

import gc
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

import psutil

__version__ = "1.0.0"


class MemoryTier(str, Enum):
    """File size tiers per SPEC-DAT-0004."""

    SMALL = "small"  # 0-100KB: eager load
    MEDIUM = "medium"  # 100KB-10MB: eager load with progress
    LARGE = "large"  # 10MB-100MB: streaming chunks
    VERY_LARGE = "very_large"  # 100MB-1GB: streaming with limits
    MASSIVE = "massive"  # > 1GB: partitioned streaming


@dataclass
class MemoryConfig:
    """Configuration for memory management per SPEC-DAT-0004.

    Attributes:
        max_memory_mb: Maximum memory usage allowed (default: 200MB).
        warning_threshold_pct: Percentage at which to warn (default: 80%).
        gc_threshold_pct: Percentage at which to trigger GC (default: 70%).
        chunk_size_rows: Default chunk size for streaming (default: 50000).
        schema_probe_rows: Rows to read for schema inference (default: 1000).
        spill_to_disk: Enable disk spilling when memory exceeded.
        spill_directory: Directory for temporary spill files.
    """

    max_memory_mb: int = 200
    warning_threshold_pct: float = 80.0
    gc_threshold_pct: float = 70.0
    chunk_size_rows: int = 50000
    schema_probe_rows: int = 1000
    spill_to_disk: bool = True
    spill_directory: Path | None = None

    def __post_init__(self):
        """Initialize spill directory if not provided."""
        if self.spill_directory is None:
            self.spill_directory = Path(tempfile.gettempdir()) / "dat_spill"


@dataclass
class MemorySnapshot:
    """Point-in-time memory usage snapshot.

    Attributes:
        timestamp: When the snapshot was taken (ISO-8601 UTC).
        process_memory_mb: Memory used by this process.
        available_memory_mb: System available memory.
        usage_pct: Percentage of configured limit used.
        tier: Current memory tier based on usage.
    """

    timestamp: datetime
    process_memory_mb: float
    available_memory_mb: float
    usage_pct: float
    tier: MemoryTier

    @classmethod
    def capture(cls, config: MemoryConfig) -> MemorySnapshot:
        """Capture current memory state."""
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / (1024 * 1024)  # MB
        available = psutil.virtual_memory().available / (1024 * 1024)  # MB
        usage_pct = (process_memory / config.max_memory_mb) * 100

        return cls(
            timestamp=datetime.now(timezone.utc),
            process_memory_mb=round(process_memory, 2),
            available_memory_mb=round(available, 2),
            usage_pct=round(usage_pct, 1),
            tier=cls._determine_tier(usage_pct),
        )

    @staticmethod
    def _determine_tier(usage_pct: float) -> MemoryTier:
        """Determine memory tier based on usage percentage."""
        if usage_pct < 25:
            return MemoryTier.SMALL
        elif usage_pct < 50:
            return MemoryTier.MEDIUM
        elif usage_pct < 75:
            return MemoryTier.LARGE
        elif usage_pct < 90:
            return MemoryTier.VERY_LARGE
        else:
            return MemoryTier.MASSIVE


@dataclass
class FileSizeStrategy:
    """Strategy for handling files based on size per SPEC-DAT-0004.

    Attributes:
        tier: The file size tier.
        strategy: Processing strategy name.
        preview_rows: Number of rows for preview (None = all).
        chunk_size: Chunk size for streaming modes.
        memory_cap_mb: Memory cap for this tier.
    """

    tier: MemoryTier
    strategy: str
    preview_rows: int | None
    chunk_size: int | None
    memory_cap_mb: int


# File size tier configurations per SPEC-DAT-0004
FILE_SIZE_STRATEGIES: dict[MemoryTier, FileSizeStrategy] = {
    MemoryTier.SMALL: FileSizeStrategy(
        tier=MemoryTier.SMALL,
        strategy="eager_load",
        preview_rows=None,  # All rows
        chunk_size=None,
        memory_cap_mb=10,
    ),
    MemoryTier.MEDIUM: FileSizeStrategy(
        tier=MemoryTier.MEDIUM,
        strategy="eager_load_with_progress",
        preview_rows=None,  # All rows
        chunk_size=None,
        memory_cap_mb=50,
    ),
    MemoryTier.LARGE: FileSizeStrategy(
        tier=MemoryTier.LARGE,
        strategy="streaming_chunks",
        preview_rows=10000,
        chunk_size=50000,
        memory_cap_mb=50,
    ),
    MemoryTier.VERY_LARGE: FileSizeStrategy(
        tier=MemoryTier.VERY_LARGE,
        strategy="streaming_with_limits",
        preview_rows=5000,
        chunk_size=50000,
        memory_cap_mb=100,
    ),
    MemoryTier.MASSIVE: FileSizeStrategy(
        tier=MemoryTier.MASSIVE,
        strategy="partitioned_streaming",
        preview_rows=1000,
        chunk_size=100000,
        memory_cap_mb=200,
    ),
}


# Threshold in bytes (10MB per ADR-0040)
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024


@dataclass
class MemoryManager:
    """Manages memory usage for DAT file processing.

    Per ADR-0040 and SPEC-DAT-0004, this class:
    - Tracks current memory usage
    - Enforces memory limits
    - Triggers garbage collection
    - Supports spill to disk

    Attributes:
        config: Memory configuration.
        _snapshots: History of memory snapshots for monitoring.
        _gc_count: Number of garbage collections triggered.
        _spill_files: List of temporary spill files created.
    """

    config: MemoryConfig = field(default_factory=MemoryConfig)
    _snapshots: list[MemorySnapshot] = field(default_factory=list)
    _gc_count: int = 0
    _spill_files: list[Path] = field(default_factory=list)
    _warning_callback: Callable[[str], None] | None = None

    def set_warning_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for memory warnings."""
        self._warning_callback = callback

    def get_current_usage(self) -> MemorySnapshot:
        """Get current memory usage snapshot."""
        snapshot = MemorySnapshot.capture(self.config)
        self._snapshots.append(snapshot)

        # Keep only last 100 snapshots
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]

        return snapshot

    def check_and_manage(self) -> MemorySnapshot:
        """Check memory and take action if needed.

        Returns:
            Current memory snapshot after any management actions.
        """
        snapshot = self.get_current_usage()

        # Trigger GC if approaching limit
        if snapshot.usage_pct >= self.config.gc_threshold_pct:
            self._trigger_gc()
            snapshot = self.get_current_usage()

        # Warn if still high
        if snapshot.usage_pct >= self.config.warning_threshold_pct:
            msg = f"Memory usage at {snapshot.usage_pct}% ({snapshot.process_memory_mb}MB)"
            if self._warning_callback:
                self._warning_callback(msg)

        return snapshot

    def _trigger_gc(self) -> None:
        """Trigger garbage collection."""
        gc.collect()
        self._gc_count += 1

    def get_strategy_for_file(self, file_path: Path) -> FileSizeStrategy:
        """Determine processing strategy based on file size.

        Per ADR-0040: Files > 10MB use streaming mode.

        Args:
            file_path: Path to the file.

        Returns:
            FileSizeStrategy for the file.
        """
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        if size_mb < 0.1:
            return FILE_SIZE_STRATEGIES[MemoryTier.SMALL]
        elif size_mb < 10:
            return FILE_SIZE_STRATEGIES[MemoryTier.MEDIUM]
        elif size_mb < 100:
            return FILE_SIZE_STRATEGIES[MemoryTier.LARGE]
        elif size_mb < 1000:
            return FILE_SIZE_STRATEGIES[MemoryTier.VERY_LARGE]
        else:
            return FILE_SIZE_STRATEGIES[MemoryTier.MASSIVE]

    def should_stream(self, file_path: Path) -> bool:
        """Check if file should use streaming mode.

        Per ADR-0040: Files > 10MB use streaming.

        Args:
            file_path: Path to the file.

        Returns:
            True if streaming should be used.
        """
        return file_path.stat().st_size > STREAMING_THRESHOLD_BYTES

    def get_chunk_size(self, file_path: Path) -> int:
        """Get appropriate chunk size for file.

        Args:
            file_path: Path to the file.

        Returns:
            Chunk size in rows.
        """
        strategy = self.get_strategy_for_file(file_path)
        return strategy.chunk_size or self.config.chunk_size_rows

    def get_preview_rows(self, file_path: Path) -> int | None:
        """Get preview row count for file.

        Per SPEC-DAT-0004:
        - 10-100MB: 10,000 row preview
        - 100MB-1GB: 5,000 row preview
        - > 1GB: 1,000 row preview

        Args:
            file_path: Path to the file.

        Returns:
            Number of preview rows, or None for all rows.
        """
        strategy = self.get_strategy_for_file(file_path)
        return strategy.preview_rows

    def create_spill_file(self, prefix: str = "dat_spill_") -> Path:
        """Create a temporary spill file.

        Args:
            prefix: Prefix for the spill file name.

        Returns:
            Path to the spill file.
        """
        if self.config.spill_directory:
            self.config.spill_directory.mkdir(parents=True, exist_ok=True)
            spill_file = self.config.spill_directory / f"{prefix}{len(self._spill_files)}.tmp"
        else:
            fd, path = tempfile.mkstemp(prefix=prefix, suffix=".tmp")
            os.close(fd)
            spill_file = Path(path)

        self._spill_files.append(spill_file)
        return spill_file

    def cleanup_spill_files(self) -> int:
        """Clean up all spill files.

        Returns:
            Number of files cleaned up.
        """
        count = 0
        for spill_file in self._spill_files:
            if spill_file.exists():
                spill_file.unlink()
                count += 1
        self._spill_files.clear()
        return count

    def get_stats(self) -> dict:
        """Get memory manager statistics.

        Returns:
            Dictionary with memory stats.
        """
        current = self.get_current_usage()
        return {
            "current_memory_mb": current.process_memory_mb,
            "available_memory_mb": current.available_memory_mb,
            "usage_pct": current.usage_pct,
            "max_memory_mb": self.config.max_memory_mb,
            "gc_count": self._gc_count,
            "spill_files_count": len(self._spill_files),
            "snapshots_count": len(self._snapshots),
        }

    def __enter__(self) -> MemoryManager:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup spill files."""
        self.cleanup_spill_files()


# Module-level singleton for convenience
_default_manager: MemoryManager | None = None


def get_memory_manager(config: MemoryConfig | None = None) -> MemoryManager:
    """Get the default memory manager instance.

    Args:
        config: Optional configuration. If provided on first call, sets config.

    Returns:
        The default MemoryManager instance.
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = MemoryManager(config=config or MemoryConfig())
    return _default_manager


def reset_memory_manager() -> None:
    """Reset the default memory manager (for testing)."""
    global _default_manager
    if _default_manager:
        _default_manager.cleanup_spill_files()
    _default_manager = None
