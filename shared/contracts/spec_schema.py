"""SPEC schema contracts for AI Development Workflow.

Per ADR-0043: AI Development Workflow Orchestration.

This module defines the Pydantic schemas for SPECs (T2), including
requirements, acceptance criteria, API contracts, and test requirements.
SPECs define WHAT to build with detailed behavioral requirements.
"""

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "2025.12.01"


# =============================================================================
# Enums
# =============================================================================


class SPECStatus(str, Enum):
    """Status of a SPEC."""

    DRAFT = "draft"
    REVIEW = "review"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


# =============================================================================
# Requirement Models
# =============================================================================


class AcceptanceCriterion(BaseModel):
    """An acceptance criterion for a requirement."""

    criterion: str = Field(..., description="What must be true")
    verification: str | None = Field(None, description="How to verify this criterion")


class FunctionalRequirement(BaseModel):
    """A functional requirement in the SPEC."""

    id: str = Field(..., description="Requirement ID (e.g., SPEC-0003-F01)")
    category: str | None = Field(None, description="Category grouping (e.g., 'UI Layout')")
    description: str = Field(..., description="What this requirement specifies")
    acceptance_criteria: list[str | AcceptanceCriterion] = Field(
        default_factory=list, description="ACs that define done"
    )
    api_endpoint: dict[str, Any] | None = Field(
        None, description="API endpoint details if applicable"
    )
    component: str | None = Field(None, description="UI component name if applicable")
    dependencies: list[str] = Field(
        default_factory=list, description="Package dependencies"
    )

    @field_validator("id")
    @classmethod
    def validate_requirement_id(cls, v: str) -> str:
        if not v.startswith("SPEC-"):
            raise ValueError("Requirement ID must start with 'SPEC-' (e.g., SPEC-0003-F01)")
        return v


class NonFunctionalRequirement(BaseModel):
    """A non-functional requirement (performance, security, etc.)."""

    id: str = Field(..., description="Requirement ID (e.g., SPEC-0003-NF01)")
    category: str = Field(..., description="Category (Performance, Security, Accessibility, etc.)")
    description: str = Field(..., description="What this requirement specifies")
    acceptance_criteria: list[str | AcceptanceCriterion] = Field(
        default_factory=list, description="ACs that define done"
    )

    @field_validator("id")
    @classmethod
    def validate_requirement_id(cls, v: str) -> str:
        if not v.startswith("SPEC-"):
            raise ValueError("Requirement ID must start with 'SPEC-' (e.g., SPEC-0003-NF01)")
        return v


class SecurityRequirement(BaseModel):
    """A security-specific requirement."""

    id: str = Field(..., description="Requirement ID (e.g., SPEC-0003-S01)")
    description: str = Field(..., description="Security requirement")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Security ACs"
    )


class Requirements(BaseModel):
    """Container for all requirement types."""

    functional: list[FunctionalRequirement] = Field(
        default_factory=list, description="Functional requirements"
    )
    non_functional: list[NonFunctionalRequirement] = Field(
        default_factory=list, description="Non-functional requirements"
    )
    security: list[SecurityRequirement] = Field(
        default_factory=list, description="Security requirements"
    )


# =============================================================================
# API Contract Models
# =============================================================================


class APIParameter(BaseModel):
    """A parameter in an API endpoint."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: str | None = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether parameter is required")
    default: Any | None = Field(None, description="Default value")


class APIEndpoint(BaseModel):
    """An API endpoint definition."""

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        ..., description="HTTP method"
    )
    path: str = Field(..., description="API path")
    description: str | None = Field(None, description="Endpoint description")
    query_params: list[APIParameter | str] = Field(
        default_factory=list, description="Query parameters"
    )
    request: str | None = Field(None, description="Request model name")
    request_model: str | None = Field(None, description="Request model name (alias)")
    response: str | None = Field(None, description="Response model name")
    response_model: str | None = Field(None, description="Response model name (alias)")


class APIModelField(BaseModel):
    """A field in an API model."""

    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Field type")
    description: str | None = Field(None, description="Field description")
    required: bool = Field(True, description="Whether field is required")


class APIModel(BaseModel):
    """An API model definition."""

    name: str = Field(..., description="Model name")
    type: Literal["enum", "model"] = Field(default="model", description="Model type")
    description: str | None = Field(None, description="Model description")
    values: list[str] | None = Field(None, description="Enum values (if type=enum)")
    fields: list[APIModelField] | None = Field(None, description="Model fields (if type=model)")


class APIContracts(BaseModel):
    """Container for API contract definitions."""

    endpoints: list[APIEndpoint] = Field(
        default_factory=list, description="API endpoints"
    )
    models: list[APIModel | str] = Field(
        default_factory=list, description="API models"
    )


# =============================================================================
# UI Component Models
# =============================================================================


class UIComponent(BaseModel):
    """A UI component in the hierarchy."""

    name: str = Field(..., description="Component name")
    description: str | None = Field(None, description="Component description")
    children: list[str] = Field(default_factory=list, description="Child component names")


class StateField(BaseModel):
    """A field in the state management."""

    name: str = Field(..., description="State field definition (name: type)")


class StateManagement(BaseModel):
    """State management approach for UI."""

    approach: str = Field(..., description="State management approach")
    global_state: list[str] = Field(
        default_factory=list, description="Global state fields"
    )
    persistence: list[str] = Field(
        default_factory=list, description="Persistence strategy"
    )


class UIComponents(BaseModel):
    """Container for UI component definitions."""

    hierarchy: list[UIComponent] = Field(
        default_factory=list, description="Component hierarchy"
    )
    state_management: StateManagement | None = Field(
        None, description="State management approach"
    )


# =============================================================================
# Implementation Milestone Models
# =============================================================================


class ImplementationMilestone(BaseModel):
    """A milestone for implementation planning."""

    id: str = Field(..., description="Milestone ID (e.g., M1)")
    name: str = Field(..., description="Milestone name")
    tasks: list[str] = Field(default_factory=list, description="Tasks in this milestone")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="ACs for this milestone"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Dependent milestone IDs"
    )


# =============================================================================
# Test Requirements Models
# =============================================================================


class TestRequirements(BaseModel):
    """Test requirements for the SPEC."""

    unit_tests: list[str] = Field(default_factory=list, description="Unit test names")
    integration_tests: list[str] = Field(
        default_factory=list, description="Integration test names"
    )
    e2e_tests: list[str] = Field(default_factory=list, description="E2E test names")


# =============================================================================
# Dependencies Models
# =============================================================================


class PackageDependency(BaseModel):
    """A package dependency."""

    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Version constraint")
    reason: str | None = Field(None, description="Why this dependency is needed")


class Dependencies(BaseModel):
    """Package dependencies for the SPEC."""

    npm_packages: list[PackageDependency] = Field(
        default_factory=list, description="NPM packages"
    )
    python_packages: list[PackageDependency] = Field(
        default_factory=list, description="Python packages"
    )
    existing_packages: list[str] = Field(
        default_factory=list, description="Already-installed packages"
    )


# =============================================================================
# Design Tokens
# =============================================================================


class DesignTokens(BaseModel):
    """Design tokens for UI styling."""

    colors: dict[str, str] = Field(default_factory=dict, description="Color tokens")
    edge_styles: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Edge styling tokens"
    )
    spacing: dict[str, str] = Field(default_factory=dict, description="Spacing tokens")
    typography: dict[str, str] = Field(
        default_factory=dict, description="Typography tokens"
    )


# =============================================================================
# Keyboard Shortcuts
# =============================================================================


class KeyboardShortcut(BaseModel):
    """A keyboard shortcut definition."""

    shortcut: str = Field(..., description="Key combination")
    action: str = Field(..., description="Action triggered")


# =============================================================================
# Overview Models
# =============================================================================


class Overview(BaseModel):
    """SPEC overview section."""

    purpose: str = Field(..., description="Why this SPEC exists")
    scope: str = Field(..., description="What this SPEC covers")
    out_of_scope: list[str] = Field(
        default_factory=list, description="What's explicitly not covered"
    )


# =============================================================================
# Main SPEC Schema
# =============================================================================


class SPECSchema(BaseModel):
    """Schema for specification documents (T2 artifacts).

    SPECs define WHAT to build with detailed behavioral requirements,
    API contracts, UI components, and test requirements.

    Per ADR-0043: SPECs are created from ADRs and implemented via Plans.
    """

    schema_type: Literal["spec"] = Field(default="spec", description="Schema type")
    id: str = Field(..., description="SPEC ID (e.g., SPEC-0003)")
    title: str = Field(..., min_length=10, description="Descriptive title")
    version: str = Field(default=__version__, description="SPEC version")
    status: SPECStatus = Field(default=SPECStatus.DRAFT, description="Current status")
    created_date: str = Field(..., description="Creation date (YYYY-MM-DD)")
    updated_date: str = Field(..., description="Last update date (YYYY-MM-DD)")

    # References
    implements_adr: list[str] = Field(
        default_factory=list, description="ADR IDs this SPEC implements"
    )
    source_discussion: str | None = Field(
        None, description="Source discussion ID"
    )
    tier_0_contracts: list[str] = Field(
        default_factory=list, description="Tier-0 contract file paths"
    )

    # Overview
    overview: Overview | None = Field(None, description="SPEC overview")

    # Requirements
    requirements: Requirements | None = Field(None, description="All requirements")

    # API Contracts
    api_contracts: APIContracts | None = Field(None, description="API definitions")

    # UI Components (for frontend specs)
    ui_components: UIComponents | None = Field(None, description="UI component hierarchy")

    # Keyboard Shortcuts
    keyboard_shortcuts: list[KeyboardShortcut] = Field(
        default_factory=list, description="Keyboard shortcuts"
    )

    # Design Tokens
    design_tokens: DesignTokens | None = Field(None, description="Design tokens")

    # Test Requirements
    test_requirements: TestRequirements | list[str] | None = Field(
        None, description="Test requirements"
    )

    # Implementation Milestones
    implementation_milestones: list[ImplementationMilestone] = Field(
        default_factory=list, description="Implementation milestones"
    )

    # Dependencies
    dependencies: Dependencies | None = Field(None, description="Package dependencies")

    # References
    references: list[str] = Field(
        default_factory=list, description="Related files, documents, or URLs"
    )

    @field_validator("id")
    @classmethod
    def validate_spec_id(cls, v: str) -> str:
        if not v.startswith("SPEC-"):
            raise ValueError("SPEC ID must start with 'SPEC-' (e.g., SPEC-0003)")
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


class SPECCreateRequest(BaseModel):
    """Request to create a new SPEC."""

    folder: str = Field(
        ..., description="Target folder (core, dat, pptx, sov, devtools)"
    )
    title: str = Field(..., description="SPEC title")
    implements_adr: list[str] = Field(
        default_factory=list, description="ADR IDs being implemented"
    )
    overview: Overview | None = Field(None, description="SPEC overview")


class SPECCreateResponse(BaseModel):
    """Response after creating a SPEC."""

    spec: SPECSchema
    file_path: str = Field(..., description="Path to created SPEC file")


class SPECValidationRequest(BaseModel):
    """Request to validate SPEC content."""

    content: dict[str, Any]


class SPECValidationResponse(BaseModel):
    """Response from SPEC validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
