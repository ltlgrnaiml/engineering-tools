"""PPTX (PowerPoint Generator) contracts.

This package contains Pydantic models for PPTX-specific data structures:
- Template contracts for slide deck templates and configuration
- Shape contracts for shape discovery and placeholder mapping
- Renderer contracts for the rendering pipeline

All contracts are domain-agnostic; user-specific knowledge (template paths,
placeholder names, data bindings) is injected via configs.
"""

from shared.contracts.pptx.template import (
    PPTXTemplate,
    PPTXTemplateRef,
    SlideTemplate,
    SlideLayout,
    TemplateValidationResult,
    RenderConfig,
    RenderRequest,
    RenderResult,
)
from shared.contracts.pptx.shape import (
    ShapeType,
    ShapeDiscoveryResult,
    ShapePlaceholder,
    ShapeBinding,
    DataBindingType,
    ChartConfig,
    TableConfig,
    TextConfig,
    ImageConfig,
)

__all__ = [
    # Template contracts
    "PPTXTemplate",
    "PPTXTemplateRef",
    "SlideTemplate",
    "SlideLayout",
    "TemplateValidationResult",
    "RenderConfig",
    "RenderRequest",
    "RenderResult",
    # Shape contracts
    "ShapeType",
    "ShapeDiscoveryResult",
    "ShapePlaceholder",
    "ShapeBinding",
    "DataBindingType",
    "ChartConfig",
    "TableConfig",
    "TextConfig",
    "ImageConfig",
]
