"""PPTX Workflow FSM - 7-step guided workflow per ADR-0020.

Implements the 'simple_linear' state model with 'reset_validation' cascade policy.

Steps:
1. Upload Template
2. Configure Environment  
3. Upload Data
4. Map Context
5. Map Metrics
6. Validate
7. Generate

Per ADR-0020: Generate button MUST be disabled until Step 6 passes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from enum import Enum
from typing import Any
from uuid import UUID

__version__ = "0.1.0"


class WorkflowStep(str, Enum):
    """The 7 steps in PPTX workflow per ADR-0020."""

    UPLOAD_TEMPLATE = "upload_template"
    CONFIGURE_ENV = "configure_env"
    UPLOAD_DATA = "upload_data"
    MAP_CONTEXT = "map_context"
    MAP_METRICS = "map_metrics"
    VALIDATE = "validate"
    GENERATE = "generate"


class StepStatus(str, Enum):
    """Status of a workflow step."""

    PENDING = "pending"  # Not yet started
    IN_PROGRESS = "in_progress"  # Currently active
    COMPLETED = "completed"  # Successfully completed
    INVALID = "invalid"  # Validation failed
    SKIPPED = "skipped"  # Optional step skipped


@dataclass
class StepState:
    """State of a single workflow step."""

    step: WorkflowStep
    status: StepStatus = StepStatus.PENDING
    completed_at: str | None = None
    artifact_id: UUID | None = None
    error_message: str | None = None
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class WorkflowState:
    """Complete workflow state for a PPTX project."""

    project_id: UUID
    current_step: WorkflowStep = WorkflowStep.UPLOAD_TEMPLATE
    steps: dict[WorkflowStep, StepState] = field(default_factory=dict)
    validation_passed: bool = False
    can_generate: bool = False

    def __post_init__(self) -> None:
        """Initialize step states if not provided."""
        if not self.steps:
            for step in WorkflowStep:
                self.steps[step] = StepState(step=step)


# Step dependencies per ADR-0020
STEP_DEPENDENCIES: dict[WorkflowStep, list[WorkflowStep]] = {
    WorkflowStep.UPLOAD_TEMPLATE: [],
    WorkflowStep.CONFIGURE_ENV: [WorkflowStep.UPLOAD_TEMPLATE],
    WorkflowStep.UPLOAD_DATA: [WorkflowStep.CONFIGURE_ENV],
    WorkflowStep.MAP_CONTEXT: [WorkflowStep.UPLOAD_DATA],
    WorkflowStep.MAP_METRICS: [WorkflowStep.UPLOAD_DATA],
    WorkflowStep.VALIDATE: [WorkflowStep.MAP_CONTEXT, WorkflowStep.MAP_METRICS],
    WorkflowStep.GENERATE: [WorkflowStep.VALIDATE],
}

# Steps that reset downstream validation when modified
RESET_TRIGGERS: dict[WorkflowStep, list[WorkflowStep]] = {
    WorkflowStep.UPLOAD_TEMPLATE: [
        WorkflowStep.CONFIGURE_ENV,
        WorkflowStep.UPLOAD_DATA,
        WorkflowStep.MAP_CONTEXT,
        WorkflowStep.MAP_METRICS,
        WorkflowStep.VALIDATE,
    ],
    WorkflowStep.CONFIGURE_ENV: [
        WorkflowStep.UPLOAD_DATA,
        WorkflowStep.MAP_CONTEXT,
        WorkflowStep.MAP_METRICS,
        WorkflowStep.VALIDATE,
    ],
    WorkflowStep.UPLOAD_DATA: [
        WorkflowStep.MAP_CONTEXT,
        WorkflowStep.MAP_METRICS,
        WorkflowStep.VALIDATE,
    ],
    WorkflowStep.MAP_CONTEXT: [WorkflowStep.VALIDATE],
    WorkflowStep.MAP_METRICS: [WorkflowStep.VALIDATE],
}


class WorkflowValidationError(Exception):
    """Raised when workflow transition is invalid."""

    pass


class WorkflowFSM:
    """Finite State Machine for PPTX 7-step workflow.

    Per ADR-0020: Implements forward gating and reset_validation cascade.
    """

    def __init__(self, state: WorkflowState) -> None:
        """Initialize FSM with workflow state."""
        self.state = state

    def can_transition_to(self, target_step: WorkflowStep) -> bool:
        """Check if transition to target step is allowed.

        Per ADR-0020: Forward gating requires all dependencies complete.

        Args:
            target_step: Step to transition to.

        Returns:
            True if transition is allowed.
        """
        dependencies = STEP_DEPENDENCIES.get(target_step, [])
        for dep in dependencies:
            dep_state = self.state.steps.get(dep)
            if not dep_state or dep_state.status != StepStatus.COMPLETED:
                return False
        return True

    def get_blocking_dependencies(self, target_step: WorkflowStep) -> list[WorkflowStep]:
        """Get list of incomplete dependencies blocking a step.

        Args:
            target_step: Step to check.

        Returns:
            List of incomplete dependency steps.
        """
        blocking = []
        dependencies = STEP_DEPENDENCIES.get(target_step, [])
        for dep in dependencies:
            dep_state = self.state.steps.get(dep)
            if not dep_state or dep_state.status != StepStatus.COMPLETED:
                blocking.append(dep)
        return blocking

    def complete_step(
        self,
        step: WorkflowStep,
        artifact_id: UUID | None = None,
    ) -> None:
        """Mark a step as completed.

        Args:
            step: Step to complete.
            artifact_id: Optional artifact ID produced by the step.

        Raises:
            WorkflowValidationError: If step cannot be completed.
        """
        if not self.can_transition_to(step):
            blocking = self.get_blocking_dependencies(step)
            raise WorkflowValidationError(
                f"Cannot complete {step.value}: dependencies incomplete: "
                f"{[b.value for b in blocking]}"
            )

        from datetime import datetime

        step_state = self.state.steps[step]
        step_state.status = StepStatus.COMPLETED
        step_state.completed_at = datetime.now(UTC).isoformat()
        step_state.artifact_id = artifact_id
        step_state.error_message = None
        step_state.validation_errors = []

        # Update current step to next pending
        self._advance_current_step()

        # Update can_generate flag
        self._update_can_generate()

    def modify_step(self, step: WorkflowStep) -> list[WorkflowStep]:
        """Handle modification of a completed step (reset downstream).

        Per ADR-0020: Cascade policy is 'reset_validation' - changes reset
        downstream validation status.

        Args:
            step: Step being modified.

        Returns:
            List of steps that were reset.
        """
        reset_steps = RESET_TRIGGERS.get(step, [])
        for reset_step in reset_steps:
            step_state = self.state.steps.get(reset_step)
            if step_state and step_state.status == StepStatus.COMPLETED:
                step_state.status = StepStatus.PENDING
                step_state.completed_at = None
                step_state.validation_errors = []

        # Validation is no longer passed
        self.state.validation_passed = False
        self._update_can_generate()

        return reset_steps

    def fail_step(self, step: WorkflowStep, error_message: str) -> None:
        """Mark a step as failed with validation errors.

        Args:
            step: Step that failed.
            error_message: Error message.
        """
        step_state = self.state.steps[step]
        step_state.status = StepStatus.INVALID
        step_state.error_message = error_message
        step_state.validation_errors.append(error_message)

        if step == WorkflowStep.VALIDATE:
            self.state.validation_passed = False

        self._update_can_generate()

    def pass_validation(self, validation_results: list[str] | None = None) -> None:
        """Mark validation step as passed ('Four Green Bars').

        Per ADR-0020: Generate requires validation to pass.

        Args:
            validation_results: Optional list of validation warnings (not errors).
        """
        if not self.can_transition_to(WorkflowStep.VALIDATE):
            blocking = self.get_blocking_dependencies(WorkflowStep.VALIDATE)
            raise WorkflowValidationError(
                f"Cannot validate: dependencies incomplete: {[b.value for b in blocking]}"
            )

        self.complete_step(WorkflowStep.VALIDATE)
        self.state.validation_passed = True
        self._update_can_generate()

    def can_generate(self) -> bool:
        """Check if Generate step is allowed.

        Per ADR-0020: Generate MUST be disabled until Step 6 passes.

        Returns:
            True if generation is allowed.
        """
        return (
            self.state.validation_passed
            and self.can_transition_to(WorkflowStep.GENERATE)
        )

    def get_step_status(self, step: WorkflowStep) -> StepState:
        """Get the status of a specific step."""
        return self.state.steps[step]

    def get_workflow_summary(self) -> dict[str, Any]:
        """Get summary of workflow state for API response."""
        return {
            "project_id": str(self.state.project_id),
            "current_step": self.state.current_step.value,
            "validation_passed": self.state.validation_passed,
            "can_generate": self.can_generate(),
            "steps": {
                step.value: {
                    "status": state.status.value,
                    "completed_at": state.completed_at,
                    "can_proceed": self.can_transition_to(step),
                }
                for step, state in self.state.steps.items()
            },
        }

    def _advance_current_step(self) -> None:
        """Advance current_step to next pending step."""
        step_order = list(WorkflowStep)
        for step in step_order:
            state = self.state.steps.get(step)
            if state and state.status == StepStatus.PENDING:
                self.state.current_step = step
                return
        # All steps complete
        self.state.current_step = WorkflowStep.GENERATE

    def _update_can_generate(self) -> None:
        """Update the can_generate flag based on current state."""
        self.state.can_generate = self.can_generate()


def create_workflow_state(project_id: UUID) -> WorkflowState:
    """Create a new workflow state for a project.

    Args:
        project_id: Project UUID.

    Returns:
        Initialized WorkflowState.
    """
    return WorkflowState(project_id=project_id)


def check_generate_allowed(state: WorkflowState) -> tuple[bool, str | None]:
    """Check if generation is allowed per ADR-0020.

    Args:
        state: Current workflow state.

    Returns:
        Tuple of (allowed, error_message).
    """
    fsm = WorkflowFSM(state)

    if not state.validation_passed:
        return False, "Generation requires validation to pass ('Four Green Bars')"

    if not fsm.can_transition_to(WorkflowStep.GENERATE):
        blocking = fsm.get_blocking_dependencies(WorkflowStep.GENERATE)
        return False, f"Incomplete steps: {[b.value for b in blocking]}"

    return True, None
