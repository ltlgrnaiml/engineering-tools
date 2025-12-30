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
    - L1: Standard detail with context (premium models: Opus, Sonnet, GPT-5.2)
    - L2: Enhanced detail with hints and constraints (mid-tier: Gemini Pro)
    - L3: Full procedural steps (budget models: Haiku, Flash, Grok)

    Higher levels include all information from lower levels.

    Evidence from EXP-001 (L1 vs L3 Granularity Experiment):
    - L1 produced 39% code volume variation, L3 only 19%
    - L1 had 6-value enum spread, L3 only 1-value spread
    - L3 achieved 100% architecture consistency vs 67% for L1
    - L2 should target the sweet spot: explicit constraints without full procedures
    """

    L1_STANDARD = "L1"      # Context + verification (premium models $$$$)
    L2_ENHANCED = "L2"      # + hints, constraints, negative examples (mid-tier $$)
    L3_PROCEDURAL = "L3"    # + step-by-step instructions with code snippets ($)


# =============================================================================
# Task (Fragment) Models
# =============================================================================


class TaskEvidence(BaseModel):
    """Evidence that a task was completed and verified."""

    command: str = Field(..., description="Verification command that was run")
    output: str = Field(..., description="Output from the command (truncated if long)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When verified")
    session_id: str | None = Field(None, description="Session that verified this task")


class StepType(str, Enum):
    """Type of procedural step for L3 granularity.

    Evidence from EXP-001: GPT-5.2 demonstrated value of session/question steps.
    """

    CODE = "code"              # Write or modify code
    VERIFY = "verify"          # Run verification command
    SESSION = "session"        # Create/update session file (from GPT-5.2 patterns)
    QUESTION = "question"      # Escalate blocker to .questions/ (from GPT-5.2 patterns)
    PREFLIGHT = "preflight"    # Run baseline checks before starting


class TaskStep(BaseModel):
    """A single procedural step within a task (L3 granularity).

    Used when maximum detail is needed for smaller/cheaper models.
    Each step is a single, atomic instruction that can be executed verbatim.

    Evidence from EXP-001:
    - L3 steps reduced code volume variation from 39% to 19%
    - GPT-5.2 showed value of session discipline and question escalation
    - These patterns should be baked into L3 plans for all models
    """

    step_number: int = Field(..., ge=1, description="Step sequence number")
    step_type: StepType = Field(
        default=StepType.CODE,
        description="Type of step: code, verify, session, question, preflight"
    )
    instruction: str = Field(..., description="Exactly what to do in this step")
    code_snippet: str | None = Field(
        None, description="Optional code to write/modify (copy-paste ready)"
    )
    file_path: str | None = Field(
        None,
        description="File to create or modify (CRITICAL: be explicit to avoid wrong locations)"
    )
    checkpoint: bool = Field(
        False, description="Safe to commit/save after this step?"
    )
    verification_hint: str | None = Field(
        None,
        description="Quick verification command the AI can run after this step"
    )
    on_failure_hint: str | None = Field(
        None,
        description="What to check if this step fails (e.g., 'Check __init__.py exports')"
    )
    escalate_on_failure: bool = Field(
        False,
        description="If True and step fails, create .questions/ file instead of proceeding"
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

    # --- L1: Standard (baseline for premium models) ---
    # Evidence: L1 context with prefixes (ARCHITECTURE:, FILE:, ENUM:) improved consistency
    context: list[str] = Field(
        default_factory=list,
        description="""L1: Key context using standard prefixes:
        - ARCHITECTURE: Style guidance (e.g., 'Functional style, no classes')
        - FILE: Exact file paths (e.g., 'Modify gateway/services/devtools_service.py')
        - FUNCTION: Exact signatures (e.g., 'def scan_artifacts(search: str) -> list')
        - ENUM: Exact values (e.g., 'ArtifactStatus: draft, active, deprecated, superseded, completed')
        - VERSION: Format spec (e.g., '__version__ = "2025.12.01"')
        - PARAM: Naming conventions (e.g., 'Use "search" not "search_query"')""",
    )

    # --- L2: Enhanced (for mid-tier models) ---
    # Evidence: L2 bridges L1 and L3 - adds constraints without full procedures
    hints: list[str] = Field(
        default_factory=list,
        description="L2: Implementation hints and patterns to follow",
    )
    references: list[str] = Field(
        default_factory=list,
        description="L2: File paths or docs to reference during implementation",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="""L2: Explicit constraints and negative examples:
        - DO NOT: Things to avoid (e.g., 'DO NOT use class-based architecture')
        - MUST: Hard requirements (e.g., 'MUST place tests in tests/gateway/')
        - EXACTLY: Precise values (e.g., 'EXACTLY 5 enum values, no more')""",
    )
    existing_patterns: list[str] = Field(
        default_factory=list,
        description="L2: References to existing code to match (e.g., 'Follow pattern in dataset_service.py')",
    )

    # --- L3: Procedural (for budget models) ---
    # Evidence: L3 achieved 100% architecture consistency vs 67% for L1
    steps: list[TaskStep] = Field(
        default_factory=list,
        description="L3: Step-by-step procedural instructions with code snippets for budget models",
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
# L3 Chunking Models (Progressive Chunking for Budget Models)
# =============================================================================


class ChunkStatus(str, Enum):
    """Status of a chunk's line count relative to limits."""

    OPTIMAL = "optimal"      # Under 600 lines - ideal
    WARNING = "warning"      # 600-800 lines - acceptable with note
    EXCEEDED = "exceeded"    # Over 800 lines - should have been split


class ChunkExecutionLog(BaseModel):
    """Record of which model executed a chunk.

    Fun experiment: Let models self-report their identity!
    """

    chunk_id: str = Field(..., description="Which chunk was executed")
    model_name: str | None = Field(
        None, description="Model's self-reported name (if self-aware)"
    )
    model_provider: str | None = Field(
        None, description="Provider: anthropic, openai, google, xai, etc."
    )
    session_id: str = Field(..., description="Session that executed this chunk")
    started_at: datetime = Field(..., description="When execution started")
    completed_at: datetime | None = Field(None, description="When execution finished")
    tasks_completed: int = Field(0, description="Number of tasks completed")
    escalations: int = Field(0, description="Number of .questions/ files created")


class ChunkMeta(BaseModel):
    """Metadata for a plan chunk (L3 progressive chunking).

    Evidence from EXP-001: Budget models need smaller context windows.
    Target: 600 lines, Soft limit: 800 lines.
    """

    chunk_id: str = Field(..., description="Chunk ID (e.g., M1, M1a, M2)")
    chunk_file: str = Field(..., description="Filename of this chunk")
    line_count: int = Field(..., description="Actual line count")
    target_limit: int = Field(default=600, description="Target max lines (optimal)")
    soft_limit: int = Field(default=800, description="Soft warning threshold")

    @computed_field
    @property
    def chunk_status(self) -> ChunkStatus:
        """Compute chunk status based on line count."""
        if self.line_count <= self.target_limit:
            return ChunkStatus.OPTIMAL
        elif self.line_count <= self.soft_limit:
            return ChunkStatus.WARNING
        else:
            return ChunkStatus.EXCEEDED

    warning_note: str | None = Field(
        None,
        description="If soft limit exceeded, explain why not split (C override)"
    )
    auto_split_disabled: bool = Field(
        default=False,
        description="If True, auto-split was overridden with justification"
    )


class ContinuationContext(BaseModel):
    """Context passed between chunks for session continuity.

    This is the 'handshake' that tells the next model what was established.
    """

    previous_chunk: str | None = Field(None, description="Previous chunk filename")
    last_completed_task: str | None = Field(None, description="Last task ID completed")
    files_created: list[str] = Field(
        default_factory=list, description="Files created in previous chunks"
    )
    files_modified: list[str] = Field(
        default_factory=list, description="Files modified in previous chunks"
    )
    architecture_rules: list[str] = Field(
        default_factory=list,
        description="Architecture rules established (e.g., 'STYLE: Functional, NO classes')"
    )
    patterns_established: list[str] = Field(
        default_factory=list,
        description="Code patterns to maintain (e.g., '5-value enums')"
    )
    active_blockers: list[str] = Field(
        default_factory=list, description="Unresolved blockers from previous chunks"
    )


class L3ChunkIndex(BaseModel):
    """Master index for L3 chunked plans.

    This file is ALWAYS loaded first. It tells the model which chunk to execute
    and provides continuation context.
    """

    plan_id: str = Field(..., description="Parent plan ID (e.g., PLAN-001)")
    granularity: Literal["L3"] = Field(default="L3", description="Always L3 for chunks")
    title: str = Field(..., description="Plan title")
    total_chunks: int = Field(..., description="Total number of chunks")
    chunks: list[ChunkMeta] = Field(..., description="List of all chunks")
    current_chunk: str | None = Field(
        None, description="Chunk currently being executed"
    )
    continuation_context: ContinuationContext = Field(
        default_factory=ContinuationContext,
        description="Context for the current/next chunk"
    )
    execution_history: list[ChunkExecutionLog] = Field(
        default_factory=list,
        description="Record of which models executed which chunks"
    )
    session_required: bool = Field(
        default=True,
        description="L3 requires session files (from GPT-5.2 patterns)"
    )


class L3ChunkHeader(BaseModel):
    """Header section of an L3 chunk file.

    Appears at the top of each chunk to orient the model.
    """

    chunk_meta: ChunkMeta
    continuation_from: ContinuationContext
    session_instruction: str = Field(
        default="Create SESSION_XXX_<plan>_<chunk>_<summary>.md before starting",
        description="Session creation instruction"
    )
    verification_strictness: Literal["stop_and_escalate", "log_and_continue", "retry_once"] = Field(
        default="stop_and_escalate",
        description="L3 default: stop and create .questions/ on failure"
    )


class L3ChunkFooter(BaseModel):
    """Footer section of an L3 chunk file.

    Appears at the end of each chunk for handoff to next chunk.
    """

    handoff_to_next: str | None = Field(None, description="Next chunk filename")
    files_to_preserve: list[str] = Field(
        default_factory=list, description="Files that must not be modified"
    )
    patterns_to_maintain: list[str] = Field(
        default_factory=list, description="Patterns the next chunk must follow"
    )
    checkpoint_command: str | None = Field(
        None, description="Command to verify chunk completion (e.g., pytest)"
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
