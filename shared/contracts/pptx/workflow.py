"""PPTX Workflow contracts - guided workflow FSM for report generation.

Per ADR-0020: PPTX implements a 7-step guided workflow with forward gating.
Per ADR-0001: Core FSM pattern with 'simple_linear' state model.
Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).

This module defines contracts for:
- Workflow stage states and transitions
- Project lifecycle management
- Validation status tracking
- Generation request/response contracts

The PPTX workflow uses 'reset_validation' cascade policy:
- Modifying Steps 1-3 resets validation status of Steps 4-6
- Modifying Steps 4-5 resets Step 6 validation status
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


# =============================================================================
# Workflow Stage Definitions
# =============================================================================


class PPTXStageId(str, Enum):
    """Stage identifiers for the PPTX 7-step workflow.

    Per ADR-0020: Steps 1-3 are sequential, 4-5 can be parallel,
    6 requires 1-5, 7 requires 6 to pass.
    """

    UPLOAD_TEMPLATE = "upload_template"  # Step 1
    CONFIGURE_ENV = "configure_env"  # Step 2
    UPLOAD_DATA = "upload_data"  # Step 3
    MAP_CONTEXT = "map_context"  # Step 4
    MAP_METRICS = "map_metrics"  # Step 5
    VALIDATE = "validate"  # Step 6
    GENERATE = "generate"  # Step 7


class PPTXStageState(str, Enum):
    """State of a single workflow stage.

    Per ADR-0001: 'simple_linear' state model for PPTX.
    """

    NOT_STARTED = "not_started"  # Stage not yet begun
    IN_PROGRESS = "in_progress"  # Stage actively being worked on
    COMPLETED = "completed"  # Stage finished successfully
    INVALID = "invalid"  # Stage invalidated by upstream change
    ERROR = "error"  # Stage failed with error


class ValidationBarStatus(str, Enum):
    """Status of a single validation bar in the 'Four Green Bars' system.

    Per ADR-0020: Step 7 requires Step 6 to pass with 'Four Green Bars'.
    """

    NOT_CHECKED = "not_checked"  # Validation not yet run
    PASSING = "passing"  # Validation passed (green)
    WARNING = "warning"  # Validation passed with warnings (yellow)
    FAILING = "failing"  # Validation failed (red)


# =============================================================================
# Stage Configuration Contracts
# =============================================================================


class PPTXStageConfig(BaseModel):
    """Configuration for a single workflow stage.

    Defines stage metadata and dependencies for the FSM orchestrator.
    """

    stage_id: PPTXStageId
    name: str = Field(..., description="Human-readable stage name")
    step_number: int = Field(..., ge=1, le=7, description="Step number (1-7)")
    optional: bool = Field(False, description="Whether stage can be skipped")
    terminal: bool = Field(
        False,
        description="Whether this is the final stage (generate)",
    )
    dependencies: list[PPTXStageId] = Field(
        default_factory=list,
        description="Stages that must complete before this one",
    )
    invalidates_on_change: list[PPTXStageId] = Field(
        default_factory=list,
        description="Stages to invalidate when this stage changes",
    )


class PPTXStageGraphConfig(BaseModel):
    """Complete stage graph configuration for PPTX workflow.

    Per ADR-0020: 7-step pipeline with reset_validation cascade policy.
    """

    stages: list[PPTXStageConfig] = Field(
        ...,
        min_length=7,
        max_length=7,
        description="All 7 PPTX workflow stages",
    )
    cascade_policy: Literal["reset_validation", "cascade_reset", "none"] = Field(
        "reset_validation",
        description="How upstream changes affect downstream stages",
    )
    state_model: Literal["simple_linear", "lockable_with_acknowledgment"] = Field(
        "simple_linear",
        description="FSM state model (PPTX uses simple_linear)",
    )

    @classmethod
    def create_default(cls) -> "PPTXStageGraphConfig":
        """Create the default PPTX 7-step stage graph.

        Returns:
            Configured stage graph per ADR-0020.
        """
        return cls(
            stages=[
                PPTXStageConfig(
                    stage_id=PPTXStageId.UPLOAD_TEMPLATE,
                    name="Upload Template",
                    step_number=1,
                    dependencies=[],
                    invalidates_on_change=[
                        PPTXStageId.CONFIGURE_ENV,
                        PPTXStageId.MAP_CONTEXT,
                        PPTXStageId.MAP_METRICS,
                        PPTXStageId.VALIDATE,
                    ],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.CONFIGURE_ENV,
                    name="Configure Environment",
                    step_number=2,
                    dependencies=[PPTXStageId.UPLOAD_TEMPLATE],
                    invalidates_on_change=[
                        PPTXStageId.MAP_CONTEXT,
                        PPTXStageId.MAP_METRICS,
                        PPTXStageId.VALIDATE,
                    ],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.UPLOAD_DATA,
                    name="Upload Data",
                    step_number=3,
                    dependencies=[PPTXStageId.CONFIGURE_ENV],
                    invalidates_on_change=[
                        PPTXStageId.MAP_CONTEXT,
                        PPTXStageId.MAP_METRICS,
                        PPTXStageId.VALIDATE,
                    ],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.MAP_CONTEXT,
                    name="Map Context",
                    step_number=4,
                    dependencies=[PPTXStageId.UPLOAD_DATA],
                    invalidates_on_change=[PPTXStageId.VALIDATE],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.MAP_METRICS,
                    name="Map Metrics",
                    step_number=5,
                    dependencies=[PPTXStageId.UPLOAD_DATA],
                    invalidates_on_change=[PPTXStageId.VALIDATE],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.VALIDATE,
                    name="Validate",
                    step_number=6,
                    dependencies=[PPTXStageId.MAP_CONTEXT, PPTXStageId.MAP_METRICS],
                    invalidates_on_change=[],
                ),
                PPTXStageConfig(
                    stage_id=PPTXStageId.GENERATE,
                    name="Generate",
                    step_number=7,
                    terminal=True,
                    dependencies=[PPTXStageId.VALIDATE],
                    invalidates_on_change=[],
                ),
            ],
            cascade_policy="reset_validation",
            state_model="simple_linear",
        )


# =============================================================================
# Workflow State Contracts
# =============================================================================


class PPTXStageStatus(BaseModel):
    """Runtime status of a single workflow stage."""

    stage_id: PPTXStageId
    state: PPTXStageState = PPTXStageState.NOT_STARTED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    invalidated_at: datetime | None = None
    error_message: str | None = None
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)

    @property
    def is_actionable(self) -> bool:
        """Check if stage can be worked on (not blocked by dependencies)."""
        return self.state in (
            PPTXStageState.NOT_STARTED,
            PPTXStageState.IN_PROGRESS,
            PPTXStageState.INVALID,
        )


class ValidationResult(BaseModel):
    """Result of validation step (Step 6).

    Per ADR-0020: 'Four Green Bars' required for generation.
    """

    template_bar: ValidationBarStatus = ValidationBarStatus.NOT_CHECKED
    data_bar: ValidationBarStatus = ValidationBarStatus.NOT_CHECKED
    context_bar: ValidationBarStatus = ValidationBarStatus.NOT_CHECKED
    metrics_bar: ValidationBarStatus = ValidationBarStatus.NOT_CHECKED

    template_issues: list[str] = Field(default_factory=list)
    data_issues: list[str] = Field(default_factory=list)
    context_issues: list[str] = Field(default_factory=list)
    metrics_issues: list[str] = Field(default_factory=list)

    validated_at: datetime | None = None
    validation_duration_ms: float = Field(0.0, ge=0.0)

    @property
    def all_passing(self) -> bool:
        """Check if all four bars are passing (green)."""
        return all(
            bar == ValidationBarStatus.PASSING
            for bar in [
                self.template_bar,
                self.data_bar,
                self.context_bar,
                self.metrics_bar,
            ]
        )

    @property
    def can_generate(self) -> bool:
        """Check if generation is allowed (all bars passing or warning)."""
        allowed = {ValidationBarStatus.PASSING, ValidationBarStatus.WARNING}
        return all(
            bar in allowed
            for bar in [
                self.template_bar,
                self.data_bar,
                self.context_bar,
                self.metrics_bar,
            ]
        )


class PPTXWorkflowState(BaseModel):
    """Complete workflow state for a PPTX project.

    Tracks all stage statuses and validation results.
    """

    project_id: str = Field(..., description="Unique project identifier")
    stages: dict[PPTXStageId, PPTXStageStatus] = Field(
        default_factory=dict,
        description="Status of each workflow stage",
    )
    validation: ValidationResult = Field(
        default_factory=ValidationResult,
        description="Validation step results",
    )
    current_stage: PPTXStageId | None = Field(
        None,
        description="Currently active stage (for UI highlighting)",
    )
    created_at: datetime
    updated_at: datetime | None = None

    @property
    def completed_stages(self) -> list[PPTXStageId]:
        """Get list of completed stage IDs."""
        return [
            stage_id
            for stage_id, status in self.stages.items()
            if status.state == PPTXStageState.COMPLETED
        ]

    @property
    def can_generate(self) -> bool:
        """Check if generation step can proceed."""
        validate_status = self.stages.get(PPTXStageId.VALIDATE)
        if not validate_status or validate_status.state != PPTXStageState.COMPLETED:
            return False
        return self.validation.can_generate

    @classmethod
    def create_new(cls, project_id: str) -> "PPTXWorkflowState":
        """Create a new workflow state with all stages initialized.

        Args:
            project_id: Unique project identifier.

        Returns:
            New workflow state with NOT_STARTED stages.
        """
        now = datetime.utcnow().replace(microsecond=0)
        stages = {stage_id: PPTXStageStatus(stage_id=stage_id) for stage_id in PPTXStageId}
        return cls(
            project_id=project_id,
            stages=stages,
            created_at=now,
        )


# =============================================================================
# Project Contracts
# =============================================================================


class PPTXProject(BaseModel):
    """Complete PPTX project including workflow state and artifacts.

    A project represents a single report generation workflow instance.
    """

    # Identity
    project_id: str = Field(
        ...,
        description="Deterministic hash of project inputs",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None

    # Timestamps (per ADR-0009)
    created_at: datetime
    updated_at: datetime | None = None

    # Template reference
    template_id: str | None = Field(
        None,
        description="ID of uploaded template (set after Step 1)",
    )
    template_path: str | None = Field(
        None,
        description="Relative path to template file",
    )

    # Data reference
    dataset_ids: list[str] = Field(
        default_factory=list,
        description="IDs of uploaded datasets (set after Step 3)",
    )

    # Environment configuration (Step 2)
    environment_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Environment-specific configuration",
    )

    # Mapping configurations (Steps 4-5)
    context_mapping: dict[str, Any] = Field(
        default_factory=dict,
        description="Context dimension mappings",
    )
    metrics_mapping: dict[str, Any] = Field(
        default_factory=dict,
        description="Metric column mappings",
    )

    # Workflow state
    workflow_state: PPTXWorkflowState | None = None

    # Output (after Step 7)
    output_path: str | None = Field(
        None,
        description="Relative path to generated PPTX file",
    )
    output_size_bytes: int | None = Field(None, ge=0)

    # Metadata
    tags: list[str] = Field(default_factory=list)
    owner: str | None = None


class PPTXProjectRef(BaseModel):
    """Lightweight reference for project list responses."""

    project_id: str
    name: str
    template_id: str | None = None
    current_stage: PPTXStageId | None = None
    completed_steps: int = Field(0, ge=0, le=7)
    can_generate: bool = False
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    """Request to create a new PPTX project."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    template_id: str | None = Field(
        None,
        description="Optional: pre-select template",
    )


class UpdateProjectRequest(BaseModel):
    """Request to update project configuration."""

    name: str | None = None
    description: str | None = None
    environment_config: dict[str, Any] | None = None
    context_mapping: dict[str, Any] | None = None
    metrics_mapping: dict[str, Any] | None = None
    tags: list[str] | None = None


# =============================================================================
# Stage Transition Contracts
# =============================================================================


class StageTransitionRequest(BaseModel):
    """Request to transition a stage's state."""

    project_id: str
    stage_id: PPTXStageId
    target_state: PPTXStageState
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific data for the transition",
    )


class StageTransitionResult(BaseModel):
    """Result of a stage transition attempt."""

    success: bool
    project_id: str
    stage_id: PPTXStageId
    previous_state: PPTXStageState
    new_state: PPTXStageState
    invalidated_stages: list[PPTXStageId] = Field(
        default_factory=list,
        description="Stages that were invalidated by this transition",
    )
    error_message: str | None = None
    transitioned_at: datetime


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "PPTXStageId",
    "PPTXStageState",
    "ValidationBarStatus",
    # Stage configuration
    "PPTXStageConfig",
    "PPTXStageGraphConfig",
    # Workflow state
    "PPTXStageStatus",
    "ValidationResult",
    "PPTXWorkflowState",
    # Project
    "PPTXProject",
    "PPTXProjectRef",
    "CreateProjectRequest",
    "UpdateProjectRequest",
    # Transitions
    "StageTransitionRequest",
    "StageTransitionResult",
]
