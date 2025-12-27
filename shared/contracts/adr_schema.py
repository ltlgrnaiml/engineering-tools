from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProvenanceEntry(BaseModel):
    at: str = Field(..., description="Date in YYYY-MM-DD format")
    by: str = Field(..., description="Who made the change")
    note: str = Field(..., description="Description of the change")


class AlternativeConsidered(BaseModel):
    name: str = Field(..., description="Name of the alternative")
    pros: str = Field(..., description="Advantages of this alternative")
    cons: str = Field(..., description="Disadvantages of this alternative")
    rejected_reason: str = Field(..., description="Why this was rejected")


class Guardrail(BaseModel):
    rule: str = Field(..., description="The rule to be enforced")
    enforcement: str = Field(..., description="How the rule is enforced")
    scope: str = Field(..., description="Where this guardrail applies")
    id: str = Field(..., description="Unique identifier for this guardrail")


class DecisionDetails(BaseModel):
    approach: str | None = Field(None, description="High-level approach description")
    constraints: list[str] = Field(default_factory=list, description="Technical constraints")
    implementation_specs: list[str] = Field(
        default_factory=list, description="Related spec documents"
    )
    migration_strategy: str | None = Field(None, description="Migration approach if applicable")
    rollback_plan: str | None = Field(None, description="Rollback strategy if needed")


class ADRSchema(BaseModel):
    schema_type: Literal["adr"] = Field(default="adr", description="Schema type identifier")
    id: str = Field(..., description="Unique ADR identifier (e.g., ADR-0001_Short-Title)")
    title: str = Field(..., min_length=10, description="Descriptive title for the ADR")
    status: Literal["proposed", "accepted", "deprecated", "superseded"] = Field(
        ..., description="Current status of the ADR"
    )
    date: str = Field(..., description="Date created in YYYY-MM-DD format")
    review_date: str | None = Field(None, description="Next review date in YYYY-MM-DD format")
    deciders: str = Field(..., description="Who made or approved this decision")
    scope: str = Field(
        ...,
        description="Scope of impact (e.g., core, subsystem:DAT, subsystem:PPTX, subsystem:SOV)",
    )
    provenance: list[ProvenanceEntry] = Field(
        default_factory=list, description="History of changes to this ADR"
    )
    context: str = Field(
        ..., min_length=50, description="Background and problem statement (minimum 50 chars)"
    )
    decision_primary: str = Field(
        ..., min_length=50, description="The primary decision made (minimum 50 chars)"
    )
    decision_details: DecisionDetails = Field(
        default_factory=DecisionDetails, description="Detailed decision breakdown"
    )
    consequences: list[str] = Field(default_factory=list, description="Known consequences")
    alternatives_considered: list[AlternativeConsidered] = Field(
        default_factory=list, description="Other options that were evaluated"
    )
    tradeoffs: str | None = Field(None, description="Key tradeoffs made in this decision")
    guardrails: list[Guardrail] = Field(
        default_factory=list, description="Specific guardrails introduced by this ADR"
    )
    cross_cutting_guardrails: list[str] = Field(
        default_factory=list, description="References to guardrails from other ADRs"
    )
    references: list[str] = Field(
        default_factory=list, description="Related files, documents, or resources"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    affected_components: list[str] = Field(
        default_factory=list, description="Components impacted by this decision"
    )

    @field_validator("date", "review_date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            parts = v.split("-")
            if len(parts) != 3:
                raise ValueError("Date must be in YYYY-MM-DD format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)
            return v
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v.startswith("ADR-"):
            raise ValueError("ADR ID must start with 'ADR-'")
        parts = v.split("_", 1)
        if len(parts) != 2:
            raise ValueError("ADR ID must follow format: ADR-NNNN_Short-Title")
        return v

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


class ADRCreateRequest(BaseModel):
    folder: str = Field(..., description="Target folder (core, shared, dat, pptx, sov, devtools)")
    adr_data: dict[str, Any] = Field(..., description="ADR data to create")


class ADRFieldValidationRequest(BaseModel):
    field_name: str = Field(..., description="Name of the field to validate")
    field_value: Any = Field(..., description="Value to validate")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Other fields for context-aware validation"
    )


class ADRFieldValidationResponse(BaseModel):
    valid: bool
    error: str | None = None
