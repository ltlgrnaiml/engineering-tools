"""Comprehensive renderer validation test suite.

This test suite validates the complete data flow from CSV -> DataFrame -> Renderer -> Asset.
Tests cover:
1. Data normalization and column name handling
2. Filter logic for context parameters (side, imcol, imrow)
3. Metric extraction and case-insensitive matching
4. Contour plot data pivoting requirements
5. Box plot multi-metric handling
"""

import logging

import pandas as pd
import pytest

from apps.pptx_generator.backend.core.shape_name_parser import parse_shape_name
from apps.pptx_generator.backend.renderers.factory import RendererFactory
from apps.pptx_generator.backend.renderers.plot_renderer import PlotRenderer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def sample_data():
    """Create sample data matching test_data/population_all.csv structure."""
    data = {
        "image_file_name": [
            "DZ001_LC1_LC1",
            "DZ001_LC1_LC2",
            "DZ001_LC2_LC1",
            "DZ002_LC1_LC1",
            "DZ002_LC1_LC2",
            "DZ002_LC2_LC1",
        ],
        "side": ["Left", "Left", "Left", "Right", "Right", "Right"],
        "imagecolumn": [1, 1, 2, 1, 1, 2],
        "imagerow": [1, 2, 1, 1, 2, 1],
        "cd": [45.2, 45.5, 45.8, 46.1, 46.3, 46.5],
        "lwr": [2.6, 2.7, 2.8, 3.0, 3.1, 3.2],
        "lcdu": [1.1, 1.2, 1.3, 1.5, 1.6, 1.7],
        "wafer": ["W1", "W1", "W1", "W1", "W1", "W1"],
        "die": ["D1", "D1", "D2", "D1", "D1", "D2"],
        "quality": ["High", "High", "High", "High", "High", "Medium"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def normalized_data(sample_data):
    """Apply data processor normalization."""
    df = sample_data.copy()
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    df.columns = [
        col.replace("imagecolumn", "imcol").replace("imagerow", "imrow") for col in df.columns
    ]
    return df


class TestDataNormalization:
    """Test data normalization and column name handling."""

    def test_column_normalization(self, sample_data):
        """Test that column names are normalized correctly."""
        df = sample_data.copy()
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]
        df.columns = [
            col.replace("imagecolumn", "imcol").replace("imagerow", "imrow") for col in df.columns
        ]

        expected_cols = [
            "image_file_name",
            "side",
            "imcol",
            "imrow",
            "cd",
            "lwr",
            "lcdu",
            "wafer",
            "die",
            "quality",
        ]
        assert list(df.columns) == expected_cols
        logger.info(f"✓ Column normalization: {list(df.columns)}")

    def test_case_sensitivity(self, normalized_data):
        """Test that normalized data has lowercase columns."""
        assert "cd" in normalized_data.columns
        assert "CD" not in normalized_data.columns
        assert "imcol" in normalized_data.columns
        assert "imagecolumn" not in normalized_data.columns
        logger.info("✓ All columns are lowercase")


class TestShapeNameParsing:
    """Test shape name parsing for different renderer types."""

    def test_contour_plot_parsing(self):
        """Test parsing of contour plot shape name (v2 format)."""
        shape_name = "contour:CD,LWR,LCDU@left"
        parsed = parse_shape_name(shape_name)

        assert parsed.renderer == "contour"
        assert parsed.data == ["CD", "LWR", "LCDU"]
        assert parsed.filters == {"side": "left"}
        logger.info(f"✓ Contour plot parsed: {parsed}")

    def test_box_plot_parsing(self):
        """Test parsing of box plot shape name (v2 format)."""
        shape_name = "box:CD,LWR,LCDU@both"
        parsed = parse_shape_name(shape_name)

        assert parsed.renderer == "box"
        assert parsed.data == ["CD", "LWR", "LCDU"]
        assert parsed.filters == {"side": "both"}
        logger.info(f"✓ Box plot parsed: {parsed}")

    def test_table_parsing(self):
        """Test parsing of table shape name (v2 format)."""
        shape_name = "table:CD,LWR,LCDU@both|group=side"
        parsed = parse_shape_name(shape_name)

        assert parsed.renderer == "table"
        assert parsed.data == ["CD", "LWR", "LCDU"]
        assert parsed.filters == {"side": "both"}
        assert parsed.options == {"group": "side"}
        logger.info(f"✓ Table parsed: {parsed}")


class TestDataFiltering:
    """Test data filtering logic in base renderer."""

    def test_filter_by_side(self, normalized_data):
        """Test filtering data by side parameter (v2 format)."""
        renderer = PlotRenderer()
        shape_name = "contour:CD@left"
        parsed = parse_shape_name(shape_name)

        filtered = renderer.filter_data(normalized_data, parsed)

        assert len(filtered) == 3  # Only Left side rows
        assert all(filtered["side"].str.lower() == "left")
        logger.info(f"✓ Filtered by side=left: {len(filtered)} rows")

    def test_filter_by_side_both(self, normalized_data):
        """Test that side=both includes all rows (v2 format)."""
        renderer = PlotRenderer()
        shape_name = "box:CD@both"
        parsed = parse_shape_name(shape_name)

        filtered = renderer.filter_data(normalized_data, parsed)

        assert len(filtered) == 6  # All rows
        logger.info(f"✓ Filtered by side=both: {len(filtered)} rows (all)")

    def test_filter_by_multiple_params(self, normalized_data):
        """Test filtering by multiple parameters (v2 format)."""
        renderer = PlotRenderer()
        # Test with explicit key=value filter
        shape_name = "contour:CD@side=left"
        parsed = parse_shape_name(shape_name)

        filtered = renderer.filter_data(normalized_data, parsed)

        assert len(filtered) == 3  # Left side
        assert all(filtered["side"].str.lower() == "left")
        logger.info(f"✓ Filtered by side=left: {len(filtered)} rows")


class TestMetricExtraction:
    """Test metric extraction with case-insensitive matching."""

    def test_metrics_case_mismatch(self, normalized_data):
        """Test that uppercase metrics (CD) match lowercase columns (cd)."""
        renderer = PlotRenderer()
        shape_name = "contour:CD,LWR,LCDU@left"
        parsed = parse_shape_name(shape_name)

        # This is the CRITICAL test - metrics are uppercase in shape name
        # but columns are lowercase in data
        metrics = renderer._get_metrics(parsed, normalized_data)

        logger.info(f"Metrics from shape: {parsed.data}")
        logger.info(f"Available columns: {list(normalized_data.columns)}")
        logger.info(f"Extracted metrics: {metrics}")

        assert len(metrics) > 0, "No metrics extracted!"
        assert any(m.lower() in ["cd", "lwr", "lcdu"] for m in metrics)

    def test_metrics_normalization_needed(self, normalized_data):
        """Demonstrate that metric names need case-insensitive matching."""
        shape_metrics = ["CD", "LWR", "LCDU"]
        data_columns = list(normalized_data.columns)

        # Case-sensitive check (current code) - WILL FAIL
        matches_sensitive = [m for m in shape_metrics if m in data_columns]
        logger.error(f"Case-sensitive matches: {matches_sensitive} (should be empty)")

        # Case-insensitive check (needed fix)
        matches_insensitive = [m for m in shape_metrics if m.lower() in data_columns]
        logger.info(f"Case-insensitive matches: {matches_insensitive} (should be all 3)")

        assert len(matches_sensitive) == 0, "Case-sensitive should fail"
        assert len(matches_insensitive) == 3, "Case-insensitive should succeed"


class TestContourPlotRequirements:
    """Test contour plot specific requirements."""

    def test_contour_requires_imcol_imrow(self, normalized_data):
        """Test that contour plot has required spatial columns."""
        assert "imcol" in normalized_data.columns
        assert "imrow" in normalized_data.columns
        logger.info("✓ Contour plot spatial columns present")

    def test_contour_pivot_structure(self, normalized_data):
        """Test that data can be pivoted for contour plot."""
        # Filter to one side
        left_data = normalized_data[normalized_data["side"].str.lower() == "left"]

        # Attempt pivot
        try:
            pivot = left_data.pivot_table(
                values="cd", index="imrow", columns="imcol", aggfunc="mean"
            )
            logger.info(f"✓ Pivot successful: shape {pivot.shape}")
            logger.info(f"Pivot:\n{pivot}")
            assert pivot.shape[0] > 0
            assert pivot.shape[1] > 0
        except Exception as e:
            pytest.fail(f"Pivot failed: {e}")

    def test_contour_with_case_sensitive_metric(self, normalized_data):
        """Test contour pivot with uppercase metric name (will fail)."""
        left_data = normalized_data[normalized_data["side"].str.lower() == "left"]

        # Try to pivot with uppercase 'CD' (not in columns)
        with pytest.raises(KeyError):
            left_data.pivot_table(values="CD", index="imrow", columns="imcol", aggfunc="mean")
        logger.error("✓ EXPECTED FAILURE: Uppercase metric 'CD' not found")


class TestBoxPlotMultiMetric:
    """Test box plot with multiple metrics."""

    def test_box_plot_multiple_metrics(self, normalized_data):
        """Test box plot with multiple metrics."""
        renderer = PlotRenderer()
        shape_name = "box:CD,LWR,LCDU@both"
        parsed = parse_shape_name(shape_name)

        metrics = renderer._get_metrics(parsed, normalized_data)
        assert len(metrics) == 3
        logger.info(f"✓ Box plot metrics: {metrics}")


class TestRendererIntegration:
    """Test renderer factory and integration."""

    def test_plot_renderer_can_render(self):
        """Test that PlotRenderer can render contour plots."""
        renderer = PlotRenderer()
        parsed = parse_shape_name("contour:CD@left")

        assert renderer.can_render(parsed)
        logger.info("✓ PlotRenderer can render contour")

    def test_renderer_factory(self):
        """Test renderer factory selection."""
        factory = RendererFactory()
        factory.register_renderer(PlotRenderer())

        parsed = parse_shape_name("box:CD@both")
        renderer = factory.get_renderer(parsed)

        assert renderer is not None
        assert isinstance(renderer, PlotRenderer)
        logger.info("✓ RendererFactory selected PlotRenderer")
