"""Output Adapters for the Unified Rendering Engine.

Per ADR-0029: Output Target Adapters.

This package provides adapters for different output formats:
- PNG: Static image via matplotlib
- SVG: Vector graphics via matplotlib
- JSON: Chart data for frontend libraries
- PPTX: Native PowerPoint charts (via python-pptx)
"""

from shared.rendering.adapters.base import BaseOutputAdapter

__version__ = "0.1.0"

__all__ = [
    "BaseOutputAdapter",
]
