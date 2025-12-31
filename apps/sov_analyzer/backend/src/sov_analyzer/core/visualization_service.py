"""Visualization service for SOV tool.

Per ADR-0025: Generate visualization-ready Pydantic contracts from ANOVA results.
Per ADR-0029: Extend ChartSpec from shared rendering primitives.

This module generates typed visualization specifications that can be:
- Consumed directly by the frontend for rendering
- Included in DataSet manifests for downstream tools (PPTX)
- Serialized to JSON for API responses
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shared.contracts.core.rendering import AxisConfig
from shared.contracts.sov.visualization import (
    BoxPlotConfig,
    InteractionPlotConfig,
    MainEffectsPlotConfig,
    ResidualPlotConfig,
    VarianceBarConfig,
    VisualizationSpec,
    VisualizationType,
)

if TYPE_CHECKING:
    from ..analysis.anova import ANOVAResult

__version__ = "0.1.0"


class VisualizationService:
    """Generate visualization contracts from ANOVA results.
    
    Per ADR-0025: SOV backend produces visualization-ready Pydantic contracts.
    The frontend renders these directly without recomputing chart data.
    """

    def generate_variance_bar_chart(
        self,
        result: ANOVAResult,
        analysis_id: str,
    ) -> VisualizationSpec:
        """Create variance bar chart specification from ANOVA result.
        
        Shows the percentage of variance explained by each factor and residual.
        
        Args:
            result: ANOVA result containing variance percentages.
            analysis_id: Analysis ID for reference.
            
        Returns:
            VisualizationSpec with VarianceBarConfig.
        """
        # Extract factor rows (exclude Total which is always 100%)
        factor_rows = [r for r in result.rows if r.source not in ("Total",)]

        # Build component list
        components = [r.source for r in factor_rows]

        variance_bar = VarianceBarConfig(
            analysis_id=analysis_id,
            components=components,
            orientation="horizontal",
            show_values=True,
            value_format="{:.1f}%",
            sort_by_value=True,
            use_gradient=True,
        )

        spec_id = f"variance_bar_{result.response_column}_{uuid.uuid4().hex[:8]}"

        return VisualizationSpec(
            spec_id=spec_id,
            name=f"Variance Decomposition - {result.response_column}",
            description=(
                f"Percentage of variance explained by each factor for "
                f"{result.response_column}. R² = {result.r_squared:.3f}"
            ),
            viz_type=VisualizationType.VARIANCE_BAR,
            variance_bar=variance_bar,
            analysis_id=analysis_id,
            title=f"Variance Components: {result.response_column}",
            subtitle=f"Factors: {', '.join(result.factors)}",
            created_at=datetime.now(UTC),
            tags=["anova", "variance", result.response_column] + result.factors,
        )

    def generate_box_plot(
        self,
        result: ANOVAResult,
        factor: str,
        dataset_id: str | None = None,
    ) -> VisualizationSpec:
        """Create box plot specification for a single factor.
        
        Args:
            result: ANOVA result.
            factor: Factor column name for grouping.
            dataset_id: Source dataset ID.
            
        Returns:
            VisualizationSpec with BoxPlotConfig.
        """
        box_plot = BoxPlotConfig(
            factor_column=factor,
            response_column=result.response_column,
            show_outliers=True,
            show_means=True,
            show_points=True,
            jitter_amount=0.2,
            point_alpha=0.6,
            x_axis=AxisConfig(label=factor, show_grid=False),
            y_axis=AxisConfig(label=result.response_column, show_grid=True),
        )

        spec_id = f"boxplot_{factor}_{result.response_column}_{uuid.uuid4().hex[:8]}"

        return VisualizationSpec(
            spec_id=spec_id,
            name=f"Box Plot: {factor} vs {result.response_column}",
            description=f"Distribution of {result.response_column} by {factor} levels",
            viz_type=VisualizationType.BOX_PLOT,
            box_plot=box_plot,
            dataset_id=dataset_id,
            title=f"{result.response_column} by {factor}",
            created_at=datetime.now(UTC),
            tags=["boxplot", factor, result.response_column],
        )

    def generate_main_effects_plot(
        self,
        result: ANOVAResult,
        dataset_id: str | None = None,
    ) -> VisualizationSpec:
        """Create main effects plot for all factors.
        
        Args:
            result: ANOVA result.
            dataset_id: Source dataset ID.
            
        Returns:
            VisualizationSpec with MainEffectsPlotConfig.
        """
        main_effects = MainEffectsPlotConfig(
            factors=result.factors,
            response_column=result.response_column,
            plot_type="means",
            reference_line="grand_mean",
            show_error_bars=True,
            error_bar_type="se",
            layout="horizontal" if len(result.factors) <= 3 else "grid",
            share_y_axis=True,
        )

        spec_id = f"main_effects_{result.response_column}_{uuid.uuid4().hex[:8]}"

        return VisualizationSpec(
            spec_id=spec_id,
            name=f"Main Effects - {result.response_column}",
            description=f"Main effects of factors on {result.response_column}",
            viz_type=VisualizationType.MAIN_EFFECTS_PLOT,
            main_effects_plot=main_effects,
            dataset_id=dataset_id,
            title=f"Main Effects Plot: {result.response_column}",
            created_at=datetime.now(UTC),
            tags=["main_effects"] + result.factors + [result.response_column],
        )

    def generate_interaction_plot(
        self,
        result: ANOVAResult,
        factor_a: str,
        factor_b: str,
        dataset_id: str | None = None,
    ) -> VisualizationSpec:
        """Create interaction plot for two factors.
        
        Args:
            result: ANOVA result.
            factor_a: First factor (X-axis).
            factor_b: Second factor (lines).
            dataset_id: Source dataset ID.
            
        Returns:
            VisualizationSpec with InteractionPlotConfig.
        """
        interaction = InteractionPlotConfig(
            factor_a=factor_a,
            factor_b=factor_b,
            response_column=result.response_column,
            plot_type="means",
            show_error_bars=True,
            error_bar_type="se",
            confidence_level=0.95,
            line_style="solid",
            marker_style="o",
        )

        spec_id = f"interaction_{factor_a}_{factor_b}_{uuid.uuid4().hex[:8]}"

        return VisualizationSpec(
            spec_id=spec_id,
            name=f"Interaction: {factor_a} × {factor_b}",
            description=(
                f"Interaction effect between {factor_a} and {factor_b} "
                f"on {result.response_column}"
            ),
            viz_type=VisualizationType.INTERACTION_PLOT,
            interaction_plot=interaction,
            dataset_id=dataset_id,
            title=f"{factor_a} × {factor_b} Interaction",
            subtitle=f"Response: {result.response_column}",
            created_at=datetime.now(UTC),
            tags=["interaction", factor_a, factor_b, result.response_column],
        )

    def generate_residual_plot(
        self,
        analysis_id: str,
        plot_type: str = "histogram",
    ) -> VisualizationSpec:
        """Create residual diagnostic plot.
        
        Args:
            analysis_id: Analysis ID to get residuals from.
            plot_type: Type of residual plot.
            
        Returns:
            VisualizationSpec with ResidualPlotConfig.
        """
        residual = ResidualPlotConfig(
            analysis_id=analysis_id,
            plot_type=plot_type,
            bins=30,
            show_normal_curve=True,
            show_reference_line=True,
        )

        spec_id = f"residual_{plot_type}_{uuid.uuid4().hex[:8]}"

        return VisualizationSpec(
            spec_id=spec_id,
            name=f"Residual Plot ({plot_type})",
            description=f"Residual diagnostics: {plot_type}",
            viz_type=VisualizationType.RESIDUAL_PLOT,
            residual_plot=residual,
            analysis_id=analysis_id,
            title="Residual Diagnostics",
            created_at=datetime.now(UTC),
            tags=["residual", "diagnostics", plot_type],
        )

    def generate_all_visualizations(
        self,
        results: list[ANOVAResult],
        analysis_id: str,
        dataset_id: str | None = None,
    ) -> list[VisualizationSpec]:
        """Generate all standard visualizations for ANOVA results.
        
        Per ADR-0025: Produces a complete set of visualization contracts
        that can be included in the DataSet manifest.
        
        Args:
            results: List of ANOVA results (one per response column).
            analysis_id: Analysis ID.
            dataset_id: Source dataset ID.
            
        Returns:
            List of VisualizationSpec for all standard charts.
        """
        specs: list[VisualizationSpec] = []

        for result in results:
            # Always generate variance bar chart
            specs.append(self.generate_variance_bar_chart(result, analysis_id))

            # Generate box plots for each factor
            for factor in result.factors:
                specs.append(self.generate_box_plot(result, factor, dataset_id))

            # Generate main effects plot if multiple factors
            if len(result.factors) >= 1:
                specs.append(self.generate_main_effects_plot(result, dataset_id))

            # Generate interaction plots for 2+ factors
            if len(result.factors) >= 2:
                for i, factor_a in enumerate(result.factors):
                    for factor_b in result.factors[i + 1:]:
                        specs.append(
                            self.generate_interaction_plot(
                                result, factor_a, factor_b, dataset_id
                            )
                        )

            # Generate residual diagnostics
            specs.append(self.generate_residual_plot(analysis_id, "histogram"))
            specs.append(self.generate_residual_plot(analysis_id, "qq"))

        return specs

    def get_visualization_summary(
        self,
        specs: list[VisualizationSpec],
    ) -> dict:
        """Get summary of generated visualizations.
        
        Args:
            specs: List of visualization specs.
            
        Returns:
            Summary dict with counts by type.
        """
        type_counts: dict[str, int] = {}
        for spec in specs:
            viz_type = spec.viz_type.value
            type_counts[viz_type] = type_counts.get(viz_type, 0) + 1

        return {
            "total_count": len(specs),
            "by_type": type_counts,
            "spec_ids": [s.spec_id for s in specs],
        }
