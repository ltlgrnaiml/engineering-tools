"""Renderer system for PowerPoint shape population.

This package provides a modular, extensible rendering system for populating
PowerPoint shapes with data based on shape naming conventions.
"""

from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext
from apps.pptx_generator.backend.renderers.factory import RendererFactory

__all__ = ["BaseRenderer", "RenderContext", "RendererFactory"]
