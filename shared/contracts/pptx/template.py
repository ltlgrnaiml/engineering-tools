"""PPTX Template contracts - slide deck templates and configuration.

Per ADR-0019: Templates are discoverable, version-controlled configurations.
Per ADR-0020: Guided workflow for template configuration.
Per ADR-0021: Domain configuration separates domain knowledge from code.
Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).

A PPTXTemplate defines:
- Slide layouts and their shapes
- Data binding placeholders
- Rendering configuration

Templates are domain-agnostic containers; the actual domain knowledge
(what data goes where) is captured in the template configuration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


class TemplateStatus(str, Enum):
    """Status of a PPTX template."""

    DRAFT = "draft"  # Being configured
    VALIDATING = "validating"  # Validation in progress
    VALID = "valid"  # Ready for use
    INVALID = "invalid"  # Validation failed
    DEPRECATED = "deprecated"  # No longer recommended
    ARCHIVED = "archived"  # No longer available


class SlideLayoutType(str, Enum):
    """Standard slide layout types."""

    TITLE = "title"
    TITLE_AND_CONTENT = "title_and_content"
    SECTION_HEADER = "section_header"
    TWO_CONTENT = "two_content"
    COMPARISON = "comparison"
    CONTENT_WITH_CAPTION = "content_with_caption"
    PICTURE_WITH_CAPTION = "picture_with_caption"
    BLANK = "blank"
    CUSTOM = "custom"


class SlideLayout(BaseModel):
    """Layout definition for a slide type.

    Captures the structure of a slide layout including available
    placeholders and their positions.
    """

    layout_name: str = Field(..., description="Layout name in the template")
    layout_type: SlideLayoutType = SlideLayoutType.CUSTOM
    layout_index: int = Field(..., ge=0, description="Index in slide master")

    # Placeholders discovered in this layout
    placeholder_count: int = Field(0, ge=0)
    placeholder_names: list[str] = Field(default_factory=list)

    # Layout properties
    width_emu: int | None = Field(None, description="Width in EMUs")
    height_emu: int | None = Field(None, description="Height in EMUs")

    # Description
    description: str | None = None
    preview_image_path: str | None = Field(
        None,
        description="Relative path to layout preview image",
    )


class SlideTemplate(BaseModel):
    """Template configuration for a single slide.

    Defines which layout to use and how data binds to placeholders.
    """

    slide_index: int = Field(..., ge=0, description="Position in output deck")
    layout_name: str = Field(..., description="Layout to use from template")
    slide_title: str | None = Field(None, description="Override title text")

    # Conditional rendering
    condition: str | None = Field(
        None,
        description="Expression to evaluate (slide included if truthy)",
    )
    repeat_for: str | None = Field(
        None,
        description="DataSet column to iterate (creates multiple slides)",
    )
    repeat_group_by: list[str] | None = Field(
        None,
        description="Group repeat iterations by these columns",
    )

    # Shape bindings (configured via guided workflow)
    bindings: list["ShapeBindingRef"] = Field(
        default_factory=list,
        description="References to shape bindings for this slide",
    )

    # Metadata
    notes: str | None = Field(None, description="Speaker notes template")
    tags: list[str] = Field(default_factory=list)


class ShapeBindingRef(BaseModel):
    """Reference to a shape binding configuration."""

    placeholder_name: str = Field(..., description="Shape placeholder to bind")
    binding_id: str = Field(..., description="ID of the binding configuration")


class PPTXTemplate(BaseModel):
    """Complete PPTX template definition.

    This is the top-level contract for template configuration.
    Per ADR-0019: Templates are discoverable and version-controlled.
    """

    # Identity
    template_id: str = Field(
        ...,
        description="Deterministic hash of template content",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    version: str = Field("1.0.0", description="Template version (semver)")

    # Status
    status: TemplateStatus = TemplateStatus.DRAFT

    # Timestamps (per ADR-0009)
    created_at: datetime
    updated_at: datetime | None = None
    validated_at: datetime | None = None

    # Source template file
    source_path: str = Field(
        ...,
        description="Relative path to .pptx template file",
    )
    source_hash: str | None = Field(
        None,
        description="SHA-256 hash of source file (for drift detection)",
    )

    # Discovered layouts
    layouts: list[SlideLayout] = Field(
        default_factory=list,
        description="Layouts discovered from source template",
    )

    # Slide configuration
    slides: list[SlideTemplate] = Field(
        default_factory=list,
        description="Configured slides for output deck",
    )

    # Output configuration
    output_filename_pattern: str = Field(
        "{name}_{date}.pptx",
        description="Pattern for output filename",
    )
    include_notes: bool = Field(True, description="Include speaker notes")
    include_hidden_slides: bool = Field(False, description="Include hidden slides")

    # Data sources
    required_datasets: list[str] = Field(
        default_factory=list,
        description="Dataset IDs required as input",
    )
    optional_datasets: list[str] = Field(
        default_factory=list,
        description="Optional dataset IDs",
    )

    # Metadata
    domain: str | None = Field(
        None,
        description="Domain identifier (e.g., 'semiconductor', 'finance')",
    )
    tags: list[str] = Field(default_factory=list)
    owner: str | None = None

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        """Ensure source path is relative and points to .pptx."""
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"Absolute paths not allowed: {v}")
        if not v.lower().endswith(".pptx"):
            raise ValueError(f"Source must be a .pptx file: {v}")
        return v


class PPTXTemplateRef(BaseModel):
    """Lightweight reference for template list responses."""

    template_id: str
    name: str
    version: str
    status: TemplateStatus
    slide_count: int
    layout_count: int
    domain: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class TemplateValidationError(BaseModel):
    """Error found during template validation."""

    error_code: str
    message: str
    slide_index: int | None = None
    placeholder_name: str | None = None
    severity: Literal["error", "warning"] = "error"


class TemplateValidationResult(BaseModel):
    """Result of validating a PPTX template."""

    template_id: str
    valid: bool
    errors: list[TemplateValidationError] = Field(default_factory=list)
    warnings: list[TemplateValidationError] = Field(default_factory=list)

    # Discovery results
    layouts_found: int = Field(0, ge=0)
    placeholders_found: int = Field(0, ge=0)
    shapes_found: int = Field(0, ge=0)

    # Binding validation
    bindings_valid: int = Field(0, ge=0)
    bindings_invalid: int = Field(0, ge=0)
    unbound_placeholders: list[str] = Field(default_factory=list)

    validation_duration_ms: float = Field(0.0, ge=0.0)


class RenderConfig(BaseModel):
    """Configuration for a render operation.

    Controls how the template is rendered with data.
    """

    # Output
    output_path: str = Field(
        ...,
        description="Relative path for output .pptx file",
    )
    overwrite_existing: bool = Field(
        False,
        description="Overwrite if file exists",
    )

    # Data filtering
    filter_expression: str | None = Field(
        None,
        description="Filter expression for input data (pandas query syntax)",
    )
    limit_rows: int | None = Field(
        None,
        ge=1,
        description="Maximum rows to process",
    )

    # Chart options
    chart_dpi: int = Field(150, ge=72, le=600)
    chart_style: str | None = None

    # Table options
    table_max_rows: int = Field(50, ge=1, le=1000)
    table_font_size: float = Field(10.0, ge=6.0, le=24.0)

    # Image options
    image_quality: int = Field(85, ge=1, le=100)
    image_max_width_px: int = Field(1920, ge=100, le=4096)

    # Determinism
    seed: int = Field(42, description="Seed for any randomized operations")

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, v: str) -> str:
        """Ensure output path is relative and has .pptx extension."""
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"Absolute paths not allowed: {v}")
        if not v.lower().endswith(".pptx"):
            raise ValueError(f"Output must be a .pptx file: {v}")
        return v


class RenderRequest(BaseModel):
    """Request to render a PPTX from template and data."""

    template_id: str = Field(..., description="Template to render")
    dataset_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Input dataset IDs",
    )
    config: RenderConfig
    job_id: str | None = Field(
        None,
        description="Parent job ID for tracking",
    )

    # Variable substitutions
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional variables for placeholder substitution",
    )


class RenderStageState(str, Enum):
    """State of the render operation."""

    PENDING = "pending"
    LOADING_DATA = "loading_data"
    RENDERING = "rendering"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SlideRenderResult(BaseModel):
    """Result of rendering a single slide."""

    slide_index: int
    layout_name: str
    success: bool
    shapes_rendered: int = Field(0, ge=0)
    shapes_failed: int = Field(0, ge=0)
    render_duration_ms: float = Field(0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)


class RenderResult(BaseModel):
    """Result of a complete render operation."""

    # Request tracking
    template_id: str
    render_id: str = Field(..., description="Unique render operation ID")
    job_id: str | None = None

    # State
    state: RenderStageState = RenderStageState.PENDING
    progress_pct: float = Field(0.0, ge=0.0, le=100.0)
    progress_message: str | None = None

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Output
    output_path: str | None = None
    output_size_bytes: int | None = Field(None, ge=0)

    # Metrics
    slides_rendered: int = Field(0, ge=0)
    slides_failed: int = Field(0, ge=0)
    total_shapes_rendered: int = Field(0, ge=0)
    render_duration_ms: float = Field(0.0, ge=0.0)

    # Per-slide results
    slide_results: list[SlideRenderResult] = Field(default_factory=list)

    # Errors
    errors: list[str] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if render completed successfully."""
        return self.state == RenderStageState.COMPLETED and self.slides_failed == 0


class CreateTemplateRequest(BaseModel):
    """Request to create a new template from a .pptx file."""

    name: str = Field(..., min_length=1, max_length=100)
    source_path: str = Field(..., description="Relative path to .pptx file")
    description: str | None = None
    domain: str | None = None
    tags: list[str] = Field(default_factory=list)
    auto_discover: bool = Field(
        True,
        description="Automatically discover layouts and shapes",
    )


class UpdateTemplateRequest(BaseModel):
    """Request to update template configuration."""

    name: str | None = None
    description: str | None = None
    slides: list[SlideTemplate] | None = None
    output_filename_pattern: str | None = None
    tags: list[str] | None = None
    bump_version: Literal["major", "minor", "patch"] = "minor"
