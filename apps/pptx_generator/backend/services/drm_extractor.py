"""DRM Extractor Service.

Extracts Derived Requirements Manifest (DRM) from parsed template shapes.
Analyzes shape names to determine required contexts, metrics, data levels, and renderers.
"""

import logging

from apps.pptx_generator.backend.core.renderer_registry import (
    RENDERER_ALIASES,
    get_renderer_config,
)
from apps.pptx_generator.backend.core.shape_name_parser import (
    ParsedShapeNameV2,
    ValidationError,
    parse_shape_name,
)
from apps.pptx_generator.backend.models.drm import (
    AggregationType,
    DataLevelCardinality,
    DerivedRequirementsManifest,
    RequiredContext,
    RequiredDataLevel,
    RequiredMetric,
    RequiredRenderer,
)
from apps.pptx_generator.backend.models.template import ShapeMap

logger = logging.getLogger(__name__)


class DRMExtractorService:
    """Service for extracting DRM from template shapes."""

    # Standard context parameters that appear in shape names
    STANDARD_CONTEXT_PARAMS = {
        "side",
        "wafer",
        "imcol",
        "imrow",
        "die",
        "run_key",
        "quality",
    }

    # Mapping of data levels to cardinality
    DATA_LEVEL_MAP = {
        "many_rows": DataLevelCardinality.MANY_ROWS,
        "one_row": DataLevelCardinality.ONE_ROW,
        "single_value": DataLevelCardinality.ONE_ROW,
        "aggregated": DataLevelCardinality.AGGREGATED,
        "aggregated_or_raw": DataLevelCardinality.AGGREGATED_OR_RAW,
        "file_reference": DataLevelCardinality.ONE_ROW,
        "none": DataLevelCardinality.ONE_ROW,
    }

    def extract_drm(self, shape_map: ShapeMap) -> DerivedRequirementsManifest:
        """Extract DRM from shape map.

        Args:
            shape_map: Parsed template shape map.

        Returns:
            DerivedRequirementsManifest with all four required lists.
        """
        logger.info(f"Extracting DRM from template {shape_map.template_id}")

        # Parse all shape names
        parsed_shapes: list[ParsedShapeNameV2] = []
        for shape in shape_map.shapes:
            try:
                parsed = parse_shape_name(shape.name)
                parsed_shapes.append(parsed)
            except ValidationError as e:
                logger.warning(
                    f"Skipping invalid shape '{shape.name}' on slide {shape.slide_index}: {e}"
                )
                continue

        # Extract each of the four lists
        required_contexts = self._extract_contexts(parsed_shapes)
        required_metrics = self._extract_metrics(parsed_shapes)
        required_data_levels = self._extract_data_levels(parsed_shapes)
        required_renderers = self._extract_renderers(parsed_shapes)

        # Create and return DRM
        drm = DerivedRequirementsManifest(
            template_id=shape_map.template_id,
            required_contexts=required_contexts,
            required_metrics=required_metrics,
            required_data_levels=required_data_levels,
            required_renderers=required_renderers,
        )

        logger.info(
            f"DRM extracted: {len(required_contexts)} contexts, "
            f"{len(required_metrics)} metrics, {len(required_data_levels)} data levels, "
            f"{len(required_renderers)} renderers"
        )

        return drm

    def _extract_contexts(self, parsed_shapes: list[ParsedShapeNameV2]) -> list[RequiredContext]:
        """Extract unique required contexts from shapes.

        Args:
            parsed_shapes: List of parsed shape names (v2 format).

        Returns:
            List of unique required contexts.
        """
        context_names: set[str] = set()

        for shape in parsed_shapes:
            # Check standard context parameters in filters
            for param in self.STANDARD_CONTEXT_PARAMS:
                if shape.has_filter(param):
                    context_names.add(param)

        # Convert to RequiredContext objects
        required_contexts = [
            RequiredContext(
                name=name,
                description=f"Context dimension: {name}",
            )
            for name in sorted(context_names)
        ]

        return required_contexts

    # Renderer types that contain metrics in their data
    METRIC_RENDERER_TYPES = {
        "contour",
        "box",
        "scatter",
        "line",
        "bar",
        "hist",
        "heatmap",
        "stacked",
        "table",
        "kpi",
        "sparkline",
    }

    def _extract_metrics(self, parsed_shapes: list[ParsedShapeNameV2]) -> list[RequiredMetric]:
        """Extract unique required metrics from shapes.

        Args:
            parsed_shapes: List of parsed shape names (v2 format).

        Returns:
            List of unique required metrics.
        """
        metrics_dict: dict[str, RequiredMetric] = {}

        for shape in parsed_shapes:
            # Only extract metrics from renderer types that actually have metrics
            # Skip text, inert (#), link (link>), and other non-metric shapes
            if shape.renderer not in self.METRIC_RENDERER_TYPES:
                continue

            # Get metrics from shape data (v2 format)
            metrics_list = shape.get_metrics()
            for metric_name in metrics_list:
                if metric_name not in metrics_dict:
                    # Infer aggregation type from options
                    agg_option = shape.get_option("agg")
                    if agg_option:
                        try:
                            agg_type = AggregationType(agg_option)
                        except ValueError:
                            agg_type = AggregationType.MEAN
                    else:
                        agg_type = self._infer_aggregation(metric_name, shape)

                    metrics_dict[metric_name] = RequiredMetric(
                        name=metric_name,
                        aggregation_type=agg_type,
                        description=f"Metric: {metric_name}",
                    )

        return list(metrics_dict.values())

    def _infer_aggregation(self, metric_name: str, _shape: ParsedShapeNameV2) -> AggregationType:
        """Infer aggregation type for a metric.

        Args:
            metric_name: Name of the metric.
            _shape: Parsed shape containing the metric.

        Returns:
            Inferred aggregation type.
        """
        # Infer from metric name patterns
        metric_lower = metric_name.lower()
        if "3s" in metric_lower or "3sigma" in metric_lower:
            return AggregationType.SIGMA_3
        elif "std" in metric_lower or "sigma" in metric_lower:
            return AggregationType.STD
        elif "min" in metric_lower:
            return AggregationType.MIN
        elif "max" in metric_lower:
            return AggregationType.MAX
        elif "median" in metric_lower:
            return AggregationType.MEDIAN

        # Default to mean
        return AggregationType.MEAN

    def _extract_data_levels(
        self, parsed_shapes: list[ParsedShapeNameV2]
    ) -> list[RequiredDataLevel]:
        """Extract data level requirements from shapes.

        Args:
            parsed_shapes: List of parsed shape names (v2 format).

        Returns:
            List of unique data level requirements.
        """
        data_levels_dict: dict[str, RequiredDataLevel] = {}

        for shape in parsed_shapes:
            v2_renderer = shape.renderer

            # Skip if already processed
            if v2_renderer in data_levels_dict:
                continue

            # Resolve renderer to base type for registry lookup
            if v2_renderer in RENDERER_ALIASES:
                base_renderer_type, _ = RENDERER_ALIASES[v2_renderer]
            else:
                base_renderer_type = v2_renderer

            # Get data level from renderer registry
            config = get_renderer_config(base_renderer_type)
            if config:
                data_level_str = config.get("data_level", "many_rows")
                cardinality = self.DATA_LEVEL_MAP.get(
                    data_level_str, DataLevelCardinality.MANY_ROWS
                )

                data_levels_dict[v2_renderer] = RequiredDataLevel(
                    renderer_class=v2_renderer,
                    cardinality=cardinality,
                    description=f"Data level for {v2_renderer} renderers",
                )

        return list(data_levels_dict.values())

    def _extract_renderers(self, parsed_shapes: list[ParsedShapeNameV2]) -> list[RequiredRenderer]:
        """Extract required renderer types from shapes.

        Args:
            parsed_shapes: List of parsed shape names (v2 format).

        Returns:
            List of required renderers with shape references.
        """
        renderers_dict: dict[str, RequiredRenderer] = {}

        for shape in parsed_shapes:
            renderer_type = shape.renderer

            if renderer_type not in renderers_dict:
                renderers_dict[renderer_type] = RequiredRenderer(
                    renderer_type=renderer_type,
                    renderer_subtype=renderer_type,  # In v2, renderer is the type
                    shape_references=[],
                    count=0,
                )

            # Add shape reference and increment count
            renderers_dict[renderer_type].shape_references.append(shape.raw_name)
            renderers_dict[renderer_type].count += 1

        return list(renderers_dict.values())


# Validation test (remove after testing)
if __name__ == "__main__":
    from uuid import uuid4

    from apps.pptx_generator.backend.models.template import ShapeInfo, ShapeMap

    # Create test shape map
    shapes = [
        ShapeInfo(
            shape_id=1,
            name="plot__metrics__by_side__contour__side=left__metrics=CD,LWR,LCDU",
            shape_type="auto_shape",
            slide_index=0,
            position={"left": 0, "top": 0, "width": 100, "height": 100},
        ),
        ShapeInfo(
            shape_id=2,
            name="plot__metrics__by_side__box__side=both__metrics=CD,LWR",
            shape_type="auto_shape",
            slide_index=0,
            position={"left": 0, "top": 0, "width": 100, "height": 100},
        ),
        ShapeInfo(
            shape_id=3,
            name="table__metrics__contexts__summary__metrics=CD,LWR__contexts=by_side,by_imcol",
            shape_type="table",
            slide_index=0,
            position={"left": 0, "top": 0, "width": 100, "height": 100},
        ),
        ShapeInfo(
            shape_id=4,
            name="kpi__metrics__overall__single__metric=CD__aggregation=mean",
            shape_type="auto_shape",
            slide_index=1,
            position={"left": 0, "top": 0, "width": 100, "height": 100},
        ),
    ]

    template_id = uuid4()
    shape_map = ShapeMap(template_id=template_id, shapes=shapes, slide_count=2)

    # Extract DRM
    extractor = DRMExtractorService()
    drm = extractor.extract_drm(shape_map)

    # Validate results
    print("\nExtracted DRM:")
    print(f"  Contexts: {drm.get_all_contexts()}")
    print(f"  Metrics: {drm.get_all_metrics()}")
    print(f"  Data Levels: {len(drm.required_data_levels)}")
    print(f"  Renderers: {len(drm.required_renderers)}")

    # Assertions
    assert "side" in drm.get_all_contexts()
    assert "imcol" in drm.get_all_contexts()
    assert "CD" in drm.get_all_metrics()
    assert "LWR" in drm.get_all_metrics()
    assert "LCDU" in drm.get_all_metrics()
    assert len(drm.required_renderers) == 4  # contour, box, table, kpi

    # Print JSON
    print("\nDRM JSON:")
    print(drm.model_dump_json(indent=2))

    print("\nAll DRM extraction tests passed!")
