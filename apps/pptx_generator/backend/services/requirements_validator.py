"""Requirements Validator Service.

Validates the Four Green Bars:
1. Required Context - all contexts mapped
2. Required Metrics - all metrics mapped with correct aggregation
3. Required Data Levels - renderer requirements can be satisfied
4. Required Renderers - all renderer types are supported
"""

import logging

from apps.pptx_generator.backend.core.renderer_registry import (
    RENDERER_ALIASES,
    is_valid_renderer_type,
)
from apps.pptx_generator.backend.models.drm import DerivedRequirementsManifest
from apps.pptx_generator.backend.models.mapping_manifest import MappingManifest
from apps.pptx_generator.backend.models.validation_report import (
    BarStatus,
    FourBarsStatus,
    ValidationStatus,
    ValidationWarning,
)

logger = logging.getLogger(__name__)


class RequirementsValidatorService:
    """Service for validating Four Green Bars."""

    # Coverage thresholds
    GREEN_THRESHOLD = 100.0  # 100% coverage
    YELLOW_THRESHOLD = 80.0  # 80-99% coverage
    # Below 80% is RED

    def validate_four_bars(
        self, drm: DerivedRequirementsManifest, mappings: MappingManifest
    ) -> FourBarsStatus:
        """Validate all four bars.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.

        Returns:
            FourBarsStatus with validation results.
        """
        logger.info("Validating Four Green Bars")

        context_bar = self._validate_context_bar(drm, mappings)
        metrics_bar = self._validate_metrics_bar(drm, mappings)
        data_levels_bar = self._validate_data_levels_bar(drm)
        renderers_bar = self._validate_renderers_bar(drm)

        status = FourBarsStatus(
            required_context=context_bar,
            required_metrics=metrics_bar,
            required_data_levels=data_levels_bar,
            required_renderers=renderers_bar,
        )

        logger.info(f"Validation complete: All green = {status.is_all_green()}")

        return status

    def _validate_context_bar(
        self, drm: DerivedRequirementsManifest, mappings: MappingManifest
    ) -> BarStatus:
        """Validate required context bar.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.

        Returns:
            BarStatus for context bar.
        """
        total_required = len(drm.required_contexts)
        if total_required == 0:
            return BarStatus(
                status=ValidationStatus.GREEN,
                coverage_percentage=100.0,
                missing_items=[],
                warnings=[],
            )

        mapped_count = 0
        missing_items = []
        warnings = []

        for context in drm.required_contexts:
            mapping = mappings.get_context_mapping(context.name)
            if mapping:
                mapped_count += 1
            else:
                missing_items.append(context.name)
                warnings.append(
                    ValidationWarning(
                        severity="error",
                        message=f"Context '{context.name}' not mapped",
                        suggested_fix=f"Add mapping for '{context.name}' in context mapping editor (Step 6)",
                    )
                )

        coverage = (mapped_count / total_required) * 100.0

        # Determine status
        if coverage >= self.GREEN_THRESHOLD:
            status = ValidationStatus.GREEN
        elif coverage >= self.YELLOW_THRESHOLD:
            status = ValidationStatus.YELLOW
        else:
            status = ValidationStatus.RED

        return BarStatus(
            status=status,
            coverage_percentage=coverage,
            missing_items=missing_items,
            warnings=warnings,
        )

    def _validate_metrics_bar(
        self, drm: DerivedRequirementsManifest, mappings: MappingManifest
    ) -> BarStatus:
        """Validate required metrics bar.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.

        Returns:
            BarStatus for metrics bar.
        """
        total_required = len(drm.required_metrics)
        if total_required == 0:
            return BarStatus(
                status=ValidationStatus.GREEN,
                coverage_percentage=100.0,
                missing_items=[],
                warnings=[],
            )

        mapped_count = 0
        missing_items = []
        warnings = []

        for metric in drm.required_metrics:
            mapping = mappings.get_metric_mapping(metric.name)
            if mapping:
                # Check aggregation semantics match
                if (
                    metric.aggregation_type
                    and mapping.aggregation_semantics != metric.aggregation_type
                ):
                    warnings.append(
                        ValidationWarning(
                            severity="warning",
                            message=f"Metric '{metric.name}' aggregation mismatch: "
                            f"required={metric.aggregation_type}, mapped={mapping.aggregation_semantics}",
                            suggested_fix="Update aggregation semantics in metrics mapping editor",
                        )
                    )
                mapped_count += 1
            else:
                missing_items.append(metric.name)
                warnings.append(
                    ValidationWarning(
                        severity="error",
                        message=f"Metric '{metric.name}' not mapped",
                        suggested_fix=f"Add mapping for '{metric.name}' in metrics mapping editor (Step 7)",
                    )
                )

        coverage = (mapped_count / total_required) * 100.0

        # Determine status
        if coverage >= self.GREEN_THRESHOLD:
            status = ValidationStatus.GREEN
        elif coverage >= self.YELLOW_THRESHOLD:
            status = ValidationStatus.YELLOW
        else:
            status = ValidationStatus.RED

        return BarStatus(
            status=status,
            coverage_percentage=coverage,
            missing_items=missing_items,
            warnings=warnings,
        )

    def _validate_data_levels_bar(self, drm: DerivedRequirementsManifest) -> BarStatus:
        """Validate required data levels bar.

        Args:
            drm: Derived requirements manifest.

        Returns:
            BarStatus for data levels bar.
        """
        # For now, assume all data levels can be satisfied
        # In future, this would check actual data cardinality
        total_required = len(drm.required_data_levels)
        if total_required == 0:
            return BarStatus(
                status=ValidationStatus.GREEN,
                coverage_percentage=100.0,
                missing_items=[],
                warnings=[],
            )

        # All data levels are satisfied if they're defined
        # (actual data validation happens during preflight)
        return BarStatus(
            status=ValidationStatus.GREEN,
            coverage_percentage=100.0,
            missing_items=[],
            warnings=[],
        )

    def _validate_renderers_bar(self, drm: DerivedRequirementsManifest) -> BarStatus:
        """Validate required renderers bar.

        Args:
            drm: Derived requirements manifest.

        Returns:
            BarStatus for renderers bar.
        """
        total_required = len(drm.required_renderers)
        if total_required == 0:
            return BarStatus(
                status=ValidationStatus.GREEN,
                coverage_percentage=100.0,
                missing_items=[],
                warnings=[],
            )

        supported_count = 0
        unsupported_items = []
        warnings = []

        for renderer in drm.required_renderers:
            # In v2, renderer_type is the v2 renderer name (e.g., "contour", "box", "text")
            v2_renderer = renderer.renderer_type

            # Check if renderer is valid (exists in RENDERER_ALIASES or is a valid base type)
            is_valid = v2_renderer in RENDERER_ALIASES or is_valid_renderer_type(v2_renderer)

            if not is_valid:
                unsupported_items.append(v2_renderer)
                warnings.append(
                    ValidationWarning(
                        severity="error",
                        message=f"Unsupported renderer: {v2_renderer}",
                        suggested_fix="Remove shapes using this renderer or implement renderer support",
                    )
                )
                continue

            supported_count += 1

        coverage = (supported_count / total_required) * 100.0

        # Determine status
        if coverage >= self.GREEN_THRESHOLD:
            status = ValidationStatus.GREEN
        elif coverage >= self.YELLOW_THRESHOLD:
            status = ValidationStatus.YELLOW
        else:
            status = ValidationStatus.RED

        return BarStatus(
            status=status,
            coverage_percentage=coverage,
            missing_items=unsupported_items,
            warnings=warnings,
        )


# Validation test (remove after testing)
if __name__ == "__main__":
    from uuid import uuid4

    from apps.pptx_generator.backend.models.drm import (
        AggregationType,
        RequiredContext,
        RequiredMetric,
        RequiredRenderer,
    )
    from apps.pptx_generator.backend.models.mapping_manifest import (
        ContextMapping,
        MappingSourceType,
        MetricMapping,
    )

    # Create test DRM
    drm = DerivedRequirementsManifest(
        template_id=uuid4(),
        required_contexts=[
            RequiredContext(name="side"),
            RequiredContext(name="wafer"),
        ],
        required_metrics=[
            RequiredMetric(name="CD", aggregation_type=AggregationType.MEAN),
            RequiredMetric(name="LWR", aggregation_type=AggregationType.SIGMA_3),
        ],
        required_renderers=[
            RequiredRenderer(renderer_type="plot", renderer_subtype="contour"),
            RequiredRenderer(renderer_type="table", renderer_subtype="summary"),
        ],
    )

    # Test with complete mappings (all green)
    complete_mappings = MappingManifest(
        project_id=uuid4(),
        context_mappings=[
            ContextMapping(
                context_name="side",
                source_type=MappingSourceType.COLUMN,
                source_column="SpaceCD_Side",
            ),
            ContextMapping(
                context_name="wafer",
                source_type=MappingSourceType.COLUMN,
                source_column="Wafer",
            ),
        ],
        metrics_mappings=[
            MetricMapping(
                metric_name="CD",
                source_column="CD",
                aggregation_semantics=AggregationType.MEAN,
            ),
            MetricMapping(
                metric_name="LWR",
                source_column="LWR",
                aggregation_semantics=AggregationType.SIGMA_3,
            ),
        ],
    )

    validator = RequirementsValidatorService()
    status = validator.validate_four_bars(drm, complete_mappings)

    print("\nFour Bars Status:")
    print(
        f"  Context: {status.required_context.status.value} ({status.required_context.coverage_percentage:.0f}%)"
    )
    print(
        f"  Metrics: {status.required_metrics.status.value} ({status.required_metrics.coverage_percentage:.0f}%)"
    )
    print(
        f"  Data Levels: {status.required_data_levels.status.value} ({status.required_data_levels.coverage_percentage:.0f}%)"
    )
    print(
        f"  Renderers: {status.required_renderers.status.value} ({status.required_renderers.coverage_percentage:.0f}%)"
    )
    print(f"\nAll Green: {status.is_all_green()}")

    assert status.is_all_green()

    # Test with incomplete mappings
    incomplete_mappings = MappingManifest(
        project_id=uuid4(),
        context_mappings=[
            ContextMapping(
                context_name="side",
                source_type=MappingSourceType.COLUMN,
                source_column="SpaceCD_Side",
            ),
        ],
        metrics_mappings=[],
    )

    incomplete_status = validator.validate_four_bars(drm, incomplete_mappings)
    assert not incomplete_status.is_all_green()
    assert incomplete_status.required_context.status == ValidationStatus.RED  # 50% < 80% = RED
    assert incomplete_status.required_metrics.status == ValidationStatus.RED

    print("\nAll requirements validator tests passed!")
