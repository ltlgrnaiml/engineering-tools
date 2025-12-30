"""DevTools API contracts.

Per ADR-0028: DevTools Page Architecture.

This module defines the contracts for the DevTools API endpoints
including ADR management, config editing, and developer utilities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


# =============================================================================
# DevTools Feature Flags
# =============================================================================


class DevToolsState(BaseModel):
    """Current state of DevTools visibility and features."""

    enabled: bool = Field(
        False,
        description="Whether DevTools is currently enabled",
    )
    enabled_via: Literal["url_param", "localStorage", "debug_panel"] | None = Field(
        None,
        description="How DevTools was enabled",
    )
    enabled_at: datetime | None = None


class DevToolsToggleRequest(BaseModel):
    """Request to toggle DevTools state."""

    enabled: bool
    persist: bool = Field(
        True,
        description="Whether to persist state to localStorage",
    )


class DevToolsToggleResponse(BaseModel):
    """Response after toggling DevTools state."""

    state: DevToolsState
    message: str


# =============================================================================
# ADR Management
# =============================================================================


class ADRScope(str, Enum):
    """Valid ADR scopes matching .adrs/ folder structure."""

    CORE = "core"
    DAT = "dat"
    PPTX = "pptx"
    SOV = "sov"
    SHARED = "shared"
    DEVTOOLS = "devtools"


class ADRStatus(str, Enum):
    """Valid ADR statuses."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class ADRListItem(BaseModel):
    """Summary of an ADR for list views."""

    id: str = Field(..., description="ADR ID (e.g., ADR-0001)")
    title: str
    status: ADRStatus
    scope: ADRScope
    date: str = Field(..., description="ISO-8601 date string")
    file_path: str = Field(..., description="Relative path to ADR file")


class ADRListResponse(BaseModel):
    """Response containing list of ADRs."""

    adrs: list[ADRListItem]
    total: int
    scopes: list[ADRScope] = Field(
        default_factory=list,
        description="Unique scopes in the result set",
    )


class ADRContent(BaseModel):
    """Full ADR content for reading/editing."""

    id: str
    title: str
    status: ADRStatus
    scope: ADRScope
    date: str
    content: dict[str, Any] = Field(
        ...,
        description="Full ADR JSON content",
    )
    file_path: str


class ADRReadResponse(BaseModel):
    """Response when reading a single ADR."""

    adr: ADRContent
    raw_json: str = Field(
        ...,
        description="Raw JSON string for editor",
    )


class ADRSaveRequest(BaseModel):
    """Request to save/update an ADR."""

    file_path: str = Field(..., description="Relative path to save ADR")
    content: dict[str, Any] = Field(..., description="ADR content as dict")
    create_backup: bool = Field(
        True,
        description="Whether to backup existing file before overwriting",
    )


class ADRSaveResponse(BaseModel):
    """Response after saving an ADR."""

    success: bool
    file_path: str
    backup_path: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    message: str


class ADRDeleteRequest(BaseModel):
    """Request to delete an ADR (moves to backup)."""

    file_path: str
    permanent: bool = Field(
        False,
        description="If True, permanently delete (not recommended)",
    )


class ADRDeleteResponse(BaseModel):
    """Response after deleting an ADR."""

    success: bool
    backup_path: str | None = Field(
        None,
        description="Path where deleted ADR was backed up",
    )
    message: str


class ADRValidationRequest(BaseModel):
    """Request to validate ADR JSON content."""

    content: dict[str, Any]


class ADRValidationResponse(BaseModel):
    """Response from ADR validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# Config File Management
# =============================================================================


class ConfigFileType(str, Enum):
    """Types of configuration files that can be edited."""

    DOMAIN_CONFIG = "domain_config"
    PROFILE = "profile"
    MESSAGE_CATALOG = "message_catalog"


class ConfigFileInfo(BaseModel):
    """Information about a configuration file."""

    file_type: ConfigFileType
    file_path: str
    name: str
    description: str | None = None
    last_modified: datetime | None = None
    size_bytes: int | None = None


class ConfigFileListResponse(BaseModel):
    """Response listing available config files."""

    files: list[ConfigFileInfo]
    total: int


class ConfigFileReadResponse(BaseModel):
    """Response when reading a config file."""

    file_info: ConfigFileInfo
    content: str = Field(..., description="Raw file content")
    format: Literal["yaml", "json"] = "yaml"


class ConfigFileSaveRequest(BaseModel):
    """Request to save a config file."""

    file_path: str
    content: str
    create_backup: bool = True


class ConfigFileSaveResponse(BaseModel):
    """Response after saving a config file."""

    success: bool
    file_path: str
    backup_path: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    message: str


# =============================================================================
# Schema Validation Utility
# =============================================================================


class SchemaValidationRequest(BaseModel):
    """Request to validate data against a Pydantic schema."""

    schema_name: str = Field(
        ...,
        description="Name of the Pydantic model (e.g., 'DataSetManifest')",
    )
    data: dict[str, Any] = Field(..., description="Data to validate")


class SchemaValidationResponse(BaseModel):
    """Response from schema validation."""

    valid: bool
    schema_name: str
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Pydantic validation errors",
    )
    validated_data: dict[str, Any] | None = Field(
        None,
        description="Validated/coerced data if valid",
    )


# =============================================================================
# API Tester Utility
# =============================================================================


class APITestRequest(BaseModel):
    """Request to test an API endpoint."""

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    path: str = Field(..., description="API path (e.g., /api/datasets)")
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    timeout_seconds: float = Field(30.0, ge=1.0, le=300.0)


class APITestResponse(BaseModel):
    """Response from API test."""

    success: bool
    status_code: int
    headers: dict[str, str]
    body: Any
    duration_ms: float
    error: str | None = None


# =============================================================================
# DevTools Health/Info
# =============================================================================


class DevToolsInfo(BaseModel):
    """Information about DevTools capabilities."""

    version: str = __version__
    utilities: list[str] = Field(
        default=[
            "adr_reader_editor",
            "config_editor",
            "schema_validator",
            "api_tester",
        ],
    )
    adr_count: int = 0
    config_count: int = 0
    schemas_available: list[str] = Field(default_factory=list)
