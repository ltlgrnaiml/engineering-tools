"""Adapter Registry for DAT file adapters.

Per ADR-0012: AdapterFactory pattern for extensible file format support.
Per SPEC-0026: Adapter Interface & Registry specification.

This module provides the central registry for file adapters. Adapters are
registered at startup and selected via file extension or MIME type.

Usage:
    from apps.data_aggregator.backend.adapters import create_default_registry

    registry = create_default_registry()
    adapter = registry.get_adapter_for_file("data.csv")
    df, result = await adapter.read_dataframe("data.csv")
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from shared.contracts.dat.adapter import (
    AdapterMetadata,
    AdapterRegistryEntry,
    AdapterRegistryState,
)

if TYPE_CHECKING:
    from shared.contracts.dat.adapter import BaseFileAdapter

__version__ = "1.0.0"


class AdapterNotFoundError(Exception):
    """Raised when no adapter can be found for a file format.

    Attributes:
        file_path: The file path that couldn't be matched.
        adapter_id: The adapter ID that was requested (if any).
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        adapter_id: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message.
            file_path: The file path that couldn't be matched.
            adapter_id: The adapter ID that was requested.
        """
        super().__init__(message)
        self.file_path = file_path
        self.adapter_id = adapter_id


class AdapterRegistry:
    """Central registry for file adapters.

    Per ADR-0012: Adapters are selected via handles-first pattern.
    The registry uses file extensions and MIME types to auto-select adapters.

    Attributes:
        _adapters: Dictionary mapping adapter_id to adapter instance.
        _extension_map: Dictionary mapping file extension to adapter_id.
        _mime_map: Dictionary mapping MIME type to adapter_id.

    Example:
        >>> registry = AdapterRegistry()
        >>> registry.register(CSVAdapter())
        >>> adapter = registry.get_adapter_for_file("data.csv")
        >>> df, result = await adapter.read_dataframe("data.csv")
    """

    def __init__(self) -> None:
        """Initialize an empty adapter registry."""
        self._adapters: dict[str, "BaseFileAdapter"] = {}
        self._extension_map: dict[str, str] = {}
        self._mime_map: dict[str, str] = {}
        self._registered_at: dict[str, datetime] = {}

    def register(
        self,
        adapter: "BaseFileAdapter",
        *,
        is_builtin: bool = True,
    ) -> None:
        """Register an adapter in the registry.

        Args:
            adapter: The adapter instance to register.
            is_builtin: Whether this is a built-in adapter (default: True).

        Raises:
            ValueError: If an adapter with the same ID is already registered.

        Example:
            >>> registry.register(CSVAdapter())
            >>> registry.register(ExcelAdapter())
        """
        meta = adapter.metadata
        adapter_id = meta.adapter_id

        if adapter_id in self._adapters:
            raise ValueError(
                f"Adapter '{adapter_id}' is already registered. "
                "Use a different adapter_id or unregister the existing adapter first."
            )

        # Register the adapter
        self._adapters[adapter_id] = adapter
        self._registered_at[adapter_id] = datetime.now(timezone.utc)

        # Map file extensions to this adapter
        for ext in meta.file_extensions:
            ext_lower = ext.lower()
            if not ext_lower.startswith("."):
                ext_lower = f".{ext_lower}"
            self._extension_map[ext_lower] = adapter_id

        # Map MIME types to this adapter
        for mime in meta.mime_types:
            self._mime_map[mime.lower()] = adapter_id

    def unregister(self, adapter_id: str) -> None:
        """Unregister an adapter from the registry.

        Args:
            adapter_id: The ID of the adapter to unregister.

        Raises:
            AdapterNotFoundError: If the adapter is not registered.
        """
        if adapter_id not in self._adapters:
            raise AdapterNotFoundError(
                f"Adapter '{adapter_id}' is not registered.",
                adapter_id=adapter_id,
            )

        adapter = self._adapters[adapter_id]
        meta = adapter.metadata

        # Remove extension mappings
        for ext in meta.file_extensions:
            ext_lower = ext.lower()
            if not ext_lower.startswith("."):
                ext_lower = f".{ext_lower}"
            if self._extension_map.get(ext_lower) == adapter_id:
                del self._extension_map[ext_lower]

        # Remove MIME mappings
        for mime in meta.mime_types:
            if self._mime_map.get(mime.lower()) == adapter_id:
                del self._mime_map[mime.lower()]

        # Remove adapter
        del self._adapters[adapter_id]
        del self._registered_at[adapter_id]

    def get_adapter(self, adapter_id: str) -> "BaseFileAdapter":
        """Get an adapter by its ID.

        Args:
            adapter_id: The adapter ID (e.g., 'csv', 'excel', 'json').

        Returns:
            The adapter instance.

        Raises:
            AdapterNotFoundError: If no adapter with that ID is registered.

        Example:
            >>> adapter = registry.get_adapter("csv")
        """
        if adapter_id not in self._adapters:
            available = ", ".join(sorted(self._adapters.keys()))
            raise AdapterNotFoundError(
                f"No adapter found with ID '{adapter_id}'. "
                f"Available adapters: {available or 'none'}",
                adapter_id=adapter_id,
            )
        return self._adapters[adapter_id]

    def get_adapter_for_file(
        self,
        file_path: str,
        mime_type: str | None = None,
    ) -> "BaseFileAdapter":
        """Auto-select an adapter for a file based on extension or MIME type.

        MIME type takes precedence over file extension if provided.

        Args:
            file_path: Path to the file (only extension is used).
            mime_type: Optional MIME type override.

        Returns:
            The appropriate adapter for the file format.

        Raises:
            AdapterNotFoundError: If no adapter can handle the file format.

        Example:
            >>> adapter = registry.get_adapter_for_file("data.csv")
            >>> adapter = registry.get_adapter_for_file("data", mime_type="text/csv")
        """
        # Try MIME type first (if provided)
        if mime_type:
            mime_lower = mime_type.lower()
            if mime_lower in self._mime_map:
                adapter_id = self._mime_map[mime_lower]
                return self._adapters[adapter_id]

        # Fall back to file extension
        ext = Path(file_path).suffix.lower()
        if ext in self._extension_map:
            adapter_id = self._extension_map[ext]
            return self._adapters[adapter_id]

        # No adapter found
        available_exts = ", ".join(sorted(self._extension_map.keys()))
        raise AdapterNotFoundError(
            f"No adapter found for file '{file_path}' (extension: '{ext}'). "
            f"Supported extensions: {available_exts or 'none'}",
            file_path=file_path,
        )

    def list_adapters(self) -> list[AdapterMetadata]:
        """List metadata for all registered adapters.

        Returns:
            List of AdapterMetadata for all registered adapters.

        Example:
            >>> for meta in registry.list_adapters():
            ...     print(f"{meta.adapter_id}: {meta.name}")
        """
        return [adapter.metadata for adapter in self._adapters.values()]

    def get_state(self) -> AdapterRegistryState:
        """Get the current state of the registry for serialization.

        Useful for DevTools display and debugging.

        Returns:
            AdapterRegistryState with all registry information.
        """
        entries = []
        for adapter_id, adapter in self._adapters.items():
            entries.append(
                AdapterRegistryEntry(
                    adapter_id=adapter_id,
                    metadata=adapter.metadata,
                    registered_at=self._registered_at[adapter_id],
                    is_builtin=True,  # All current adapters are built-in
                )
            )

        return AdapterRegistryState(
            adapters=entries,
            extension_map=dict(self._extension_map),
            mime_map=dict(self._mime_map),
            last_updated=datetime.now(timezone.utc),
        )

    def __len__(self) -> int:
        """Return the number of registered adapters."""
        return len(self._adapters)

    def __contains__(self, adapter_id: str) -> bool:
        """Check if an adapter ID is registered."""
        return adapter_id in self._adapters
