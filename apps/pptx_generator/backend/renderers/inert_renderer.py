"""Inert and image renderers for non-data shapes."""

import logging
from pathlib import Path

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext

logger = logging.getLogger(__name__)


class InertRenderer(BaseRenderer):
    """Renderer for inert shapes that should not be modified."""

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is an inert shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is 'inert'.
        """
        return parsed_name.renderer == "inert"

    async def render(self, context: RenderContext) -> None:
        """Do nothing - inert shapes are not modified.

        Args:
            context: Rendering context.
        """
        self.logger.debug(f"Skipping inert shape: {context.shape.name}")
        pass


class ImageRenderer(BaseRenderer):
    """Renderer for image shapes that insert external images."""

    def can_render(self, parsed_name: ParsedShapeNameV2) -> bool:
        """Check if this is an image shape.

        Args:
            parsed_name: Parsed shape name.

        Returns:
            True if renderer is 'image'.
        """
        return parsed_name.renderer == "image"

    async def render(self, context: RenderContext) -> None:
        """Insert image into shape.

        Args:
            context: Rendering context.
        """
        shape = context.shape

        # Get image path from parameters or metadata
        image_path = self._get_image_path(context)

        if not image_path or not Path(image_path).exists():
            self.logger.warning(f"Image file not found for {shape.name}: {image_path}")
            return

        try:
            # Get shape position and size
            left = shape.left
            top = shape.top
            width = shape.width
            height = shape.height
            shape_name = shape.name

            # Get parent slide shapes collection
            slide_shapes = shape._parent

            # Remove old shape
            sp = shape.element
            sp.getparent().remove(sp)

            # Add image as picture
            pic = slide_shapes.add_picture(str(image_path), left, top, width=width, height=height)

            # Copy name
            pic.name = shape_name

            self.logger.debug(f"Inserted image {image_path} into {shape_name}")

        except Exception as e:
            self.logger.error(f"Failed to insert image: {e}", exc_info=True)

    def _get_image_path(self, context: RenderContext) -> str:
        """Get image file path from context.

        Args:
            context: Rendering context.

        Returns:
            Path to image file.
        """
        parsed_name = context.parsed_name

        # Check for path option
        path = parsed_name.get_option("path")
        if path:
            return path

        # Check for ref option (reference to metadata)
        ref = parsed_name.get_option("ref")
        if ref and context.metadata:
            return context.metadata.get(ref, "")

        # Check metadata by renderer type
        if context.metadata:
            return context.metadata.get(parsed_name.renderer, "")

        return ""
