"""Workflow FSM tests per ADR-0019.

Tests for the 7-step guided workflow state machine.
"""

from uuid import uuid4

import pytest

from apps.pptx_generator.backend.core.workflow_fsm import (
    WorkflowFSM,
    WorkflowState,
    WorkflowStep,
    StepStatus,
    StepState,
    WorkflowValidationError,
    STEP_DEPENDENCIES,
    RESET_TRIGGERS,
    create_workflow_state,
    check_generate_allowed,
)


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_create_workflow_state(self):
        """Test creating a new workflow state."""
        project_id = uuid4()
        state = create_workflow_state(project_id)

        assert state.project_id == project_id
        assert state.current_step == WorkflowStep.UPLOAD_TEMPLATE
        assert state.validation_passed is False
        assert state.can_generate is False
        assert len(state.steps) == 7

    def test_all_steps_initialized_pending(self):
        """Test all steps are initialized as pending."""
        state = create_workflow_state(uuid4())

        for step in WorkflowStep:
            assert step in state.steps
            assert state.steps[step].status == StepStatus.PENDING


class TestWorkflowFSM:
    """Tests for WorkflowFSM class."""

    @pytest.fixture
    def fsm(self):
        """Create a fresh FSM for testing."""
        state = create_workflow_state(uuid4())
        return WorkflowFSM(state)

    def test_initial_step_has_no_dependencies(self, fsm):
        """Test first step has no dependencies per ADR-0019."""
        assert fsm.can_transition_to(WorkflowStep.UPLOAD_TEMPLATE)
        assert fsm.get_blocking_dependencies(WorkflowStep.UPLOAD_TEMPLATE) == []

    def test_second_step_requires_first(self, fsm):
        """Test configure_env requires upload_template."""
        assert not fsm.can_transition_to(WorkflowStep.CONFIGURE_ENV)
        blocking = fsm.get_blocking_dependencies(WorkflowStep.CONFIGURE_ENV)
        assert WorkflowStep.UPLOAD_TEMPLATE in blocking

    def test_complete_step_success(self, fsm):
        """Test completing a step successfully."""
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)

        step_state = fsm.get_step_status(WorkflowStep.UPLOAD_TEMPLATE)
        assert step_state.status == StepStatus.COMPLETED
        assert step_state.completed_at is not None

    def test_complete_step_with_artifact(self, fsm):
        """Test completing step with artifact ID."""
        artifact_id = uuid4()
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE, artifact_id=artifact_id)

        step_state = fsm.get_step_status(WorkflowStep.UPLOAD_TEMPLATE)
        assert step_state.artifact_id == artifact_id

    def test_cannot_complete_without_dependencies(self, fsm):
        """Test cannot complete step when dependencies are incomplete."""
        with pytest.raises(WorkflowValidationError) as exc_info:
            fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        assert "dependencies incomplete" in str(exc_info.value)

    def test_sequential_workflow(self, fsm):
        """Test completing steps 1-3 sequentially per ADR-0019."""
        # Step 1
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)
        assert fsm.can_transition_to(WorkflowStep.CONFIGURE_ENV)

        # Step 2
        fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        assert fsm.can_transition_to(WorkflowStep.UPLOAD_DATA)

        # Step 3
        fsm.complete_step(WorkflowStep.UPLOAD_DATA)
        # Steps 4 and 5 can be done in any order
        assert fsm.can_transition_to(WorkflowStep.MAP_CONTEXT)
        assert fsm.can_transition_to(WorkflowStep.MAP_METRICS)


class TestParallelSteps:
    """Tests for parallel step execution per ADR-0019."""

    @pytest.fixture
    def fsm_at_step3(self):
        """FSM with steps 1-3 complete."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)
        fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        fsm.complete_step(WorkflowStep.UPLOAD_DATA)
        return fsm

    def test_steps_4_5_parallel(self, fsm_at_step3):
        """ADR-0019: Steps 4-5 may be completed in any order after Step 3."""
        # Both should be available
        assert fsm_at_step3.can_transition_to(WorkflowStep.MAP_CONTEXT)
        assert fsm_at_step3.can_transition_to(WorkflowStep.MAP_METRICS)

        # Complete in reverse order (5 before 4)
        fsm_at_step3.complete_step(WorkflowStep.MAP_METRICS)
        assert fsm_at_step3.can_transition_to(WorkflowStep.MAP_CONTEXT)

        fsm_at_step3.complete_step(WorkflowStep.MAP_CONTEXT)
        # Now validation should be available
        assert fsm_at_step3.can_transition_to(WorkflowStep.VALIDATE)

    def test_validation_requires_both_mappings(self, fsm_at_step3):
        """ADR-0019: Step 6 requires both Steps 4 and 5 complete."""
        # Only MAP_CONTEXT done
        fsm_at_step3.complete_step(WorkflowStep.MAP_CONTEXT)
        assert not fsm_at_step3.can_transition_to(WorkflowStep.VALIDATE)

        # Now complete MAP_METRICS
        fsm_at_step3.complete_step(WorkflowStep.MAP_METRICS)
        assert fsm_at_step3.can_transition_to(WorkflowStep.VALIDATE)


class TestResetTriggers:
    """Tests for reset cascade policy per ADR-0019."""

    @pytest.fixture
    def fsm_complete(self):
        """FSM with all steps through validation complete."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)
        fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        fsm.complete_step(WorkflowStep.UPLOAD_DATA)
        fsm.complete_step(WorkflowStep.MAP_CONTEXT)
        fsm.complete_step(WorkflowStep.MAP_METRICS)
        fsm.pass_validation()
        return fsm

    def test_modify_template_resets_downstream(self, fsm_complete):
        """ADR-0019: Modifying template resets steps 2-6."""
        reset_steps = fsm_complete.modify_step(WorkflowStep.UPLOAD_TEMPLATE)

        # Should reset configure_env through validate
        assert WorkflowStep.CONFIGURE_ENV in reset_steps
        assert WorkflowStep.VALIDATE in reset_steps

        # Validation should no longer be passed
        assert not fsm_complete.state.validation_passed

    def test_modify_data_resets_mappings(self, fsm_complete):
        """ADR-0019: Modifying data upload resets mapping steps."""
        reset_steps = fsm_complete.modify_step(WorkflowStep.UPLOAD_DATA)

        assert WorkflowStep.MAP_CONTEXT in reset_steps
        assert WorkflowStep.MAP_METRICS in reset_steps
        assert WorkflowStep.VALIDATE in reset_steps

    def test_modify_mapping_resets_validation_only(self, fsm_complete):
        """ADR-0019: Modifying mapping only resets validation."""
        reset_steps = fsm_complete.modify_step(WorkflowStep.MAP_CONTEXT)

        assert WorkflowStep.VALIDATE in reset_steps
        assert len(reset_steps) == 1


class TestGenerateGating:
    """Tests for Generate step gating per ADR-0019."""

    @pytest.fixture
    def fsm_validated(self):
        """FSM with validation passed."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)
        fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        fsm.complete_step(WorkflowStep.UPLOAD_DATA)
        fsm.complete_step(WorkflowStep.MAP_CONTEXT)
        fsm.complete_step(WorkflowStep.MAP_METRICS)
        fsm.pass_validation()
        return fsm

    def test_generate_requires_validation_pass(self):
        """ADR-0019: Generate MUST be disabled until Step 6 passes."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)

        # Complete all steps except validation
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)
        fsm.complete_step(WorkflowStep.CONFIGURE_ENV)
        fsm.complete_step(WorkflowStep.UPLOAD_DATA)
        fsm.complete_step(WorkflowStep.MAP_CONTEXT)
        fsm.complete_step(WorkflowStep.MAP_METRICS)

        # Validation step completed but not passed
        fsm.complete_step(WorkflowStep.VALIDATE)

        # Still cannot generate without validation_passed = True
        assert not fsm.can_generate()

    def test_generate_allowed_after_validation(self, fsm_validated):
        """Test generate is allowed after validation passes."""
        assert fsm_validated.can_generate()
        assert fsm_validated.state.can_generate

    def test_check_generate_allowed_function(self, fsm_validated):
        """Test check_generate_allowed helper function."""
        allowed, error = check_generate_allowed(fsm_validated.state)
        assert allowed is True
        assert error is None

    def test_check_generate_blocked_without_validation(self):
        """Test check_generate_allowed returns error when validation not passed."""
        state = create_workflow_state(uuid4())
        allowed, error = check_generate_allowed(state)

        assert allowed is False
        assert "Four Green Bars" in error


class TestStepDependencies:
    """Tests for STEP_DEPENDENCIES configuration."""

    def test_upload_template_no_deps(self):
        """First step has no dependencies."""
        assert STEP_DEPENDENCIES[WorkflowStep.UPLOAD_TEMPLATE] == []

    def test_validate_requires_both_mappings(self):
        """Validate requires both mapping steps."""
        deps = STEP_DEPENDENCIES[WorkflowStep.VALIDATE]
        assert WorkflowStep.MAP_CONTEXT in deps
        assert WorkflowStep.MAP_METRICS in deps

    def test_generate_requires_validate(self):
        """Generate requires validate."""
        deps = STEP_DEPENDENCIES[WorkflowStep.GENERATE]
        assert WorkflowStep.VALIDATE in deps


class TestResetTriggerConfiguration:
    """Tests for RESET_TRIGGERS configuration."""

    def test_template_triggers_most_resets(self):
        """Upload template triggers the most downstream resets."""
        resets = RESET_TRIGGERS.get(WorkflowStep.UPLOAD_TEMPLATE, [])
        assert len(resets) >= 5

    def test_mapping_only_resets_validation(self):
        """Mapping steps only reset validation."""
        context_resets = RESET_TRIGGERS.get(WorkflowStep.MAP_CONTEXT, [])
        metrics_resets = RESET_TRIGGERS.get(WorkflowStep.MAP_METRICS, [])

        assert context_resets == [WorkflowStep.VALIDATE]
        assert metrics_resets == [WorkflowStep.VALIDATE]


class TestWorkflowSummary:
    """Tests for workflow summary generation."""

    def test_get_workflow_summary(self):
        """Test workflow summary includes all required fields."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)

        summary = fsm.get_workflow_summary()

        assert "project_id" in summary
        assert "current_step" in summary
        assert "validation_passed" in summary
        assert "can_generate" in summary
        assert "steps" in summary
        assert len(summary["steps"]) == 7

    def test_summary_step_details(self):
        """Test step details in summary."""
        state = create_workflow_state(uuid4())
        fsm = WorkflowFSM(state)
        fsm.complete_step(WorkflowStep.UPLOAD_TEMPLATE)

        summary = fsm.get_workflow_summary()
        step_info = summary["steps"]["upload_template"]

        assert step_info["status"] == "completed"
        assert step_info["completed_at"] is not None
        assert step_info["can_proceed"] is True
