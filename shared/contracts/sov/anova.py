"""SOV ANOVA contracts - analysis of variance and variance components.

Per ADR-0023: SOV pipeline produces standardized analysis results.
Per ADR-0024: SOV integrates with DataSet contracts for input/output.
Per ADR-0005: Analysis IDs are deterministic (hash of inputs + config).
Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).

This module defines contracts for:
- ANOVA analysis configuration and results
- Variance components decomposition
- Post-hoc testing
- Analysis request/response lifecycle

All contracts are domain-agnostic; factor names, response columns,
and grouping variables are specified in configuration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


class ANOVAType(str, Enum):
    """Type of ANOVA analysis."""

    ONE_WAY = "one_way"  # Single factor
    TWO_WAY = "two_way"  # Two factors
    N_WAY = "n_way"  # Multiple factors
    NESTED = "nested"  # Hierarchical/nested factors
    MIXED = "mixed"  # Mixed effects (fixed + random)
    REPEATED_MEASURES = "repeated_measures"  # Within-subjects


class EffectType(str, Enum):
    """Type of factor effect in the model."""

    FIXED = "fixed"  # Fixed effect (specific levels of interest)
    RANDOM = "random"  # Random effect (sample from population)


class SumOfSquaresType(str, Enum):
    """Type of sum of squares calculation."""

    TYPE_I = "type_i"  # Sequential (order matters)
    TYPE_II = "type_ii"  # Each effect adjusted for others at same level
    TYPE_III = "type_iii"  # Each effect adjusted for all other effects


class PostHocMethod(str, Enum):
    """Post-hoc comparison methods."""

    TUKEY = "tukey"  # Tukey's HSD
    BONFERRONI = "bonferroni"  # Bonferroni correction
    SCHEFFE = "scheffe"  # Scheffé's method
    DUNNETT = "dunnett"  # Dunnett's test (vs control)
    LSD = "lsd"  # Fisher's LSD
    SIDAK = "sidak"  # Šidák correction
    HOLM = "holm"  # Holm-Bonferroni


class FactorConfig(BaseModel):
    """Configuration for a single factor in the ANOVA model."""

    column: str = Field(..., description="Column name in input dataset")
    name: str | None = Field(
        None,
        description="Display name (default: column name)",
    )
    effect_type: EffectType = EffectType.FIXED
    nested_within: str | None = Field(
        None,
        description="Column this factor is nested within",
    )
    is_repeated: bool = Field(
        False,
        description="True if this is a repeated measures factor",
    )
    reference_level: str | None = Field(
        None,
        description="Reference level for effect coding",
    )


class ANOVAConfig(BaseModel):
    """Configuration for ANOVA analysis.

    This is the primary input contract for running ANOVA.
    All domain-specific information (which columns are factors,
    which are responses) is captured here.
    """

    # Analysis type
    anova_type: ANOVAType = ANOVAType.ONE_WAY
    ss_type: SumOfSquaresType = SumOfSquaresType.TYPE_III

    # Factors
    factors: list[FactorConfig] = Field(
        ...,
        min_length=1,
        description="Factor columns for the analysis",
    )

    # Response
    response_column: str = Field(..., description="Numeric response column")
    response_transform: Literal["none", "log", "sqrt", "inverse"] | None = Field(
        None,
        description="Transform to apply to response",
    )

    # Interactions
    include_interactions: bool = Field(
        True,
        description="Include interaction terms",
    )
    max_interaction_order: int = Field(
        2,
        ge=1,
        le=5,
        description="Maximum interaction order (2 = two-way only)",
    )
    specific_interactions: list[list[str]] | None = Field(
        None,
        description="Specific interactions to include (overrides auto)",
    )

    # Subject/blocking
    subject_column: str | None = Field(
        None,
        description="Subject ID column (for repeated measures)",
    )
    block_column: str | None = Field(
        None,
        description="Blocking factor column",
    )

    # Post-hoc
    run_post_hoc: bool = Field(True, description="Run post-hoc comparisons")
    post_hoc_method: PostHocMethod = PostHocMethod.TUKEY
    post_hoc_alpha: float = Field(0.05, gt=0, lt=1)

    # Significance
    alpha: float = Field(0.05, gt=0, lt=1)

    # Filtering
    filter_expression: str | None = Field(
        None,
        description="Filter input data (pandas query syntax)",
    )
    dropna: bool = Field(True, description="Drop rows with missing values")

    # Determinism
    seed: int = Field(42, description="Random seed for any randomized operations")

    @model_validator(mode="after")
    def validate_factors(self) -> "ANOVAConfig":
        """Validate factor configuration matches ANOVA type."""
        n_factors = len(self.factors)

        if self.anova_type == ANOVAType.ONE_WAY and n_factors != 1:
            raise ValueError(f"ONE_WAY ANOVA requires exactly 1 factor, got {n_factors}")
        if self.anova_type == ANOVAType.TWO_WAY and n_factors != 2:
            raise ValueError(f"TWO_WAY ANOVA requires exactly 2 factors, got {n_factors}")

        # Check for nested within references
        factor_cols = {f.column for f in self.factors}
        for factor in self.factors:
            if factor.nested_within and factor.nested_within not in factor_cols:
                raise ValueError(
                    f"Factor {factor.column} nested_within '{factor.nested_within}' "
                    f"not found in factors"
                )

        return self


class FactorEffect(BaseModel):
    """Results for a single factor or interaction effect."""

    effect_name: str = Field(..., description="Factor name or interaction (e.g., 'A', 'A:B')")
    effect_type: EffectType
    is_interaction: bool = False

    # ANOVA table values
    sum_of_squares: float = Field(..., ge=0)
    degrees_of_freedom: int = Field(..., ge=0)
    mean_square: float = Field(..., ge=0)
    f_statistic: float | None = Field(None, ge=0)
    p_value: float | None = Field(None, ge=0, le=1)

    # Effect size
    eta_squared: float | None = Field(None, ge=0, le=1)
    partial_eta_squared: float | None = Field(None, ge=0, le=1)
    omega_squared: float | None = Field(None, ge=0, le=1)

    # Significance
    is_significant: bool = False
    alpha: float = 0.05

    # Factor levels (for reference)
    levels: list[str] = Field(default_factory=list)
    level_count: int = Field(0, ge=0)


class VarianceComponent(BaseModel):
    """Variance component from random effects model."""

    component_name: str = Field(..., description="Name of variance component")
    variance_estimate: float = Field(..., ge=0)
    std_error: float | None = Field(None, ge=0)
    variance_percent: float = Field(..., ge=0, le=100)
    confidence_lower: float | None = Field(None, ge=0)
    confidence_upper: float | None = None
    is_negative: bool = Field(
        False,
        description="True if raw estimate was negative (set to 0)",
    )


class PostHocComparison(BaseModel):
    """Single pairwise comparison from post-hoc test."""

    group_1: str
    group_2: str
    mean_diff: float
    std_error: float = Field(..., ge=0)
    t_statistic: float | None = None
    p_value: float = Field(..., ge=0, le=1)
    p_adjusted: float = Field(..., ge=0, le=1)
    confidence_lower: float | None = None
    confidence_upper: float | None = None
    is_significant: bool = False


class PostHocResult(BaseModel):
    """Complete results from post-hoc analysis."""

    factor_name: str
    method: PostHocMethod
    alpha: float
    comparisons: list[PostHocComparison] = Field(default_factory=list)
    significant_count: int = Field(0, ge=0)
    total_count: int = Field(0, ge=0)


class ANOVASummary(BaseModel):
    """Summary statistics from the ANOVA."""

    grand_mean: float
    grand_std: float
    total_n: int = Field(..., ge=0)
    total_ss: float = Field(..., ge=0)
    total_df: int = Field(..., ge=0)
    error_ss: float = Field(..., ge=0)
    error_df: int = Field(..., ge=0)
    error_ms: float = Field(..., ge=0)
    model_r_squared: float = Field(..., ge=0, le=1)
    adjusted_r_squared: float | None = None


class ResidualDiagnostics(BaseModel):
    """Residual diagnostics for model validation."""

    # Normality
    shapiro_w: float | None = None
    shapiro_p: float | None = None
    is_normal: bool | None = None

    # Homoscedasticity
    levene_w: float | None = None
    levene_p: float | None = None
    is_homoscedastic: bool | None = None

    # Independence (Durbin-Watson)
    durbin_watson: float | None = None

    # Outliers
    outlier_count: int = Field(0, ge=0)
    outlier_indices: list[int] = Field(default_factory=list)


class ANOVAResult(BaseModel):
    """Complete ANOVA analysis result.

    This is the primary output contract for ANOVA analysis.
    Per ADR-0005: analysis_id is deterministic hash of inputs + config.
    """

    # Identity
    analysis_id: str = Field(
        ...,
        description="Deterministic hash of inputs + config",
    )
    analysis_type: ANOVAType

    # Source
    input_dataset_id: str
    output_dataset_id: str | None = Field(
        None,
        description="DataSet containing detailed results",
    )

    # Timestamps (per ADR-0009)
    created_at: datetime
    completed_at: datetime | None = None

    # Configuration (immutable)
    config: ANOVAConfig

    # Results
    summary: ANOVASummary
    effects: list[FactorEffect] = Field(default_factory=list)
    variance_components: list[VarianceComponent] = Field(default_factory=list)
    post_hoc_results: list[PostHocResult] = Field(default_factory=list)

    # Diagnostics
    diagnostics: ResidualDiagnostics | None = None

    # Group means for reference
    group_means: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Factor -> {level: mean}",
    )
    group_counts: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Factor -> {level: count}",
    )

    # Metrics
    analysis_duration_ms: float = Field(0.0, ge=0.0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def significant_effects(self) -> list[FactorEffect]:
        """Return only statistically significant effects."""
        return [e for e in self.effects if e.is_significant]

    @property
    def has_significant_effects(self) -> bool:
        """Check if any effects are significant."""
        return len(self.significant_effects) > 0


class ANOVAResultRef(BaseModel):
    """Lightweight reference for ANOVA result list responses."""

    analysis_id: str
    analysis_type: ANOVAType
    input_dataset_id: str
    response_column: str
    factor_count: int
    effect_count: int
    significant_count: int
    model_r_squared: float
    created_at: datetime


class VarianceComponentsConfig(BaseModel):
    """Configuration for variance components analysis.

    Decomposes total variance into hierarchical components.
    """

    # Hierarchy (from lowest to highest level)
    hierarchy: list[str] = Field(
        ...,
        min_length=2,
        description="Column hierarchy from lowest to highest level",
    )
    hierarchy_names: list[str] | None = Field(
        None,
        description="Display names for hierarchy levels",
    )

    # Response
    response_column: str
    response_transform: Literal["none", "log", "sqrt", "inverse"] | None = None

    # Method
    method: Literal["anova", "reml", "ml"] = Field(
        "anova",
        description="Estimation method",
    )

    # Options
    include_negative: bool = Field(
        False,
        description="Allow negative variance estimates (default: set to 0)",
    )
    confidence_level: float = Field(0.95, gt=0, lt=1)

    # Filtering
    filter_expression: str | None = None
    dropna: bool = True

    @model_validator(mode="after")
    def validate_hierarchy_names(self) -> "VarianceComponentsConfig":
        """Ensure hierarchy names match if provided."""
        if self.hierarchy_names and len(self.hierarchy_names) != len(self.hierarchy):
            raise ValueError(
                f"hierarchy_names count ({len(self.hierarchy_names)}) must match "
                f"hierarchy count ({len(self.hierarchy)})"
            )
        return self


class VarianceComponentsResult(BaseModel):
    """Result of variance components analysis."""

    analysis_id: str
    input_dataset_id: str
    output_dataset_id: str | None = None

    created_at: datetime
    completed_at: datetime | None = None

    config: VarianceComponentsConfig

    # Components (from lowest to highest + residual)
    components: list[VarianceComponent] = Field(default_factory=list)
    total_variance: float = Field(..., ge=0)
    residual_variance: float = Field(..., ge=0)

    # Metrics
    analysis_duration_ms: float = Field(0.0, ge=0.0)
    warnings: list[str] = Field(default_factory=list)


class PostHocTest(BaseModel):
    """Request for a standalone post-hoc test."""

    analysis_id: str = Field(..., description="ANOVA result to run post-hoc on")
    factor_name: str = Field(..., description="Factor to compare levels")
    method: PostHocMethod = PostHocMethod.TUKEY
    alpha: float = Field(0.05, gt=0, lt=1)
    control_group: str | None = Field(
        None,
        description="Control group for Dunnett's test",
    )


class AnalysisState(str, Enum):
    """State of an analysis operation."""

    PENDING = "pending"
    LOADING_DATA = "loading_data"
    ANALYZING = "analyzing"
    POST_HOC = "post_hoc"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisRequest(BaseModel):
    """Request to run a SOV analysis."""

    # Type of analysis
    analysis_type: Literal["anova", "variance_components"] = "anova"

    # Input
    dataset_id: str = Field(..., description="Input dataset ID")

    # Configuration (one must be set based on type)
    anova_config: ANOVAConfig | None = None
    variance_config: VarianceComponentsConfig | None = None

    # Job tracking
    job_id: str | None = Field(
        None,
        description="Parent job ID for pipeline tracking",
    )

    # Output
    save_results: bool = Field(True, description="Save results as DataSet")
    output_name: str | None = Field(
        None,
        description="Name for output DataSet",
    )

    @model_validator(mode="after")
    def validate_config(self) -> "AnalysisRequest":
        """Ensure correct config is provided for analysis type."""
        if self.analysis_type == "anova" and self.anova_config is None:
            raise ValueError("anova_config required for anova analysis")
        if self.analysis_type == "variance_components" and self.variance_config is None:
            raise ValueError("variance_config required for variance_components analysis")
        return self


class AnalysisResult(BaseModel):
    """Result wrapper for any SOV analysis."""

    request_id: str = Field(..., description="Unique request ID")
    analysis_type: Literal["anova", "variance_components"]
    state: AnalysisState = AnalysisState.PENDING

    # Progress
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    progress_message: str | None = None

    # Timestamps
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Results (one will be populated based on type)
    anova_result: ANOVAResult | None = None
    variance_result: VarianceComponentsResult | None = None

    # Errors
    error_message: str | None = None
    error_details: dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if analysis completed successfully."""
        return self.state == AnalysisState.COMPLETED and self.error_message is None
