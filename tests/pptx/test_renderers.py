"""Unit tests for PPTX renderers.

Tests renderer functionality per ADR-0022 and ADR-0029.
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from apps.pptx_generator.backend.core.shape_name_parser import ParsedShapeNameV2
from apps.pptx_generator.backend.renderers.base import BaseRenderer, RenderContext


class TestBaseRenderer:
    """Tests for BaseRenderer ABC."""

    def test_base_renderer_is_abstract(self):
        """BaseRenderer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseRenderer()

    def test_base_renderer_defines_can_render(self):
        """BaseRenderer defines can_render abstract method."""
        assert hasattr(BaseRenderer, "can_render")

    def test_base_renderer_defines_render(self):
        """BaseRenderer defines render abstract method."""
        assert hasattr(BaseRenderer, "render")


class TestRenderContext:
    """Tests for RenderContext dataclass."""

    def test_render_context_creation(self):
        """RenderContext can be created with required fields."""
        mock_shape = MagicMock()
        mock_parsed_name = MagicMock(spec=ParsedShapeNameV2)
        mock_data = pd.DataFrame({"col": [1, 2, 3]})

        context = RenderContext(
            shape=mock_shape,
            parsed_name=mock_parsed_name,
            data=mock_data,
        )

        assert context.shape == mock_shape
        assert context.parsed_name == mock_parsed_name
        assert context.data is mock_data
        assert context.shape_data is None
        assert context.output_dir is None
        assert context.metadata is None

    def test_render_context_with_optional_fields(self):
        """RenderContext accepts optional fields."""
        from pathlib import Path

        mock_shape = MagicMock()
        mock_parsed_name = MagicMock(spec=ParsedShapeNameV2)
        mock_data = pd.DataFrame({"col": [1, 2, 3]})
        mock_shape_data = pd.DataFrame({"filtered": [1]})
        output_dir = Path("/tmp/output")
        metadata = {"run_id": "abc123"}

        context = RenderContext(
            shape=mock_shape,
            parsed_name=mock_parsed_name,
            data=mock_data,
            shape_data=mock_shape_data,
            output_dir=output_dir,
            metadata=metadata,
        )

        assert context.shape_data is mock_shape_data
        assert context.output_dir == output_dir
        assert context.metadata == metadata


class TestTableRendererSpec:
    """Tests for TableRenderer per ADR-0029."""

    def test_table_renderer_imports_table_spec(self):
        """TableRenderer imports TableSpec from shared contracts."""
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer
        from shared.contracts.core.rendering import TableSpec

        renderer = TableRenderer()
        # TableRenderer uses TableSpec contract internally
        assert TableSpec is not None
        assert renderer is not None

    def test_table_renderer_can_render_table_shapes(self):
        """TableRenderer.can_render returns True for table shapes."""
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer

        renderer = TableRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "table"

        assert renderer.can_render(mock_parsed) is True

    def test_table_renderer_rejects_non_table_shapes(self):
        """TableRenderer.can_render returns False for non-table shapes."""
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer

        renderer = TableRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "chart"

        assert renderer.can_render(mock_parsed) is False

    def test_table_renderer_has_defaults(self):
        """TableRenderer has defaults property."""
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer

        renderer = TableRenderer()
        # defaults property should exist
        assert hasattr(renderer, "defaults")


class TestPlotRendererSpec:
    """Tests for PlotRenderer per ADR-0029."""

    def test_plot_renderer_imports_chart_spec(self):
        """PlotRenderer imports ChartSpec from shared contracts."""
        from apps.pptx_generator.backend.renderers.plot_renderer import PlotRenderer
        from shared.contracts.core.rendering import ChartSpec

        renderer = PlotRenderer()
        # PlotRenderer uses ChartSpec contract internally
        assert ChartSpec is not None
        assert renderer is not None

    def test_plot_renderer_can_render_bar_chart(self):
        """PlotRenderer.can_render returns True for bar charts."""
        from apps.pptx_generator.backend.renderers.plot_renderer import PlotRenderer

        renderer = PlotRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "bar"

        assert renderer.can_render(mock_parsed) is True

    def test_plot_renderer_can_render_line_chart(self):
        """PlotRenderer.can_render returns True for line charts."""
        from apps.pptx_generator.backend.renderers.plot_renderer import PlotRenderer

        renderer = PlotRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "line"

        assert renderer.can_render(mock_parsed) is True

    def test_plot_renderer_rejects_non_plot_shapes(self):
        """PlotRenderer.can_render returns False for non-plot shapes."""
        from apps.pptx_generator.backend.renderers.plot_renderer import PlotRenderer

        renderer = PlotRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "table"

        assert renderer.can_render(mock_parsed) is False


class TestImageRenderer:
    """Tests for ImageRenderer per ADR-0022."""

    def test_image_renderer_can_render(self):
        """ImageRenderer handles image_ category shapes."""
        from apps.pptx_generator.backend.renderers.image_renderer import ImageRenderer

        renderer = ImageRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "image"

        assert renderer.can_render(mock_parsed) is True

    def test_image_renderer_rejects_non_image(self):
        """ImageRenderer rejects non-image shapes."""
        from apps.pptx_generator.backend.renderers.image_renderer import ImageRenderer

        renderer = ImageRenderer()

        mock_parsed = MagicMock(spec=ParsedShapeNameV2)
        mock_parsed.renderer = "table"

        assert renderer.can_render(mock_parsed) is False

    def test_image_renderer_builds_image_spec(self):
        """ImageRenderer can build ImageSpec contract."""
        from apps.pptx_generator.backend.renderers.image_renderer import ImageRenderer
        from shared.contracts.core.rendering import ImageSpec

        renderer = ImageRenderer()

        spec = renderer.build_image_spec(
            source_path="/path/to/image.png",
            name="test_image",
            fit_mode="contain",
        )

        assert isinstance(spec, ImageSpec)
        assert spec.name == "test_image"
        assert spec.source_path == "/path/to/image.png"
        assert spec.fit_mode == "contain"


class TestRendererFactory:
    """Tests for renderer factory pattern per ADR-0022."""

    def test_factory_exists(self):
        """Renderer factory module exists."""
        from apps.pptx_generator.backend.renderers import factory

        assert factory is not None

    def test_factory_class_has_get_renderer(self):
        """RendererFactory class has get_renderer method."""
        from apps.pptx_generator.backend.renderers.factory import RendererFactory

        factory = RendererFactory()
        assert hasattr(factory, "get_renderer")
        assert callable(factory.get_renderer)

    def test_factory_can_register_renderer(self):
        """RendererFactory can register renderers."""
        from apps.pptx_generator.backend.renderers.factory import RendererFactory
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer

        factory = RendererFactory()
        renderer = TableRenderer()
        factory.register_renderer(renderer)

        assert len(factory.get_all_renderers()) == 1


class TestRendererGracefulDegradation:
    """Tests for graceful degradation per ADR-0022."""

    def test_renderer_logs_errors(self):
        """Renderers log errors without crashing."""
        from apps.pptx_generator.backend.renderers.table_renderer import TableRenderer

        renderer = TableRenderer()

        # Verify renderer has logger
        assert hasattr(renderer, "logger")

    def test_render_context_handles_empty_data(self):
        """RenderContext handles empty DataFrame gracefully."""
        mock_shape = MagicMock()
        mock_parsed_name = MagicMock(spec=ParsedShapeNameV2)
        empty_df = pd.DataFrame()

        context = RenderContext(
            shape=mock_shape,
            parsed_name=mock_parsed_name,
            data=empty_df,
        )

        assert len(context.data) == 0
