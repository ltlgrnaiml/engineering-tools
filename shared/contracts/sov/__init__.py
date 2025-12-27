"""SOV (Sources of Variation Analyzer) contracts.

This package contains Pydantic models for SOV-specific data structures:
- ANOVA contracts for analysis of variance results
- Variance components contracts for hierarchical variance decomposition
- Visualization contracts for chart/plot specifications

All contracts are domain-agnostic; user-specific knowledge (factor names,
response columns, grouping levels) is injected via analysis configs.
"""

from shared.contracts.sov.anova import (
    ANOVAConfig,
    ANOVAResult,
    ANOVAResultRef,
    ANOVASummary,
    FactorEffect,
    VarianceComponent,
    VarianceComponentsConfig,
    VarianceComponentsResult,
    PostHocTest,
    PostHocResult,
    AnalysisRequest,
    AnalysisResult,
)
from shared.contracts.sov.visualization import (
    VisualizationType,
    VisualizationSpec,
    VisualizationResult,
    BoxPlotConfig,
    InteractionPlotConfig,
    MainEffectsPlotConfig,
    VarianceBarConfig,
    ResidualPlotConfig,
    NormalProbabilityPlotConfig,
    PlotStyle,
    ColorPalette,
)

__all__ = [
    # ANOVA contracts
    "ANOVAConfig",
    "ANOVAResult",
    "ANOVAResultRef",
    "ANOVASummary",
    "FactorEffect",
    "VarianceComponent",
    "VarianceComponentsConfig",
    "VarianceComponentsResult",
    "PostHocTest",
    "PostHocResult",
    "AnalysisRequest",
    "AnalysisResult",
    # Visualization contracts
    "VisualizationType",
    "VisualizationSpec",
    "VisualizationResult",
    "BoxPlotConfig",
    "InteractionPlotConfig",
    "MainEffectsPlotConfig",
    "VarianceBarConfig",
    "ResidualPlotConfig",
    "NormalProbabilityPlotConfig",
    "PlotStyle",
    "ColorPalette",
]
