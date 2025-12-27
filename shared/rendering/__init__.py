"""Unified Rendering Engine.

Per ADR-0028: Unified Rendering Engine for Cross-Tool Visualization.

This package provides a shared rendering system for all tools (DAT, SOV, PPTX).
It consumes RenderSpec contracts and produces outputs via target adapters.

Architecture:
    RenderSpec (contracts) → RenderEngine → OutputAdapter → Output (PNG, SVG, PPTX, etc.)

Usage:
    from shared.rendering import RenderEngine, get_adapter
    from shared.contracts.core.rendering import ChartSpec, OutputTarget

    engine = RenderEngine()
    spec = ChartSpec(...)
    result = await engine.render(spec, target=OutputTarget.PNG)
"""

from shared.rendering.engine import RenderEngine
from shared.rendering.registry import AdapterRegistry, get_adapter, register_adapter

__version__ = "0.1.0"

__all__ = [
    "RenderEngine",
    "AdapterRegistry",
    "get_adapter",
    "register_adapter",
]
