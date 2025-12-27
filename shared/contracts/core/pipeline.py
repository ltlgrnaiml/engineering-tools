"""Pipeline contracts - multi-tool workflow orchestration.

A Pipeline defines a sequence of steps across tools, enabling workflows like:
  DAT (aggregate) → SOV (analyze) → PPTX (generate report)

Per ADR-0004: Pipeline IDs are deterministic.
Per ADR-0008: All timestamps are ISO-8601 UTC.
Per ADR-0013: Cancellation preserves completed artifacts.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class PipelineStepType(str, Enum):
    """Available step types in a pipeline."""

    # Data Aggregator steps
    DAT_AGGREGATE = "dat:aggregate"
    DAT_EXPORT = "dat:export"

    # SOV Analyzer steps
    SOV_ANOVA = "sov:anova"
    SOV_VARIANCE_COMPONENTS = "sov:variance_components"

    # PowerPoint Generator steps
    PPTX_GENERATE = "pptx:generate"
    PPTX_RENDER = "pptx:render"


class PipelineStepState(str, Enum):
    """State of a pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStep(BaseModel):
    """A single step in a cross-tool pipeline."""

    step_index: int = Field(..., ge=0)
    step_type: PipelineStepType
    name: str | None = Field(None, description="Optional human-readable step name")

    # Input/Output DataSets
    input_dataset_ids: list[str] = Field(
        default_factory=list,
        description="DataSet IDs to use as input. Use '$step_N_output' for dynamic refs.",
    )
    output_dataset_id: str | None = Field(
        None,
        description="DataSet ID produced by this step (set after completion)",
    )

    # Tool-specific configuration
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration for this step",
    )

    # State tracking
    state: PipelineStepState = PipelineStepState.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)


class Pipeline(BaseModel):
    """A multi-tool workflow definition and execution state.

    Pipelines enable chaining tools together:
    1. User creates pipeline with steps
    2. Gateway orchestrates execution across tools
    3. Each step produces DataSets consumed by later steps
    4. Final outputs (e.g., PPTX report) are tracked

    Example:
        Pipeline(
            name="Full Analysis Report",
            steps=[
                PipelineStep(step_type="dat:aggregate", config={...}),
                PipelineStep(step_type="sov:anova", input_dataset_ids=["$step_0_output"]),
                PipelineStep(step_type="pptx:generate", input_dataset_ids=["$step_0_output", "$step_1_output"]),
            ]
        )
    """

    # Identity
    pipeline_id: str = Field(
        ...,
        description="Deterministic hash of pipeline definition",
    )
    name: str

    # Timestamps
    created_at: datetime
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Steps
    steps: list[PipelineStep] = Field(
        default_factory=list,
        min_length=1,
    )

    # Execution state
    current_step: int = Field(0, ge=0)
    state: Literal["draft", "queued", "running", "completed", "failed", "cancelled"] = "draft"

    # Final outputs
    output_artifact_paths: list[str] = Field(
        default_factory=list,
        description="Relative paths to final output artifacts (e.g., report.pptx)",
    )

    # Metadata
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class PipelineRef(BaseModel):
    """Lightweight reference to a Pipeline for list responses."""

    pipeline_id: str
    name: str
    state: str
    step_count: int
    current_step: int
    created_at: datetime
    updated_at: datetime | None = None


class CreatePipelineRequest(BaseModel):
    """Request to create a new pipeline."""

    name: str
    description: str | None = None
    steps: list[PipelineStep]
    tags: list[str] = Field(default_factory=list)
    auto_execute: bool = Field(
        False,
        description="If true, immediately queue pipeline for execution",
    )
