"""Plan schema contracts for AI Development Workflow.

Per ADR-0041: AI Development Workflow Orchestration.

This module defines the Pydantic schemas for Plans (T4), including
milestones, tasks, acceptance criteria, and progress tracking.
Plans are the executable implementation artifacts that track
fragment-based development work.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_validator

__version__ = "2025.12.01"


# =============================================================================
# Enums
# =============================================================================


class PlanStatus(str, Enum):
    """Status of a plan."""

    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ABANDONED = "abandoned"


class MilestoneStatus(str, Enum):
    """Status of a milestone."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class TaskStatus(str, Enum):
    """Status of a task (fragment)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ACStatus(str, Enum):
    """Status of an acceptance criterion."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class GranularityLevel(str, Enum):
    """Plan granularity level for tiered execution.

    Allows the same plan structure to support different execution modes:
    - L1: Standard detail with context (mid-tier models, $$)
    - L2: Enhanced detail with hints and patterns (smaller models, $)
    - L3: Full procedural steps (cheapest models, $)

    Higher levels include all information from lower levels.
    """

    L1_STANDARD = "L1"      # Context + verification (baseline, $$)
    L2_ENHANCED = "L2"      # + hints, patterns, gotchas ($)
    L3_PROCEDURAL = "L3"    # + step-by-step instructions ($)


# =============================================================================
# Task (Fragment) Models
# =============================================================================


class TaskEvidence(BaseModel):
    """Evidence that a task was completed and verified."""

    command: str = Field(..., description="Verification command that was run")
    output: str = Field(..., description="Output from the command (truncated if long)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When verified")
    session_id: str | None = Field(None, description="Session that verified this task")


class TaskStep(BaseModel):
    """A single procedural step within a task (L3 granularity).

    Used when maximum detail is needed for smaller/cheaper models.
    Each step is a single, atomic instruction that can be executed verbatim.
    """

    step_number: int = Field(..., ge=1, description="Step sequence number")
    instruction: str = Field(..., description="Exactly what to do in this step")
    code_snippet: str | None = Field(
        None, description="Optional code to write/modify (copy-paste ready)"
    )
    file_path: str | None = Field(None, description="File to create or modify")
    checkpoint: bool = Field(
        False, description="Safe to commit/save after this step?"
    )


class Task(BaseModel):
    """A single executable task (fragment) within a milestone.

    Tasks are the atomic units of work in fragment-based development.
    Each task MUST have a verification command that proves completion.

    Supports tiered granularity:
    - L1 (Standard): description + context + verification_command
    - L2 (Enhanced): + hints, patterns, gotchas
    - L3 (Procedural): + steps with code snippets
    """

    id: str = Field(..., description="Task ID (e.g., T-M1-01)")
    description: str = Field(..., description="What this task accomplishes")
    verification_command: str = Field(
        ...,
        description="Command to verify task completion (grep, pytest, import check, etc.)",
    )
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    evidence: TaskEvidence | None = Field(
        None, description="Verification evidence when passed"
    )
    notes: str | None = Field(None, description="Additional notes or context")
    blocked_by: str | None = Field(None, description="What's blocking this task")

    # --- L1: Standard (baseline) ---
    context: list[str] = Field(
        default_factory=list,
        description="L1: Key context, decisions, and constraints for this task",
    )

    # --- L2: Enhanced ---
    hints: list[str] = Field(
        default_factory=list,
        description="L2: Implementation hints, patterns to follow, gotchas to avoid",
    )
    references: list[str] = Field(
        default_factory=list,
        description="L2: File paths or docs to reference during implementation",
    )

    # --- L3: Procedural ---
    steps: list[TaskStep] = Field(
        default_factory=list,
        description="L3: Step-by-step procedural instructions for smaller models",
    )

    @field_validator("id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        if not v.startswith("T-"):
            raise ValueError("Task ID must start with 'T-' (e.g., T-M1-01)")
        return v


# =============================================================================
# Acceptance Criteria Models
# =============================================================================


class AcceptanceCriterion(BaseModel):
    """An acceptance criterion for a milestone."""

    id: str = Field(..., description="AC ID (e.g., AC-M1-01)")
    description: str = Field(..., description="What must be true for this AC to pass")
    verification_command: str = Field(..., description="Command to verify this AC")
    status: ACStatus = Field(default=ACStatus.PENDING, description="Current status")
    evidence: str | None = Field(None, description="Output from verification when passed")

    @field_validator("id")
    @classmethod
    def validate_ac_id(cls, v: str) -> str:
        if not v.startswith("AC-"):
            raise ValueError("AC ID must start with 'AC-' (e.g., AC-M1-01)")
        return v


# =============================================================================
# Milestone Models
# =============================================================================


class Milestone(BaseModel):
    """A milestone containing multiple tasks and acceptance criteria.

    Milestones group related tasks and define the acceptance criteria
    that must pass before the milestone is considered complete.
    """

    id: str = Field(..., description="Milestone ID (e.g., M1)")
    name: str = Field(..., description="Short name for the milestone")
    objective: str = Field(..., description="What this milestone achieves")
    status: MilestoneStatus = Field(
        default=MilestoneStatus.PENDING, description="Current status"
    )
    deliverables: list[str] = Field(
        default_factory=list, description="Expected deliverables"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="IDs of milestones this depends on"
    )
    tasks: list[Task] = Field(default_factory=list, description="Tasks in this milestone")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list, description="ACs that must pass"
    )
    notes: str | None = Field(None, description="Additional notes")
    started_at: datetime | None = Field(None, description="When work started")
    completed_at: datetime | None = Field(None, description="When completed")

    @field_validator("id")
    @classmethod
    def validate_milestone_id(cls, v: str) -> str:
        if not v.startswith("M"):
            raise ValueError("Milestone ID must start with 'M' (e.g., M1)")
        return v

    @computed_field
    @property
    def tasks_total(self) -> int:
        """Total number of tasks in this milestone."""
        return len(self.tasks)

    @computed_field
    @property
    def tasks_completed(self) -> int:
        """Number of completed (passed) tasks."""
        return len([t for t in self.tasks if t.status == TaskStatus.PASSED])

    @computed_field
    @property
    def progress_percentage(self) -> float:
        """Completion percentage for this milestone."""
        if self.tasks_total == 0:
            return 0.0
        return round((self.tasks_completed / self.tasks_total) * 100, 1)


# =============================================================================
# Source Reference Models
# =============================================================================


class SourceReference(BaseModel):
    """Reference to a source artifact (Discussion, ADR, SPEC)."""

    type: Literal["discussion", "adr", "spec", "contract"] = Field(
        ..., description="Type of source artifact"
    )
    id: str = Field(..., description="Artifact ID (e.g., DISC-001, ADR-0043)")
    title: str = Field(..., description="Title of the artifact")


# =============================================================================
# Execution Log Models
# =============================================================================


class SessionLog(BaseModel):
    """Log entry for a work session."""

    session_id: str = Field(..., description="Session ID (e.g., SESSION_021)")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    started_at: str | None = Field(None, description="Start time (HH:MM)")
    ended_at: str | None = Field(None, description="End time (HH:MM)")
    tasks_completed: list[str] = Field(
        default_factory=list, description="Task IDs completed this session"
    )
    blockers_encountered: list[str] = Field(
        default_factory=list, description="Blockers encountered"
    )
    notes: str | None = Field(None, description="Session notes")
    next_session_focus: str | None = Field(None, description="What to work on next")


# =============================================================================
# Blocker Models
# =============================================================================


class Blocker(BaseModel):
    """A blocker preventing progress."""

    id: str = Field(..., description="Blocker ID (e.g., B-001)")
    description: str = Field(..., description="What is blocking progress")
    raised_date: str = Field(..., description="When blocker was raised (YYYY-MM-DD)")
    status: Literal["open", "resolved"] = Field(
        default="open", description="Current status"
    )
    resolution: str | None = Field(None, description="How it was resolved")
    resolved_date: str | None = Field(None, description="When resolved (YYYY-MM-DD)")
    affects_milestones: list[str] = Field(
        default_factory=list, description="Milestone IDs affected"
    )


# =============================================================================
# Global Acceptance Criteria
# =============================================================================


class GlobalAC(BaseModel):
    """Global acceptance criteria that apply to all milestones."""

    id: str = Field(..., description="AC ID (e.g., AC-GLOBAL-01)")
    description: str = Field(..., description="What must be true")
    verification_command: str = Field(..., description="Command to verify")


# =============================================================================
# Handoff Notes
# =============================================================================


class HandoffNotes(BaseModel):
    """Handoff notes for the next session."""

    current_state: str = Field(..., description="Brief description of current state")
    immediate_next_steps: list[str] = Field(
        default_factory=list, description="What to do next"
    )
    known_issues: list[str] = Field(default_factory=list, description="Known issues")
    files_modified: list[str] = Field(
        default_factory=list, description="Files modified in last session"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="When last updated"
    )


# =============================================================================
# Progress Summary
# =============================================================================


class ProgressSummary(BaseModel):
    """Computed progress summary for the plan."""

    total_milestones: int = Field(0, description="Total milestones")
    completed_milestones: int = Field(0, description="Completed milestones")
    total_tasks: int = Field(0, description="Total tasks across all milestones")
    completed_tasks: int = Field(0, description="Completed tasks")
    blocked_tasks: int = Field(0, description="Blocked tasks")
    percentage: float = Field(0.0, description="Overall completion percentage")


# =============================================================================
# Main Plan Schema
# =============================================================================


class PlanSchema(BaseModel):
    """Schema for implementation plans (T4 artifacts).

    Plans are the executable implementation artifacts that track
    fragment-based development work. They contain milestones, tasks,
    acceptance criteria, and progress tracking.

    Per ADR-0041: Plans are created from SPECs and executed via fragments.
    """

    schema_type: Literal["plan"] = Field(default="plan", description="Schema type")
    id: str = Field(..., description="Plan ID (e.g., PLAN-001)")
    title: str = Field(..., min_length=10, description="Descriptive title")
    version: str = Field(default=__version__, description="Schema version")
    status: PlanStatus = Field(default=PlanStatus.DRAFT, description="Current status")
    granularity: GranularityLevel = Field(
        default=GranularityLevel.L1_STANDARD,
        description="Plan detail level: L1 (standard $$), L2 (enhanced $), L3 (procedural $)",
    )
    created_date: str = Field(..., description="Creation date (YYYY-MM-DD)")
    updated_date: str = Field(..., description="Last update date (YYYY-MM-DD)")
    author: str = Field(..., description="Author or creator")

    # Summary
    summary: str = Field(..., description="One paragraph describing what this plan implements")
    objective: str = Field(..., description="Clear statement of what success looks like")

    # Source references
    source_references: list[SourceReference] = Field(
        default_factory=list, description="Source artifacts this plan implements"
    )

    # Prerequisites
    prerequisites: list[str] = Field(
        default_factory=list, description="Prerequisites that must be met before starting"
    )

    # Milestones (the core of the plan)
    milestones: list[Milestone] = Field(
        default_factory=list, description="Milestones containing tasks"
    )

    # Global acceptance criteria
    global_acceptance_criteria: list[GlobalAC] = Field(
        default_factory=list, description="ACs that apply to all milestones"
    )

    # Execution tracking
    execution_log: list[SessionLog] = Field(
        default_factory=list, description="Session logs"
    )
    blockers: list[Blocker] = Field(default_factory=list, description="Current blockers")
    lessons_learned: list[str] = Field(
        default_factory=list, description="Insights captured during execution"
    )
    handoff_notes: HandoffNotes | None = Field(
        None, description="Notes for the next session"
    )

    @field_validator("id")
    @classmethod
    def validate_plan_id(cls, v: str) -> str:
        if not v.startswith("PLAN-"):
            raise ValueError("Plan ID must start with 'PLAN-' (e.g., PLAN-001)")
        return v

    @field_validator("created_date", "updated_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            parts = v.split("-")
            if len(parts) != 3:
                raise ValueError("Date must be in YYYY-MM-DD format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)
            return v
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")

    @computed_field
    @property
    def progress(self) -> ProgressSummary:
        """Computed progress summary."""
        total_tasks = sum(len(m.tasks) for m in self.milestones)
        completed_tasks = sum(
            len([t for t in m.tasks if t.status == TaskStatus.PASSED])
            for m in self.milestones
        )
        blocked_tasks = sum(
            len([t for t in m.tasks if t.status == TaskStatus.FAILED])
            for m in self.milestones
        )
        completed_milestones = len(
            [m for m in self.milestones if m.status == MilestoneStatus.COMPLETED]
        )

        percentage = 0.0
        if total_tasks > 0:
            percentage = round((completed_tasks / total_tasks) * 100, 1)

        return ProgressSummary(
            total_milestones=len(self.milestones),
            completed_milestones=completed_milestones,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            blocked_tasks=blocked_tasks,
            percentage=percentage,
        )

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


# =============================================================================
# API Request/Response Models
# =============================================================================


class PlanCreateRequest(BaseModel):
    """Request to create a new plan."""

    title: str = Field(..., description="Plan title")
    summary: str = Field(..., description="Plan summary")
    objective: str = Field(..., description="Plan objective")
    source_references: list[SourceReference] = Field(
        default_factory=list, description="Source artifacts"
    )


class PlanCreateResponse(BaseModel):
    """Response after creating a plan."""

    plan: PlanSchema
    file_path: str = Field(..., description="Path to created plan file")


class TaskUpdateRequest(BaseModel):
    """Request to update a task status."""

    plan_id: str = Field(..., description="Plan ID")
    milestone_id: str = Field(..., description="Milestone ID")
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="New status")
    evidence: TaskEvidence | None = Field(None, description="Verification evidence")


class TaskUpdateResponse(BaseModel):
    """Response after updating a task."""

    success: bool
    task: Task
    milestone_progress: float = Field(..., description="Updated milestone progress %")
    plan_progress: float = Field(..., description="Updated plan progress %")


class PlanProgressResponse(BaseModel):
    """Response containing plan progress summary."""

    plan_id: str
    status: PlanStatus
    progress: ProgressSummary
    current_milestone: str | None = Field(None, description="Current milestone ID")
    next_task: Task | None = Field(None, description="Next task to work on")
