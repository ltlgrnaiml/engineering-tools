"""Renderer type registry and validation."""

from typing import Any

RENDERER_TYPES: dict[str, dict[str, Any]] = {
    "plot": {
        "subtypes": [
            "contour",
            "scatter",
            "line",
            "bar",
            "box",
            "hist",
            "heatmap",
            "stacked",
        ],
        "data_level": "many_rows",
        "required_params": ["metrics"],
        "optional_params": [
            "side",
            "wafer",
            "imcol",
            "imrow",
            "contexts",
            "filters",
            "colormap",
            "vmin",
            "vmax",
        ],
        "description": "Data visualization charts and plots",
    },
    "table": {
        "subtypes": ["summary", "detail", "pivot"],
        "data_level": "aggregated_or_raw",
        "required_params": ["metrics"],
        "optional_params": ["contexts", "side", "wafer", "filters", "sort_by"],
        "description": "Tabular data display",
    },
    "text": {
        "subtypes": ["subtitle", "label", "annotation", "link", "summary"],
        "data_level": "single_value",
        "required_params": [],
        "optional_params": ["text", "ref", "label", "side", "metrics"],
        "description": "Text content and labels",
    },
    "kpi": {
        "subtypes": ["single", "delta", "trend"],
        "data_level": "single_value",
        "required_params": ["metric", "aggregation"],
        "optional_params": ["side", "wafer", "comparison", "format"],
        "description": "Key performance indicators",
    },
    "sparkline": {
        "subtypes": ["line", "bar", "area"],
        "data_level": "many_rows",
        "required_params": ["metric"],
        "optional_params": ["window", "side", "wafer", "color"],
        "description": "Inline mini-charts",
    },
    "image": {
        "subtypes": ["logo", "diagram", "photo"],
        "data_level": "file_reference",
        "required_params": ["source"],
        "optional_params": ["alt_text", "scale"],
        "description": "Static images",
    },
    "inert": {
        "subtypes": ["shape", "divider", "background"],
        "data_level": "none",
        "required_params": [],
        "optional_params": [],
        "description": "Non-data decorative elements",
    },
}

_CUSTOM_RENDERERS: dict[str, dict[str, Any]] = {}

# V2 renderer aliases: maps v2 renderer name to (renderer_type, renderer_subtype)
RENDERER_ALIASES: dict[str, tuple[str, str]] = {
    "contour": ("plot", "contour"),
    "box": ("plot", "box"),
    "scatter": ("plot", "scatter"),
    "line": ("plot", "line"),
    "bar": ("plot", "bar"),
    "hist": ("plot", "hist"),
    "heatmap": ("plot", "heatmap"),
    "stacked": ("plot", "stacked"),
    "table": ("table", "summary"),
    "summary": ("table", "summary"),
    "detail": ("table", "detail"),
    "pivot": ("table", "pivot"),
    "text": ("text", "subtitle"),
    "kpi": ("kpi", "single"),
    "sparkline": ("sparkline", "line"),
    "image": ("image", "photo"),
    "link": ("text", "link"),
    "inert": ("inert", "shape"),
}


def resolve_renderer_type(renderer: str) -> tuple[str, str]:
    """
    Resolve a v2 renderer name to (renderer_type, renderer_subtype).

    Args:
        renderer: V2 renderer name (e.g., 'contour', 'box', 'table').

    Returns:
        Tuple of (renderer_type, renderer_subtype).

    Raises:
        ValueError: If renderer is unknown.
    """
    if renderer in RENDERER_ALIASES:
        return RENDERER_ALIASES[renderer]
    raise ValueError(
        f"Unknown renderer: {renderer}. "
        f"Valid renderers: {', '.join(sorted(RENDERER_ALIASES.keys()))}"
    )


def get_default_options(renderer: str) -> dict[str, str]:
    """
    Get default options for a v2 renderer.

    Args:
        renderer: V2 renderer name.

    Returns:
        Dictionary of default options.
    """
    defaults = {
        "contour": {"layout": "stack"},
        "box": {"layout": "side-by-side"},
        "scatter": {"layout": "single"},
        "line": {"layout": "overlay"},
        "bar": {"layout": "side-by-side"},
        "hist": {"layout": "overlay"},
        "heatmap": {"layout": "stack"},
        "stacked": {"layout": "stack"},
        "table": {"sort": "asc"},
        "text": {},
        "kpi": {"agg": "mean"},
        "sparkline": {"layout": "inline"},
        "image": {},
        "link": {},
        "inert": {},
    }
    return defaults.get(renderer, {})


def register_custom_renderer(renderer_type: str, config: dict[str, Any]) -> None:
    """
    Register a custom renderer type at runtime.

    Args:
        renderer_type: Unique identifier for the renderer type.
        config: Configuration dictionary with keys:
            - subtypes: List of valid subtypes
            - data_level: Data requirement level
            - required_params: List of required parameter names
            - optional_params: List of optional parameter names
            - description: Human-readable description

    Example:
        register_custom_renderer("qqplot", {
            "subtypes": ["normal", "lognormal", "weibull"],
            "data_level": "many_rows",
            "required_params": ["metric", "distribution"],
            "optional_params": ["side", "confidence_level"],
            "description": "Quantile-quantile plots for distribution analysis"
        })
    """
    _CUSTOM_RENDERERS[renderer_type] = config


def get_renderer_config(renderer_type: str) -> dict[str, Any] | None:
    """
    Get configuration for a renderer type.

    Args:
        renderer_type: The renderer type to look up.

    Returns:
        Configuration dictionary or None if not found.
    """
    if renderer_type in RENDERER_TYPES:
        return RENDERER_TYPES[renderer_type]
    return _CUSTOM_RENDERERS.get(renderer_type)


def get_all_renderer_types() -> list[str]:
    """
    Get list of all registered renderer types.

    Returns:
        List of renderer type names.
    """
    return list(RENDERER_TYPES.keys()) + list(_CUSTOM_RENDERERS.keys())


def is_valid_renderer_type(renderer_type: str) -> bool:
    """
    Check if a renderer type is registered.

    Args:
        renderer_type: The renderer type to validate.

    Returns:
        True if valid, False otherwise.
    """
    return renderer_type in RENDERER_TYPES or renderer_type in _CUSTOM_RENDERERS


def is_valid_subtype(renderer_type: str, subtype: str) -> bool:
    """
    Check if a subtype is valid for a renderer type.

    Args:
        renderer_type: The renderer type.
        subtype: The subtype to validate.

    Returns:
        True if valid, False otherwise.
    """
    config = get_renderer_config(renderer_type)
    if not config:
        return False
    return subtype in config.get("subtypes", [])


def get_required_params(renderer_type: str) -> list[str]:
    """
    Get required parameters for a renderer type.

    Args:
        renderer_type: The renderer type.

    Returns:
        List of required parameter names.
    """
    config = get_renderer_config(renderer_type)
    if not config:
        return []
    return config.get("required_params", [])


def get_optional_params(renderer_type: str) -> list[str]:
    """
    Get optional parameters for a renderer type.

    Args:
        renderer_type: The renderer type.

    Returns:
        List of optional parameter names.
    """
    config = get_renderer_config(renderer_type)
    if not config:
        return []
    return config.get("optional_params", [])


def get_data_level(renderer_type: str) -> str | None:
    """
    Get data level requirement for a renderer type.

    Args:
        renderer_type: The renderer type.

    Returns:
        Data level string or None if not found.
    """
    config = get_renderer_config(renderer_type)
    if not config:
        return None
    return config.get("data_level")
