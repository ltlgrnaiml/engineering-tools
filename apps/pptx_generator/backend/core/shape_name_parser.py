"""Shape name parser for extracting structured information from shape names (v2 format)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Module-level parser instance for caching
_default_parser: ShapeNameParserV2 | None = None


class ShapeNameError(Exception):
    """Base exception for shape name parsing errors."""

    pass


class ValidationError(ShapeNameError):
    """Raised when shape name validation fails."""

    pass


@dataclass
class ParsedShapeNameV2:
    """
    Structured representation of a parsed v2 shape name.

    Attributes:
        renderer: Renderer type (e.g., 'contour', 'box', 'table', 'text', 'kpi').
        data: List of metrics or text content.
        filters: Dictionary of filter conditions (e.g., {'side': 'left', 'wafer': 'W1'}).
        options: Dictionary of rendering options (e.g., {'layout': '3x1', 'agg': 'mean'}).
        raw_name: Original shape name string.
    """

    renderer: str
    data: list[str]
    filters: dict[str, str]
    options: dict[str, str]
    raw_name: str

    def get_metrics(self) -> list[str]:
        """
        Get list of metrics from data.

        Returns:
            List of metric names.
        """
        return self.data

    def get_filter(self, key: str, default: str | None = None) -> str | None:
        """
        Get a filter value with optional default.

        Args:
            key: Filter key.
            default: Default value if key not found.

        Returns:
            Filter value or default.
        """
        return self.filters.get(key, default)

    def get_option(self, key: str, default: str | None = None) -> str | None:
        """
        Get an option value with optional default.

        Args:
            key: Option key.
            default: Default value if key not found.

        Returns:
            Option value or default.
        """
        return self.options.get(key, default)

    def has_filter(self, key: str) -> bool:
        """
        Check if a filter exists.

        Args:
            key: Filter key.

        Returns:
            True if filter exists.
        """
        return key in self.filters

    def has_option(self, key: str) -> bool:
        """
        Check if an option exists.

        Args:
            key: Option key.

        Returns:
            True if option exists.
        """
        return key in self.options


class ShapeNameParserV2:
    """Parser for v2 Asset Request Language shape naming convention."""

    def __init__(self):
        """Initialize the parser with cached filter shorthands."""
        self._filter_shorthands: dict[str, dict[str, str]] | None = None

    @property
    def FILTER_SHORTHANDS(self) -> dict[str, dict[str, str]]:
        """Get filter shorthands, loading from config if needed.

        Returns:
            Dict mapping shorthand to filter dict.
        """
        if self._filter_shorthands is None:
            self._filter_shorthands = self._load_filter_shorthands()
        return self._filter_shorthands

    def _load_filter_shorthands(self) -> dict[str, dict[str, str]]:
        """Load filter shorthands from domain config.

        Returns:
            Filter shorthands dict, or default fallback if config unavailable.
        """
        try:
            from apps.pptx_generator.backend.core.domain_config_service import get_domain_config
            config = get_domain_config()
            return config.get_filter_shorthands()
        except Exception:
            # Fallback to defaults if config not available
            return {
                "left": {"side": "left"},
                "right": {"side": "right"},
                "both": {"side": "both"},
                "all": {"side": "all"},
            }

    def parse(self, shape_name: str) -> ParsedShapeNameV2:
        """
        Parse a v2 format shape name into structured components.

        Format: <renderer>:<data>[@<filter>][|<options>]
        Examples:
            contour:CD
            contour:CD@left
            contour:CD,LWR,LCDU@left|layout=3x1
            box:CD,LWR,LCDU@both|agg=mean
            link>contour:CD@left:Open
            #divider

        Args:
            shape_name: The shape name to parse.

        Returns:
            ParsedShapeNameV2 object with extracted information.

        Raises:
            ValidationError: If shape name is invalid.
        """
        if not shape_name or not isinstance(shape_name, str):
            raise ValidationError("Shape name must be a non-empty string")

        raw_name = shape_name

        # Handle special prefixes
        if shape_name.startswith("link>"):
            return self._parse_link(shape_name, raw_name)
        elif shape_name.startswith("#"):
            return self._parse_inert(shape_name, raw_name)

        # Standard format: renderer:data[@filter][|options]
        if ":" not in shape_name:
            raise ValidationError(
                f"Invalid shape name format: '{raw_name}'. "
                "Expected: renderer:data[@filter][|options]"
            )

        # Split on : to get renderer and remainder
        renderer, remainder = shape_name.split(":", 1)

        if not renderer or not remainder:
            raise ValidationError(
                f"Invalid shape name format: '{raw_name}'. Renderer and data cannot be empty."
            )

        # Split remainder on @ to separate data from filter
        if "@" in remainder:
            data_part, filter_and_options = remainder.split("@", 1)
        else:
            data_part = remainder
            filter_and_options = ""

        # Split filter_and_options on | to separate filter from options
        if "|" in filter_and_options:
            filter_part, options_part = filter_and_options.split("|", 1)
        else:
            filter_part = filter_and_options
            options_part = ""

        # Parse data as comma-separated list
        data = [d.strip() for d in data_part.split(",") if d.strip()]

        if not data:
            raise ValidationError(f"Invalid shape name format: '{raw_name}'. Data cannot be empty.")

        # Parse filters
        filters = self._parse_filters(filter_part) if filter_part else {}

        # Parse options
        options = self._parse_options(options_part) if options_part else {}

        return ParsedShapeNameV2(
            renderer=renderer,
            data=data,
            filters=filters,
            options=options,
            raw_name=raw_name,
        )

    def _parse_link(self, shape_name: str, raw_name: str) -> ParsedShapeNameV2:
        """
        Parse link syntax: link>renderer:data[@filter]:label

        Args:
            shape_name: The shape name starting with 'link>'
            raw_name: Original shape name for error messages

        Returns:
            ParsedShapeNameV2 with link information
        """
        # Remove 'link>' prefix
        remainder = shape_name[5:]

        # Split on last : to get label
        if ":" not in remainder:
            raise ValidationError(
                f"Invalid link format: '{raw_name}'. Expected: link>renderer:data[@filter]:label"
            )

        # Find the last colon (label separator)
        parts = remainder.rsplit(":", 1)
        if len(parts) != 2:
            raise ValidationError(
                f"Invalid link format: '{raw_name}'. Expected: link>renderer:data[@filter]:label"
            )

        target_part, label = parts

        # Parse the target part as a normal shape name
        target_parsed = self.parse(target_part)

        # Add label as an option
        target_parsed.options["label"] = label

        return target_parsed

    def _parse_inert(self, shape_name: str, raw_name: str) -> ParsedShapeNameV2:
        """
        Parse inert syntax: #identifier

        Args:
            shape_name: The shape name starting with '#'
            raw_name: Original shape name for error messages

        Returns:
            ParsedShapeNameV2 with inert renderer
        """
        identifier = shape_name[1:].strip()

        if not identifier:
            raise ValidationError(
                f"Invalid inert format: '{raw_name}'. "
                "Expected: #identifier (e.g., #divider, #title)"
            )

        return ParsedShapeNameV2(
            renderer="inert",
            data=[identifier],
            filters={},
            options={},
            raw_name=raw_name,
        )

    def _parse_filters(self, filter_str: str) -> dict[str, str]:
        """
        Parse filter string into dictionary.

        Supports:
        - Shorthands: @left, @right, @both, @W1, etc.
        - Explicit: @side=left, @wafer=W1
        - Multiple: @left,W1 or @side=left,wafer=W1

        Args:
            filter_str: Filter string (without @ prefix)

        Returns:
            Dictionary of filters
        """
        if not filter_str:
            return {}

        filters = {}

        # Check if it's a shorthand (single word, no =)
        if "=" not in filter_str and "," not in filter_str:
            # Single shorthand
            if filter_str in self.FILTER_SHORTHANDS:
                filters.update(self.FILTER_SHORTHANDS[filter_str])
            else:
                raise ValidationError(
                    f"Unknown filter shorthand: '{filter_str}'. "
                    f"Valid shorthands: {', '.join(self.FILTER_SHORTHANDS.keys())}"
                )
            return filters

        # Handle multiple filters separated by comma
        for part in filter_str.split(","):
            part = part.strip()

            if not part:
                continue

            # Check if it's a shorthand
            if "=" not in part:
                if part in self.FILTER_SHORTHANDS:
                    filters.update(self.FILTER_SHORTHANDS[part])
                else:
                    raise ValidationError(
                        f"Unknown filter shorthand: '{part}'. "
                        f"Valid shorthands: {', '.join(self.FILTER_SHORTHANDS.keys())}"
                    )
            else:
                # Explicit key=value
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                if not key or not value:
                    raise ValidationError(f"Invalid filter format: '{part}'")

                filters[key] = value

        return filters

    def _parse_options(self, options_str: str) -> dict[str, str]:
        """
        Parse options string into dictionary.

        Format: key=value|key=value|...

        Args:
            options_str: Options string (without leading |)

        Returns:
            Dictionary of options
        """
        if not options_str:
            return {}

        options = {}

        for part in options_str.split("|"):
            part = part.strip()

            if not part:
                continue

            if "=" not in part:
                raise ValidationError(f"Invalid option format: '{part}'. Expected: key=value")

            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key or not value:
                raise ValidationError(
                    f"Invalid option format: '{part}'. Key and value cannot be empty."
                )

            options[key] = value

        return options

    def validate(self, parsed: ParsedShapeNameV2) -> list[str]:
        """
        Validate a parsed shape name.

        Args:
            parsed: The parsed shape name to validate.

        Returns:
            List of validation warnings (empty if all valid).
        """
        warnings: list[str] = []

        # Check renderer is known
        valid_renderers = [
            "contour",
            "box",
            "scatter",
            "line",
            "bar",
            "hist",
            "heatmap",
            "stacked",
            "table",
            "text",
            "kpi",
            "sparkline",
            "image",
            "inert",
            "link",
        ]

        if parsed.renderer not in valid_renderers:
            warnings.append(
                f"Unknown renderer '{parsed.renderer}'. "
                f"Valid renderers: {', '.join(valid_renderers)}"
            )

        return warnings


def parse_shape_name(shape_name: str) -> ParsedShapeNameV2:
    """
    Convenience function to parse a v2 shape name using cached parser instance.

    Uses a cached parser instance for efficiency.

    Args:
        shape_name: The shape name to parse.

    Returns:
        ParsedShapeNameV2 object.

    Raises:
        ValidationError: If shape name is invalid.
    """
    global _default_parser
    if _default_parser is None:
        _default_parser = ShapeNameParserV2()
    return _default_parser.parse(shape_name)


def validate_shape_name(shape_name: str) -> tuple[ParsedShapeNameV2, list[str]]:
    """
    Parse and validate a v2 shape name.

    Args:
        shape_name: The shape name to validate.

    Returns:
        Tuple of (parsed shape name, list of warnings).

    Raises:
        ValidationError: If shape name has syntax errors.
    """
    parser = ShapeNameParserV2()
    parsed = parser.parse(shape_name)
    warnings = parser.validate(parsed)
    return parsed, warnings
