"""Adapter factory for multi-format file parsing.

Per ADR-0011: Adapters are selected via handles-first registry.
"""
from pathlib import Path
from typing import Type

import polars as pl

from .base import FileAdapter
from .registry import AdapterRegistry, get_default_registry


class AdapterFactory:
    """Factory for selecting and using file adapters.

    Per ADR-0011: Uses AdapterRegistry for dynamic adapter selection.
    """

    _registry: AdapterRegistry | None = None

    @classmethod
    def _get_registry(cls) -> AdapterRegistry:
        """Get the adapter registry (lazy initialization)."""
        if cls._registry is None:
            cls._registry = get_default_registry()
        return cls._registry

    @classmethod
    def register_adapter(
        cls,
        adapter_class: Type[FileAdapter],
        priority: int = 0,
    ) -> None:
        """Register a custom adapter.

        Per ADR-0011: Adapters are dynamically registrable.

        Args:
            adapter_class: FileAdapter subclass to register.
            priority: Higher priority adapters are checked first.
        """
        cls._get_registry().register(adapter_class, priority)

    @classmethod
    def get_adapter(cls, path: Path) -> Type[FileAdapter]:
        """Get appropriate adapter for file.

        Args:
            path: Path to the file.

        Returns:
            Adapter class that can handle the file.

        Raises:
            ValueError: If no adapter can handle the file.
        """
        return cls._get_registry().get_adapter(path)
    
    @classmethod
    def read_file(cls, path: Path, **options) -> pl.DataFrame:
        """Read file using appropriate adapter.
        
        Args:
            path: Path to the file
            **options: Additional options passed to adapter
            
        Returns:
            DataFrame with file contents
        """
        adapter = cls.get_adapter(path)
        return adapter.read(path, **options)
    
    @classmethod
    def get_tables(cls, path: Path) -> list[str]:
        """Get tables/sheets from file.
        
        Args:
            path: Path to the file
            
        Returns:
            List of table/sheet names
        """
        adapter = cls.get_adapter(path)
        return adapter.get_tables(path)
    
    @classmethod
    def get_preview(cls, path: Path, table: str | None = None, rows: int = 100) -> pl.DataFrame:
        """Get preview of table data.
        
        Args:
            path: Path to the file
            table: Optional table/sheet name
            rows: Number of rows to preview
            
        Returns:
            DataFrame with preview data
        """
        adapter = cls.get_adapter(path)
        return adapter.get_preview(path, table, rows)
    
    @classmethod
    def get_supported_extensions(cls) -> set[str]:
        """Get all supported file extensions."""
        return cls._get_registry().get_supported_extensions()

    @classmethod
    def get_adapter_catalog(cls) -> dict:
        """Get catalog of all registered adapters with capabilities.

        Per ADR-0011: Catalog diagnostics for adapter inspection.

        Returns:
            Dict mapping adapter names to their capabilities.
        """
        from .registry import AdapterCapabilities

        catalog = cls._get_registry().get_catalog()
        return {
            name: {
                "extensions": caps.extensions,
                "can_read": caps.can_read,
                "can_write": caps.can_write,
                "supports_tables": caps.supports_tables,
                "supports_preview": caps.supports_preview,
                "description": caps.description,
            }
            for name, caps in catalog.items()
        }
