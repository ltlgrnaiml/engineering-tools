"""Renderer factory for creating appropriate renderers based on shape type."""

import logging

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.renderers.base import BaseRenderer

logger = logging.getLogger(__name__)


class RendererFactory:
    """Factory for creating and managing renderers.

    Maintains a registry of available renderers and selects the appropriate
    one based on the parsed shape name.
    """

    def __init__(self) -> None:
        """Initialize the factory with an empty renderer registry."""
        self._renderers: list[BaseRenderer] = []
        self.logger = logging.getLogger(__name__)

    def register_renderer(self, renderer: BaseRenderer) -> None:
        """Register a renderer with the factory.

        Args:
            renderer: Renderer instance to register.
        """
        self._renderers.append(renderer)
        self.logger.info(f"Registered renderer: {renderer.__class__.__name__}")

    def get_renderer(self, parsed_name: ParsedShapeNameV2) -> BaseRenderer | None:
        """Get the appropriate renderer for a shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            Renderer instance if found, None otherwise.
        """
        for renderer in self._renderers:
            if renderer.can_render(parsed_name):
                self.logger.debug(
                    f"Selected {renderer.__class__.__name__} for renderer '{parsed_name.renderer}'"
                )
                return renderer

        self.logger.warning(f"No renderer found for renderer '{parsed_name.renderer}'")
        return None

    def get_all_renderers(self) -> list[BaseRenderer]:
        """Get all registered renderers.

        Returns:
            List of all renderer instances.
        """
        return self._renderers.copy()
