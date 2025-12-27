"""Core business logic and utilities."""

from apps.pptx_generator.backend.core.renderer_registry import (
    RENDERER_ALIASES,
    RENDERER_TYPES,
    get_default_options,
    get_renderer_config,
    is_valid_renderer_type,
    is_valid_subtype,
    register_custom_renderer,
    resolve_renderer_type,
)
from apps.pptx_generator.backend.core.shape_name_parser import (
    ParsedShapeNameV2,
    ShapeNameError,
    ValidationError,
    parse_shape_name,
    validate_shape_name,
)

__all__ = [
    "RENDERER_TYPES",
    "RENDERER_ALIASES",
    "get_renderer_config",
    "is_valid_renderer_type",
    "is_valid_subtype",
    "register_custom_renderer",
    "resolve_renderer_type",
    "get_default_options",
    "ParsedShapeNameV2",
    "parse_shape_name",
    "validate_shape_name",
    "ShapeNameError",
    "ValidationError",
]
