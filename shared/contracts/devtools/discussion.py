"""Discussion schema contracts for AI Development Workflow.

Per ADR-0043: AI Development Workflow Orchestration.
Per DISC-002: AI-Lite Prompt Chain Workflow.

This module defines the Pydantic schemas for Discussions (T0), the entry point
for capturing design conversations that evolve into formal artifacts.
Discussions are the natural starting point for AI-assisted development.
"""

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "2025.12.01"


# =============================================================================
# Enums
# =============================================================================


class DiscussionStatus(str, Enum):
    """Status of a discussion."""

    DRAFT = "draft"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class QuestionStatus(str, Enum):
    """Status of an open question."""

    OPEN = "open"
    ANSWERED = "answered"


class DecisionStatus(str, Enum):
    """Status of a decision point."""

    PENDING = "pending"
    DECIDED = "decided"


# =============================================================================
# Requirement Models
# =============================================================================


class FunctionalRequirement(BaseModel):
    """A functional requirement captured in discussion."""

    id: str = Field(..., description="Requirement ID (e.g., FR-1)")
    description: str = Field(..., description="What this requirement specifies")
    completed: bool = Field(default=False, description="Whether requirement is addressed")

    @field_validator("id")
    @classmethod
    def validate_requirement_id(cls, v: str) -> str:
        if not v.startswith("FR-"):
            raise ValueError("Functional requirement ID must start with 'FR-'")
        return v


class NonFunctionalRequirement(BaseModel):
    """A non-functional requirement (performance, security, etc.)."""

    id: str = Field(..., description="Requirement ID (e.g., NFR-1)")
    description: str = Field(..., description="What this requirement specifies")
    completed: bool = Field(default=False, description="Whether requirement is addressed")

    @field_validator("id")
    @classmethod
    def validate_requirement_id(cls, v: str) -> str:
        if not v.startswith("NFR-"):
            raise ValueError("Non-functional requirement ID must start with 'NFR-'")
        return v


class DiscussionRequirements(BaseModel):
    """Container for requirements captured in discussion."""

    functional: list[FunctionalRequirement] = Field(
        default_factory=list, description="Functional requirements"
    )
    non_functional: list[NonFunctionalRequirement] = Field(
        default_factory=list, description="Non-functional requirements"
    )


# =============================================================================
# Constraint Model
# =============================================================================


class Constraint(BaseModel):
    """A hard constraint that cannot be violated."""

    id: str = Field(..., description="Constraint ID (e.g., C-1)")
    description: str = Field(..., description="What this constraint requires")

    @field_validator("id")
    @classmethod
    def validate_constraint_id(cls, v: str) -> str:
        if not v.startswith("C-"):
            raise ValueError("Constraint ID must start with 'C-'")
        return v


# =============================================================================
# Open Question Model
# =============================================================================


class OpenQuestion(BaseModel):
    """An open question that needs to be answered."""

    id: str = Field(..., description="Question ID (e.g., Q-1)")
    question: str = Field(..., description="The question text")
    status: QuestionStatus = Field(
        default=QuestionStatus.OPEN, description="Current status"
    )
    answer: str | None = Field(None, description="Answer if resolved")

    @field_validator("id")
    @classmethod
    def validate_question_id(cls, v: str) -> str:
        if not v.startswith("Q-"):
            raise ValueError("Question ID must start with 'Q-'")
        return v


# =============================================================================
# Option Considered Model
# =============================================================================


class OptionConsidered(BaseModel):
    """An option being considered for an architectural decision."""

    name: str = Field(..., description="Option name (e.g., 'Option A: Use REST')")
    description: str = Field(..., description="How this option works")
    pros: list[str] = Field(default_factory=list, description="Advantages")
    cons: list[str] = Field(default_factory=list, description="Disadvantages")


# =============================================================================
# Decision Point Model
# =============================================================================


class DecisionPoint(BaseModel):
    """A key decision that needs to be made."""

    id: str = Field(..., description="Decision ID (e.g., D-1)")
    description: str = Field(..., description="What decision needs to be made")
    status: DecisionStatus = Field(
        default=DecisionStatus.PENDING, description="Current status"
    )
    outcome: str | None = Field(None, description="Outcome if decided")

    @field_validator("id")
    @classmethod
    def validate_decision_id(cls, v: str) -> str:
        if not v.startswith("D-"):
            raise ValueError("Decision ID must start with 'D-'")
        return v


# =============================================================================
# Scope Definition Model
# =============================================================================


class ScopeDefinition(BaseModel):
    """What is in scope and out of scope for this work."""

    in_scope: list[str] = Field(default_factory=list, description="Items in scope")
    out_of_scope: list[str] = Field(
        default_factory=list, description="Items explicitly out of scope"
    )


# =============================================================================
# Resulting Artifact Model
# =============================================================================


class ResultingArtifact(BaseModel):
    """An artifact created from this discussion."""

    type: Literal["adr", "spec", "contract", "plan"] = Field(
        ..., description="Type of artifact"
    )
    id: str = Field(..., description="Artifact ID (e.g., ADR-0001, SPEC-0003)")
    title: str = Field(..., description="Title of the artifact")
    status: str = Field(default="draft", description="Status of the artifact")


# =============================================================================
# Conversation Log Entry Model
# =============================================================================


class ConversationLogEntry(BaseModel):
    """A log entry for a conversation session."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    session_id: str | None = Field(None, description="Session ID if applicable")
    topics_discussed: list[str] = Field(
        default_factory=list, description="Topics covered in this session"
    )
    key_insights: list[str] = Field(
        default_factory=list, description="Key insights or decisions"
    )
    action_items: list[str] = Field(
        default_factory=list, description="Action items from this session"
    )

    @field_validator("date")
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


# =============================================================================
# Context Model
# =============================================================================


class DiscussionContext(BaseModel):
    """Context for why this discussion is happening."""

    background: str = Field(..., description="Background and current state")
    trigger: str = Field(..., description="What triggered this discussion")


# =============================================================================
# Resolution Model
# =============================================================================


class DiscussionResolution(BaseModel):
    """Resolution information when discussion is resolved."""

    date: str = Field(..., description="Resolution date in YYYY-MM-DD format")
    outcome: str = Field(..., description="Summary of what was decided/created")
    next_steps: list[str] = Field(
        default_factory=list, description="Next steps after resolution"
    )

    @field_validator("date")
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


# =============================================================================
# Main Discussion Schema
# =============================================================================


class DiscussionSchema(BaseModel):
    """Schema for discussion documents (T0 artifacts).

    Discussions capture the exploratory conversation between USER and AI
    before formal artifacts are created. They are the natural entry point
    for AI-assisted development.

    Per ADR-0043: Discussions are created to capture design conversations
    and can produce ADRs, SPECs, Contracts, and Plans.
    """

    schema_type: Literal["discussion"] = Field(
        default="discussion", description="Schema type"
    )
    id: str = Field(..., description="Discussion ID (e.g., DISC-001)")
    title: str = Field(..., min_length=5, description="Descriptive title")
    version: str = Field(default=__version__, description="Schema version")
    status: DiscussionStatus = Field(
        default=DiscussionStatus.DRAFT, description="Current status"
    )
    created_date: str = Field(..., description="Creation date (YYYY-MM-DD)")
    updated_date: str = Field(..., description="Last update date (YYYY-MM-DD)")
    author: str = Field(..., description="Author or creator")
    session_id: str | None = Field(None, description="AI session ID if applicable")

    # Summary
    summary: str = Field(
        ..., description="One paragraph describing what this discussion is about"
    )

    # Context
    context: DiscussionContext | None = Field(
        None, description="Background and trigger for this discussion"
    )

    # Requirements
    requirements: DiscussionRequirements | None = Field(
        None, description="Captured requirements"
    )

    # Constraints
    constraints: list[Constraint] = Field(
        default_factory=list, description="Hard constraints"
    )

    # Open Questions
    open_questions: list[OpenQuestion] = Field(
        default_factory=list, description="Questions that need answers"
    )

    # Options Considered (for architectural decisions)
    options_considered: list[OptionConsidered] = Field(
        default_factory=list, description="Options being evaluated"
    )
    recommendation: str | None = Field(
        None, description="Recommended option and why"
    )

    # Decision Points
    decision_points: list[DecisionPoint] = Field(
        default_factory=list, description="Key decisions to make"
    )

    # Scope
    scope: ScopeDefinition | None = Field(None, description="Scope definition")

    # Resulting Artifacts
    resulting_artifacts: list[ResultingArtifact] = Field(
        default_factory=list, description="Artifacts created from this discussion"
    )

    # Conversation Log
    conversation_log: list[ConversationLogEntry] = Field(
        default_factory=list, description="Session-by-session conversation log"
    )

    # Resolution
    resolution: DiscussionResolution | None = Field(
        None, description="Resolution when discussion is resolved"
    )

    @field_validator("id")
    @classmethod
    def validate_discussion_id(cls, v: str) -> str:
        if not v.startswith("DISC-"):
            raise ValueError("Discussion ID must start with 'DISC-' (e.g., DISC-001)")
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

    model_config = {"extra": "allow", "str_strip_whitespace": True}


# =============================================================================
# API Request/Response Models
# =============================================================================


class DiscussionCreateRequest(BaseModel):
    """Request to create a new discussion."""

    title: str = Field(..., description="Discussion title")
    summary: str = Field(..., description="Initial summary")
    context: DiscussionContext | None = Field(None, description="Context")
    session_id: str | None = Field(None, description="Session ID")


class DiscussionCreateResponse(BaseModel):
    """Response after creating a discussion."""

    discussion: DiscussionSchema
    file_path: str = Field(..., description="Path to created discussion file")


class DiscussionUpdateRequest(BaseModel):
    """Request to update a discussion."""

    requirements: DiscussionRequirements | None = Field(None)
    open_questions: list[OpenQuestion] | None = Field(None)
    options_considered: list[OptionConsidered] | None = Field(None)
    decision_points: list[DecisionPoint] | None = Field(None)
    conversation_log_entry: ConversationLogEntry | None = Field(None)


class DiscussionSummaryForPrompt(BaseModel):
    """Summarized discussion content for prompt generation.

    This is a simplified view of a discussion optimized for
    inclusion in AI prompts.
    """

    id: str
    title: str
    summary: str
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    options_considered: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    decision_points: list[str] = Field(default_factory=list)

    @classmethod
    def from_discussion(cls, disc: DiscussionSchema) -> "DiscussionSummaryForPrompt":
        """Create a summary from a full discussion schema."""
        return cls(
            id=disc.id,
            title=disc.title,
            summary=disc.summary,
            functional_requirements=[
                f"{r.id}: {r.description}"
                for r in (disc.requirements.functional if disc.requirements else [])
            ],
            non_functional_requirements=[
                f"{r.id}: {r.description}"
                for r in (disc.requirements.non_functional if disc.requirements else [])
            ],
            constraints=[f"{c.id}: {c.description}" for c in disc.constraints],
            open_questions=[
                f"{q.id}: {q.question} (Status: {q.status.value})"
                for q in disc.open_questions
            ],
            options_considered=[
                {"name": o.name, "pros": o.pros, "cons": o.cons}
                for o in disc.options_considered
            ],
            recommendation=disc.recommendation,
            decision_points=[
                f"{d.id}: {d.description} (Status: {d.status.value})"
                for d in disc.decision_points
            ],
        )
