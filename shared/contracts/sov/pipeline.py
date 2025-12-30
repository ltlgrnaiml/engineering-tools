"""SOV Pipeline contracts - analysis pipeline stages and orchestration.

Per ADR-0022: SOV implements ANOVA-based variance decomposition using a
5-stage pipeline: Data Ingestion, Factor Identification, ANOVA Computation,
Variance Decomposition, Visualization Preparation.

Per ADR-0001: Pipeline follows core FSM pattern.
Per ADR-0004: Pipeline IDs are deterministic (SHA-256 hash of inputs).
Per ADR-0008: All timestamps are ISO-8601 UTC (no microseconds).

This module defines contracts for:
- Pipeline stage definitions and states
- Stage configuration and results
- Pipeline execution tracking
- Job management contracts
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

__version__ = "0.1.0"


# =============================================================================
# Pipeline Stage Definitions
# =============================================================================


class SOVStageId(str, Enum):
    """Stage identifiers for the SOV 5-stage pipeline.

    Per ADR-0022: 5-stage pipeline for ANOVA analysis.
    """

    DATA_INGESTION = "data_ingestion"  # Stage 1: Load from DataSet
    FACTOR_IDENTIFICATION = "factor_identification"  # Stage 2: Detect factors
    ANOVA_COMPUTATION = "anova_computation"  # Stage 3: Run ANOVA
    VARIANCE_DECOMPOSITION = "variance_decomposition"  # Stage 4: Decompose variance
    VISUALIZATION_PREPARATION = "visualization_preparation"  # Stage 5: Generate viz contracts


class SOVStageState(str, Enum):
    """State of a pipeline stage."""

    PENDING = "pending"  # Not yet started
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Failed with error
    SKIPPED = "skipped"  # Skipped (optional stage)
    CANCELLED = "cancelled"  # Cancelled by user


class SOVPipelineState(str, Enum):
    """Overall state of the SOV pipeline."""

    DRAFT = "draft"  # Configuration in progress
    QUEUED = "queued"  # Waiting to start
    RUNNING = "running"  # Execution in progress
    COMPLETED = "completed"  # All stages complete
    FAILED = "failed"  # Pipeline failed
    CANCELLED = "cancelled"  # User cancelled


# =============================================================================
# Stage Configuration Contracts
# =============================================================================


class DataIngestionConfig(BaseModel):
    """Configuration for Stage 1: Data Ingestion.

    Per ADR-0023: Input loaded via DataSetRef.
    """

    dataset_id: str = Field(..., description="Input DataSet ID to load")
    filter_expression: str | None = Field(
        None,
        description="Filter expression to apply (pandas query syntax)",
    )
    sample_size: int | None = Field(
        None,
        ge=100,
        description="Sample size for large datasets (None = use all)",
    )
    random_seed: int = Field(42, description="Seed for sampling")


class FactorIdentificationConfig(BaseModel):
    """Configuration for Stage 2: Factor Identification.

    Identifies which columns are categorical factors vs numeric responses.
    """

    factor_columns: list[str] | None = Field(
        None,
        description="Explicit factor columns (None = auto-detect)",
    )
    response_columns: list[str] | None = Field(
        None,
        description="Explicit response columns (None = auto-detect)",
    )
    exclude_columns: list[str] = Field(
        default_factory=list,
        description="Columns to exclude from analysis",
    )
    max_factor_levels: int = Field(
        100,
        ge=2,
        le=1000,
        description="Max unique values for auto-detection as factor",
    )
    min_numeric_values: int = Field(
        10,
        ge=2,
        description="Min non-null values for numeric detection",
    )


class ANOVAComputationConfig(BaseModel):
    """Configuration for Stage 3: ANOVA Computation.

    References ANOVAConfig from anova.py for detailed settings.
    """

    response_column: str = Field(..., description="Numeric response column to analyze")
    factor_columns: list[str] = Field(
        ...,
        min_length=1,
        description="Factor columns for the ANOVA model",
    )
    ss_type: Literal["type_i", "type_ii", "type_iii"] = Field(
        "type_iii",
        description="Sum of squares type (per ADR-0022: Type III for unbalanced data)",
    )
    include_interactions: bool = Field(True, description="Include interaction terms")
    max_interaction_order: int = Field(2, ge=1, le=4)
    alpha: float = Field(0.05, gt=0, lt=1, description="Significance level")
    run_post_hoc: bool = Field(True, description="Run post-hoc comparisons")
    post_hoc_method: Literal["tukey", "bonferroni", "scheffe"] = "tukey"


class VarianceDecompositionConfig(BaseModel):
    """Configuration for Stage 4: Variance Decomposition.

    Computes percentage contribution per factor.
    """

    method: Literal["anova", "reml", "ml"] = Field(
        "anova",
        description="Variance estimation method",
    )
    include_residual: bool = Field(True, description="Include residual variance")
    include_interactions: bool = Field(
        True,
        description="Include interaction terms in decomposition",
    )
    confidence_level: float = Field(0.95, gt=0, lt=1)


class VisualizationPreparationConfig(BaseModel):
    """Configuration for Stage 5: Visualization Preparation.

    Generates chart-ready data contracts.
    """

    generate_box_plots: bool = Field(True, description="Generate box plot specs")
    generate_interaction_plots: bool = Field(True, description="Generate interaction plots")
    generate_main_effects_plots: bool = Field(True, description="Generate main effects plots")
    generate_variance_bar: bool = Field(True, description="Generate variance contribution bar")
    generate_residual_plots: bool = Field(True, description="Generate residual diagnostics")
    chart_style: str | None = Field(None, description="Named chart style preset")
    color_palette: str | None = Field(None, description="Named color palette")


# =============================================================================
# Stage Result Contracts
# =============================================================================


class DataIngestionResult(BaseModel):
    """Result from Stage 1: Data Ingestion."""

    rows_loaded: int = Field(..., ge=0)
    columns_loaded: int = Field(..., ge=0)
    rows_after_filter: int = Field(..., ge=0)
    bytes_loaded: int = Field(..., ge=0)
    null_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Null count per column",
    )
    load_duration_ms: float = Field(..., ge=0)


class FactorIdentificationResult(BaseModel):
    """Result from Stage 2: Factor Identification."""

    detected_factors: list[str] = Field(
        default_factory=list,
        description="Columns identified as factors",
    )
    detected_responses: list[str] = Field(
        default_factory=list,
        description="Columns identified as responses",
    )
    excluded_columns: list[str] = Field(
        default_factory=list,
        description="Columns excluded from analysis",
    )
    factor_level_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Factor -> level count mapping",
    )
    detection_warnings: list[str] = Field(default_factory=list)
    detection_duration_ms: float = Field(..., ge=0)


class ANOVAComputationResult(BaseModel):
    """Result from Stage 3: ANOVA Computation.

    References ANOVAResult from anova.py for detailed results.
    """

    analysis_id: str = Field(..., description="Reference to full ANOVAResult")
    significant_effects: list[str] = Field(
        default_factory=list,
        description="Names of significant effects",
    )
    non_significant_effects: list[str] = Field(default_factory=list)
    model_r_squared: float = Field(..., ge=0, le=1)
    total_effects_count: int = Field(..., ge=0)
    computation_duration_ms: float = Field(..., ge=0)


class VarianceDecompositionResult(BaseModel):
    """Result from Stage 4: Variance Decomposition."""

    components: dict[str, float] = Field(
        ...,
        description="Component -> variance percentage mapping",
    )
    total_variance: float = Field(..., ge=0)
    residual_variance_pct: float = Field(..., ge=0, le=100)
    largest_contributor: str = Field(..., description="Component with highest variance")
    decomposition_duration_ms: float = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_percentages_sum(self) -> "VarianceDecompositionResult":
        """Validate variance percentages sum to ~100%."""
        total = sum(self.components.values())
        if not (99.0 <= total <= 101.0):
            raise ValueError(f"Variance components must sum to ~100%, got {total:.2f}%")
        return self


class VisualizationPreparationResult(BaseModel):
    """Result from Stage 5: Visualization Preparation."""

    visualizations_generated: int = Field(..., ge=0)
    visualization_ids: list[str] = Field(
        default_factory=list,
        description="IDs of generated visualization specs",
    )
    visualization_types: list[str] = Field(
        default_factory=list,
        description="Types of visualizations generated",
    )
    preparation_duration_ms: float = Field(..., ge=0)


# =============================================================================
# Stage Status Tracking
# =============================================================================


class SOVStageStatus(BaseModel):
    """Runtime status of a pipeline stage."""

    stage_id: SOVStageId
    state: SOVStageState = SOVStageState.PENDING
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    progress_message: str | None = None

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Configuration and results (type depends on stage)
    config: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)

    # Error tracking
    error_code: str | None = None
    error_message: str | None = None
    retry_count: int = Field(0, ge=0)

    @property
    def duration_ms(self) -> float | None:
        """Calculate stage duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None


# =============================================================================
# Pipeline Contracts
# =============================================================================


class SOVPipelineConfig(BaseModel):
    """Complete configuration for a SOV analysis pipeline."""

    # Stage configurations
    data_ingestion: DataIngestionConfig
    factor_identification: FactorIdentificationConfig = Field(
        default_factory=FactorIdentificationConfig,
    )
    anova_computation: ANOVAComputationConfig | None = Field(
        None,
        description="Set after factor identification",
    )
    variance_decomposition: VarianceDecompositionConfig = Field(
        default_factory=VarianceDecompositionConfig,
    )
    visualization_preparation: VisualizationPreparationConfig = Field(
        default_factory=VisualizationPreparationConfig,
    )

    # Pipeline options
    stop_on_first_error: bool = Field(
        True,
        description="Stop pipeline on first stage error",
    )
    save_intermediate_results: bool = Field(
        True,
        description="Save results after each stage",
    )


class SOVPipeline(BaseModel):
    """Complete SOV analysis pipeline.

    Per ADR-0022: 5-stage pipeline for ANOVA-based variance decomposition.
    """

    # Identity (per ADR-0004: deterministic hash)
    pipeline_id: str = Field(
        ...,
        description="Deterministic SHA-256 hash of inputs + config",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None

    # Timestamps (per ADR-0008)
    created_at: datetime
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Configuration
    config: SOVPipelineConfig

    # Stage tracking
    stages: dict[SOVStageId, SOVStageStatus] = Field(
        default_factory=dict,
        description="Status of each pipeline stage",
    )
    current_stage: SOVStageId | None = None

    # Overall state
    state: SOVPipelineState = SOVPipelineState.DRAFT

    # Results references
    input_dataset_id: str = Field(..., description="Input DataSet ID")
    output_dataset_id: str | None = Field(
        None,
        description="Output DataSet ID (created after completion)",
    )
    analysis_id: str | None = Field(
        None,
        description="Reference to ANOVAResult or VarianceComponentsResult",
    )

    # Metadata
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def create_new(
        cls,
        pipeline_id: str,
        name: str,
        config: SOVPipelineConfig,
    ) -> "SOVPipeline":
        """Create a new pipeline with initialized stages.

        Args:
            pipeline_id: Unique pipeline identifier.
            name: Human-readable pipeline name.
            config: Pipeline configuration.

        Returns:
            New pipeline with PENDING stages.
        """
        now = datetime.utcnow().replace(microsecond=0)
        stages = {
            stage_id: SOVStageStatus(stage_id=stage_id) for stage_id in SOVStageId
        }
        return cls(
            pipeline_id=pipeline_id,
            name=name,
            config=config,
            stages=stages,
            created_at=now,
            input_dataset_id=config.data_ingestion.dataset_id,
        )

    @property
    def completed_stages(self) -> list[SOVStageId]:
        """Get list of completed stage IDs."""
        return [
            stage_id
            for stage_id, status in self.stages.items()
            if status.state == SOVStageState.COMPLETED
        ]

    @property
    def progress_pct(self) -> float:
        """Calculate overall pipeline progress."""
        if not self.stages:
            return 0.0
        total = sum(status.progress_pct for status in self.stages.values())
        return total / len(self.stages)


class SOVPipelineRef(BaseModel):
    """Lightweight reference for pipeline list responses."""

    pipeline_id: str
    name: str
    state: SOVPipelineState
    current_stage: SOVStageId | None
    progress_pct: float
    input_dataset_id: str
    created_at: datetime
    completed_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


# =============================================================================
# Job Management Contracts
# =============================================================================


class CreatePipelineRequest(BaseModel):
    """Request to create a new SOV analysis pipeline."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    config: SOVPipelineConfig
    tags: list[str] = Field(default_factory=list)
    auto_start: bool = Field(
        False,
        description="Start execution immediately after creation",
    )


class StartPipelineRequest(BaseModel):
    """Request to start pipeline execution."""

    pipeline_id: str
    resume_from_stage: SOVStageId | None = Field(
        None,
        description="Resume from specific stage (None = start from beginning)",
    )


class CancelPipelineRequest(BaseModel):
    """Request to cancel a running pipeline."""

    pipeline_id: str
    reason: str | None = None


class PipelineProgressUpdate(BaseModel):
    """Progress update during pipeline execution."""

    pipeline_id: str
    stage_id: SOVStageId
    progress_pct: float = Field(..., ge=0.0, le=100.0)
    message: str | None = None
    updated_at: datetime


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "SOVStageId",
    "SOVStageState",
    "SOVPipelineState",
    # Stage configurations
    "DataIngestionConfig",
    "FactorIdentificationConfig",
    "ANOVAComputationConfig",
    "VarianceDecompositionConfig",
    "VisualizationPreparationConfig",
    # Stage results
    "DataIngestionResult",
    "FactorIdentificationResult",
    "ANOVAComputationResult",
    "VarianceDecompositionResult",
    "VisualizationPreparationResult",
    # Stage status
    "SOVStageStatus",
    # Pipeline
    "SOVPipelineConfig",
    "SOVPipeline",
    "SOVPipelineRef",
    # Job management
    "CreatePipelineRequest",
    "StartPipelineRequest",
    "CancelPipelineRequest",
    "PipelineProgressUpdate",
]
