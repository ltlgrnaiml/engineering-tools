"""Fragment (T5) contracts for AI Development Workflow.

Per ADR-0043: A Fragment is a single verifiable unit of work (T5 tier).
Fragments are the atomic execution units within Plans (T4).

Key characteristics:
- One task from a Plan milestone
- Has verification command and expected output
- Tracks status through lifecycle
- Captures evidence of completion
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class FragmentStatus(str, Enum):
    """Fragment execution lifecycle status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class VerificationResult(BaseModel):
    """Result of a fragment verification command."""

    command: str = Field(..., description="The verification command that was run")
    exit_code: int = Field(..., description="Exit code of the command")
    output: str = Field(default="", description="Command output (truncated if large)")
    passed: bool = Field(..., description="Whether verification passed")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When verification was run",
    )


class Fragment(BaseModel):
    """A single verifiable unit of work (T5 tier artifact).

    Fragments represent atomic tasks within Plan milestones that can be
    independently executed and verified.
    """

    id: str = Field(..., description="Fragment ID (e.g., T-M1-01 for Task 1 of Milestone 1)")
    plan_id: str = Field(..., description="Parent plan ID (e.g., PLAN-001)")
    milestone_id: str = Field(..., description="Parent milestone ID (e.g., M1)")
    description: str = Field(..., description="What this fragment accomplishes")
    status: FragmentStatus = Field(default=FragmentStatus.PENDING)

    # Execution context
    context: list[str] = Field(
        default_factory=list,
        description="Context items needed (file paths, function names, etc.)",
    )
    hints: list[str] = Field(
        default_factory=list,
        description="Implementation hints for the AI executor",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="DO NOT / MUST / EXACTLY rules",
    )

    # Verification
    verification_command: str | None = Field(
        default=None,
        description="Command to verify fragment completion",
    )
    verification_result: VerificationResult | None = Field(
        default=None,
        description="Result of running verification",
    )

    # Evidence
    files_changed: list[str] = Field(
        default_factory=list,
        description="Files modified during execution",
    )
    evidence: str = Field(
        default="",
        description="Captured evidence of completion (logs, output, etc.)",
    )

    # Metadata
    session_id: str | None = Field(
        default=None,
        description="Session that executed this fragment (e.g., SESSION_015)",
    )
    started_at: str | None = Field(default=None)
    completed_at: str | None = Field(default=None)
    error_message: str | None = Field(default=None, description="Error if failed/blocked")


class FragmentExecution(BaseModel):
    """Record of a fragment execution attempt."""

    fragment_id: str
    session_id: str
    executor_model: str = Field(
        ...,
        description="AI model that executed (e.g., claude-sonnet-4-20250514, gpt-4o)",
    )
    status: FragmentStatus
    verification_result: VerificationResult | None = None
    duration_seconds: float | None = None
    notes: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MilestoneFragment(BaseModel):
    """A milestone broken into fragments for L3 execution.

    This replaces the 'chunk' terminology - a MilestoneFragment is
    one milestone's worth of tasks packaged for L3 procedural execution.
    """

    plan_id: str
    milestone_id: str
    milestone_title: str
    granularity: str = Field(default="L3", description="Plan granularity level")

    # Fragment list
    fragments: list[Fragment] = Field(default_factory=list)

    # Execution tracking
    current_fragment_index: int = Field(default=0)
    continuation_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context to pass to next session",
    )

    # Acceptance criteria for the milestone
    acceptance_criteria: list[str] = Field(default_factory=list)
    verification_commands: list[str] = Field(default_factory=list)


class FragmentListResponse(BaseModel):
    """API response for listing fragments."""

    items: list[Fragment]
    total: int
    plan_id: str | None = None
    milestone_id: str | None = None
