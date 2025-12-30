"""Adapter Registry for the Unified Rendering Engine.

Per ADR-0029: Output Target Adapters.

This module provides a registry pattern for output adapters,
allowing dynamic registration of renderers for different targets.
"""

from typing import TYPE_CHECKING

from shared.contracts.core.rendering import OutputTarget

if TYPE_CHECKING:
    from shared.rendering.adapters.base import BaseOutputAdapter

__version__ = "0.1.0"


class AdapterRegistry:
    """Global registry for output adapters.

    Provides a singleton-like registry for all output adapters.
    Tools can register custom adapters at startup.

    Usage:
        from shared.rendering.registry import AdapterRegistry

        # Register an adapter
        AdapterRegistry.register(OutputTarget.PNG, PNGAdapter())

        # Get an adapter
        adapter = AdapterRegistry.get(OutputTarget.PNG)
    """

    _adapters: dict[OutputTarget, "BaseOutputAdapter"] = {}
    _initialized: bool = False

    @classmethod
    def register(
        cls,
        target: OutputTarget,
        adapter: "BaseOutputAdapter",
        replace: bool = False,
    ) -> None:
        """Register an output adapter for a target.

        Args:
            target: Output target (PNG, SVG, PPTX, etc.)
            adapter: Adapter implementation.
            replace: If True, replace existing adapter. Otherwise raise error.

        Raises:
            ValueError: If adapter already registered and replace=False.
        """
        if target in cls._adapters and not replace:
            raise ValueError(
                f"Adapter already registered for {target}. "
                f"Use replace=True to override."
            )
        cls._adapters[target] = adapter

    @classmethod
    def get(cls, target: OutputTarget) -> "BaseOutputAdapter | None":
        """Get the registered adapter for a target.

        Args:
            target: Output target to get adapter for.

        Returns:
            Registered adapter or None if not found.
        """
        return cls._adapters.get(target)

    @classmethod
    def get_or_raise(cls, target: OutputTarget) -> "BaseOutputAdapter":
        """Get adapter or raise error if not found.

        Args:
            target: Output target to get adapter for.

        Returns:
            Registered adapter.

        Raises:
            ValueError: If no adapter registered for target.
        """
        adapter = cls._adapters.get(target)
        if adapter is None:
            available = list(cls._adapters.keys())
            raise ValueError(
                f"No adapter registered for {target}. "
                f"Available: {available}"
            )
        return adapter

    @classmethod
    def list_targets(cls) -> list[OutputTarget]:
        """List all registered output targets."""
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, target: OutputTarget) -> bool:
        """Check if an adapter is registered for target."""
        return target in cls._adapters

    @classmethod
    def unregister(cls, target: OutputTarget) -> bool:
        """Unregister an adapter.

        Args:
            target: Output target to unregister.

        Returns:
            True if adapter was removed, False if not found.
        """
        if target in cls._adapters:
            del cls._adapters[target]
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (useful for testing)."""
        cls._adapters.clear()
        cls._initialized = False

    @classmethod
    def initialize_defaults(cls) -> None:
        """Initialize default adapters.

        Called at startup to register built-in adapters.
        """
        if cls._initialized:
            return

        # Import and register default adapters
        try:
            from shared.rendering.adapters.png_adapter import PNGAdapter
            cls.register(OutputTarget.PNG, PNGAdapter(), replace=True)
        except ImportError:
            pass  # PNG adapter not available

        try:
            from shared.rendering.adapters.svg_adapter import SVGAdapter
            cls.register(OutputTarget.SVG, SVGAdapter(), replace=True)
        except ImportError:
            pass  # SVG adapter not available

        try:
            from shared.rendering.adapters.json_adapter import JSONAdapter
            cls.register(OutputTarget.WEB_JSON, JSONAdapter(), replace=True)
        except ImportError:
            pass  # JSON adapter not available

        cls._initialized = True


# Convenience functions
def register_adapter(
    target: OutputTarget,
    adapter: "BaseOutputAdapter",
    replace: bool = False,
) -> None:
    """Register an output adapter (convenience function)."""
    AdapterRegistry.register(target, adapter, replace)


def get_adapter(target: OutputTarget) -> "BaseOutputAdapter | None":
    """Get an output adapter (convenience function)."""
    return AdapterRegistry.get(target)
