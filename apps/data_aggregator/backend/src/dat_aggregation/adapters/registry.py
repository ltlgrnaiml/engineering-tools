"""Adapter registry for extensible file format support.

Per ADR-0011: Adapters are dynamically registrable and selected via handles-first pattern.

This module provides:
- Dynamic adapter registration
- Capability metadata
- Catalog diagnostics
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Type

from .base import FileAdapter

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


@dataclass
class AdapterCapabilities:
    """Capabilities metadata for an adapter per ADR-0011.

    Documents what an adapter can do for catalog diagnostics.
    """

    adapter_name: str
    extensions: list[str]
    can_read: bool = True
    can_write: bool = False
    supports_tables: bool = False
    supports_preview: bool = True
    supports_streaming: bool = False
    max_file_size_mb: int | None = None
    description: str = ""
    version: str = "1.0.0"
    extra: dict[str, Any] = field(default_factory=dict)


class AdapterRegistry:
    """Extensible adapter registry per ADR-0011.

    Provides dynamic adapter registration and selection using
    the handles-first pattern.

    Example:
        >>> registry = AdapterRegistry()
        >>> registry.register(CSVAdapter)
        >>> registry.register(ExcelAdapter, priority=10)
        >>> adapter = registry.get_adapter(Path("data.csv"))
    """

    _instance: "AdapterRegistry | None" = None

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._adapters: dict[str, tuple[Type[FileAdapter], int]] = {}
        self._extension_map: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "AdapterRegistry":
        """Get singleton registry instance."""
        if cls._instance is None:
            cls._instance = AdapterRegistry()
        return cls._instance

    def register(
        self,
        adapter_class: Type[FileAdapter],
        priority: int = 0,
    ) -> None:
        """Register an adapter by its extensions.

        Per ADR-0011: Adapters are registered with their supported extensions.

        Args:
            adapter_class: FileAdapter subclass to register.
            priority: Higher priority adapters are checked first (default 0).
        """
        adapter_name = adapter_class.__name__

        # Check if adapter has required attributes
        if not hasattr(adapter_class, "EXTENSIONS"):
            raise ValueError(f"Adapter {adapter_name} must define EXTENSIONS")
        if not hasattr(adapter_class, "can_handle"):
            raise ValueError(f"Adapter {adapter_name} must define can_handle()")

        # Register adapter
        self._adapters[adapter_name] = (adapter_class, priority)

        # Map extensions to adapter
        for ext in adapter_class.EXTENSIONS:
            ext_lower = ext.lower()
            existing = self._extension_map.get(ext_lower)
            if existing:
                existing_priority = self._adapters[existing][1]
                if priority > existing_priority:
                    self._extension_map[ext_lower] = adapter_name
                    logger.debug(
                        f"Extension {ext} remapped from {existing} to {adapter_name}"
                    )
            else:
                self._extension_map[ext_lower] = adapter_name

        logger.info(
            f"Registered adapter: {adapter_name} for extensions {adapter_class.EXTENSIONS}"
        )

    def unregister(self, adapter_name: str) -> bool:
        """Unregister an adapter by name.

        Args:
            adapter_name: Name of adapter class to unregister.

        Returns:
            True if adapter was unregistered, False if not found.
        """
        if adapter_name not in self._adapters:
            return False

        adapter_class, _ = self._adapters[adapter_name]

        # Remove extension mappings
        for ext in adapter_class.EXTENSIONS:
            ext_lower = ext.lower()
            if self._extension_map.get(ext_lower) == adapter_name:
                del self._extension_map[ext_lower]

        del self._adapters[adapter_name]
        logger.info(f"Unregistered adapter: {adapter_name}")
        return True

    def get_adapter(self, path: Path) -> Type[FileAdapter]:
        """Get appropriate adapter for file using handles-first pattern.

        Per ADR-0011: Adapters are selected via handles-first registry.

        Args:
            path: Path to the file.

        Returns:
            Adapter class that can handle the file.

        Raises:
            ValueError: If no adapter can handle the file.
        """
        # Sort adapters by priority (highest first)
        sorted_adapters = sorted(
            self._adapters.values(),
            key=lambda x: x[1],
            reverse=True,
        )

        for adapter_class, _ in sorted_adapters:
            if adapter_class.can_handle(path):
                return adapter_class

        raise ValueError(f"No adapter found for: {path}")

    def get_adapter_by_extension(self, extension: str) -> Type[FileAdapter] | None:
        """Get adapter by file extension.

        Args:
            extension: File extension (with or without leading dot).

        Returns:
            Adapter class or None if not found.
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        adapter_name = self._extension_map.get(ext)
        if adapter_name and adapter_name in self._adapters:
            return self._adapters[adapter_name][0]
        return None

    def get_capabilities(self, adapter_name: str) -> AdapterCapabilities | None:
        """Get capabilities metadata for an adapter.

        Args:
            adapter_name: Name of adapter class.

        Returns:
            AdapterCapabilities or None if not found.
        """
        if adapter_name not in self._adapters:
            return None

        adapter_class, _ = self._adapters[adapter_name]

        # Build capabilities from adapter attributes
        return AdapterCapabilities(
            adapter_name=adapter_name,
            extensions=list(adapter_class.EXTENSIONS),
            can_read=hasattr(adapter_class, "read"),
            can_write=hasattr(adapter_class, "write"),
            supports_tables=hasattr(adapter_class, "get_tables"),
            supports_preview=hasattr(adapter_class, "get_preview"),
            description=adapter_class.__doc__ or "",
            version=getattr(adapter_class, "__version__", "1.0.0"),
        )

    def get_catalog(self) -> dict[str, AdapterCapabilities]:
        """Get catalog of all registered adapters with capabilities.

        Per ADR-0011: Catalog diagnostics for adapter inspection.

        Returns:
            Dict mapping adapter names to their capabilities.
        """
        catalog = {}
        for adapter_name in self._adapters:
            caps = self.get_capabilities(adapter_name)
            if caps:
                catalog[adapter_name] = caps
        return catalog

    def get_supported_extensions(self) -> set[str]:
        """Get all supported file extensions."""
        return set(self._extension_map.keys())

    def list_adapters(self) -> list[str]:
        """List all registered adapter names."""
        return list(self._adapters.keys())

    def clear(self) -> None:
        """Clear all registered adapters."""
        self._adapters.clear()
        self._extension_map.clear()
        logger.info("Adapter registry cleared")


def register_builtin_adapters(registry: AdapterRegistry) -> None:
    """Register all built-in adapters.

    Args:
        registry: Registry to populate.
    """
    from .csv_adapter import CSVAdapter
    from .excel_adapter import ExcelAdapter
    from .json_adapter import JSONAdapter
    from .parquet_adapter import ParquetAdapter

    # Register in priority order (higher = checked first)
    registry.register(ParquetAdapter, priority=100)
    registry.register(ExcelAdapter, priority=50)
    registry.register(JSONAdapter, priority=30)
    registry.register(CSVAdapter, priority=10)  # CSV is fallback

    logger.info("Built-in adapters registered")


def get_default_registry() -> AdapterRegistry:
    """Get the default registry with built-in adapters registered.

    Returns:
        AdapterRegistry with all built-in adapters.
    """
    registry = AdapterRegistry.get_instance()
    if not registry.list_adapters():
        register_builtin_adapters(registry)
    return registry
