"""Shape discovery tests per ADR-0019.

Tests for the shape naming convention and discovery logic.
"""

import pytest

from apps.pptx_generator.backend.core.shape_discovery import (
    VALID_CATEGORIES,
    InvalidCategoryError,
    InvalidIdentifierError,
    ParsedShapeName,
    is_default_shape_name,
    is_valid_shape_name,
    parse_shape_name_adr0018,
)


class TestParseShapeNameAdr0018:
    """Tests for parse_shape_name_adr0018 function."""

    def test_valid_shape_name_basic(self):
        """Test parsing basic valid shape name."""
        result = parse_shape_name_adr0018("chart_revenue")
        assert result.category == "chart"
        assert result.identifier == "revenue"
        assert result.variant is None
        assert result.raw_name == "chart_revenue"

    def test_valid_shape_name_with_variant(self):
        """Test parsing shape name with variant."""
        result = parse_shape_name_adr0018("text_title_main")
        assert result.category == "text"
        assert result.identifier == "title"
        assert result.variant == "main"

    def test_valid_all_categories(self):
        """Test all valid categories per ADR-0019."""
        for category in VALID_CATEGORIES:
            result = parse_shape_name_adr0018(f"{category}_test")
            assert result.category == category
            assert result.identifier == "test"

    def test_case_insensitive(self):
        """Test case-insensitive matching per ADR-0019."""
        result1 = parse_shape_name_adr0018("CHART_REVENUE")
        assert result1.category == "chart"
        assert result1.identifier == "revenue"

        result2 = parse_shape_name_adr0018("Chart_Revenue")
        assert result2.category == "chart"
        assert result2.identifier == "revenue"

    def test_invalid_category_raises_error(self):
        """Test invalid category raises InvalidCategoryError with suggestions."""
        with pytest.raises(InvalidCategoryError) as exc_info:
            parse_shape_name_adr0018("unknown_field")
        assert "unknown" in str(exc_info.value)
        assert "Must be one of:" in str(exc_info.value)

    def test_missing_identifier_raises_error(self):
        """Test missing identifier raises InvalidIdentifierError."""
        with pytest.raises(InvalidIdentifierError):
            parse_shape_name_adr0018("chart_")

    def test_empty_name_raises_error(self):
        """Test empty name raises InvalidIdentifierError."""
        with pytest.raises(InvalidIdentifierError):
            parse_shape_name_adr0018("")

    def test_no_underscore_raises_error(self):
        """Test name without underscore raises InvalidIdentifierError."""
        with pytest.raises(InvalidIdentifierError) as exc_info:
            parse_shape_name_adr0018("chartrevenue")
        assert "underscore separator" in str(exc_info.value)

    def test_special_characters_raise_error(self):
        """Test special characters in name raise error."""
        with pytest.raises(InvalidIdentifierError):
            parse_shape_name_adr0018("chart_revenue-2024")

    def test_canonical_name_property(self):
        """Test canonical_name property."""
        result = parse_shape_name_adr0018("Chart_Revenue_Q1")
        assert result.canonical_name == "chart_revenue_q1"


class TestIsValidShapeName:
    """Tests for is_valid_shape_name function."""

    def test_valid_names(self):
        """Test valid shape names return True."""
        assert is_valid_shape_name("chart_revenue")
        assert is_valid_shape_name("table_summary")
        assert is_valid_shape_name("text_title_main")
        assert is_valid_shape_name("image_logo")
        assert is_valid_shape_name("metric_cd")
        assert is_valid_shape_name("dimension_wafer")

    def test_invalid_names(self):
        """Test invalid shape names return False."""
        assert not is_valid_shape_name("")
        assert not is_valid_shape_name("Rectangle 1")
        assert not is_valid_shape_name("unknown_field")
        assert not is_valid_shape_name("chartrevenue")

    def test_default_names_return_false(self):
        """Test default PowerPoint names return False."""
        assert not is_valid_shape_name("TextBox 1")
        assert not is_valid_shape_name("Rectangle 5")
        assert not is_valid_shape_name("Title")


class TestIsDefaultShapeName:
    """Tests for is_default_shape_name function."""

    def test_default_names(self):
        """Test common default PowerPoint names are detected."""
        assert is_default_shape_name("Rectangle 1")
        assert is_default_shape_name("TextBox 5")
        assert is_default_shape_name("Oval 2")
        assert is_default_shape_name("Line 1")
        assert is_default_shape_name("Title")
        assert is_default_shape_name("Subtitle")
        assert is_default_shape_name("Picture 3")
        assert is_default_shape_name("Chart 1")
        assert is_default_shape_name("Table 2")

    def test_custom_names_not_default(self):
        """Test custom names are not detected as defaults."""
        assert not is_default_shape_name("chart_revenue")
        assert not is_default_shape_name("table_summary")
        assert not is_default_shape_name("my_custom_shape")


class TestParsedShapeName:
    """Tests for ParsedShapeName dataclass."""

    def test_dataclass_fields(self):
        """Test dataclass field access."""
        parsed = ParsedShapeName(
            category="chart",
            identifier="revenue",
            variant="q1",
            raw_name="Chart_Revenue_Q1",
        )
        assert parsed.category == "chart"
        assert parsed.identifier == "revenue"
        assert parsed.variant == "q1"
        assert parsed.raw_name == "Chart_Revenue_Q1"

    def test_canonical_name_with_variant(self):
        """Test canonical_name with variant."""
        parsed = ParsedShapeName(
            category="text",
            identifier="title",
            variant="main",
            raw_name="text_title_main",
        )
        assert parsed.canonical_name == "text_title_main"

    def test_canonical_name_without_variant(self):
        """Test canonical_name without variant."""
        parsed = ParsedShapeName(
            category="chart",
            identifier="revenue",
            variant=None,
            raw_name="chart_revenue",
        )
        assert parsed.canonical_name == "chart_revenue"


class TestAdr0018Compliance:
    """Integration tests for full ADR-0019 compliance."""

    def test_all_valid_categories_accepted(self):
        """ADR-0019: Valid categories are text, chart, table, image, metric, dimension."""
        expected = {"text", "chart", "table", "image", "metric", "dimension"}
        assert expected == VALID_CATEGORIES

    def test_identifier_alphanumeric_only(self):
        """ADR-0019: Identifier must be alphanumeric."""
        # Valid
        assert is_valid_shape_name("chart_abc123")
        assert is_valid_shape_name("table_test1")
        # Invalid (special chars)
        assert not is_valid_shape_name("chart_abc-123")
        assert not is_valid_shape_name("chart_abc.123")
        assert not is_valid_shape_name("chart_abc 123")

    def test_case_insensitive_matching(self):
        """ADR-0019: Shape names are case-insensitive."""
        result_lower = parse_shape_name_adr0018("chart_revenue")
        result_upper = parse_shape_name_adr0018("CHART_REVENUE")
        result_mixed = parse_shape_name_adr0018("Chart_Revenue")

        assert result_lower.category == result_upper.category == result_mixed.category
        assert result_lower.identifier == result_upper.identifier == result_mixed.identifier

    def test_reserved_names_ignored(self):
        """ADR-0019: Reserved PowerPoint default names are automatically ignored."""
        reserved = [
            "Rectangle 1",
            "TextBox 5",
            "Oval 2",
            "Line 1",
            "Arrow 1",
            "Freeform 1",
            "Picture 3",
            "Chart 1",
            "Table 2",
            "Group 1",
            "Content Placeholder 1",
            "Title",
            "Subtitle",
            "Footer",
            "Slide Number",
            "Date Placeholder",
        ]
        for name in reserved:
            assert is_default_shape_name(name), f"{name} should be recognized as default"
            assert not is_valid_shape_name(name), f"{name} should not be valid shape name"
