"""Frontend logging contracts - structured logging models for React/TypeScript frontends.

Per ADR-0037: Observability & Debugging First (Backend + Frontend).
Per ADR-0009: All timestamps are ISO-8601 UTC.

These contracts define the structure of frontend debug logs, API call logs,
and state transitions for tool-specific debug panels. These Python models
serve as the source of truth for TypeScript interfaces used in frontend code.

Usage:
    These contracts are used to:
    1. Generate TypeScript interfaces for frontend debug components
    2. Validate exported debug logs from frontend
    3. Ensure consistency between frontend and backend logging formats
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.001"


class FrontendLogLevel(str, Enum):
    """Log levels for frontend debug panel."""

    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"


class FrontendLogCategory(str, Enum):
    """Categories for frontend log entries."""

    API = "api"
    STATE = "state"
    RENDER = "render"
    USER = "user"
    SYSTEM = "system"


class FrontendLogEntry(BaseModel):
    """Structured log entry for frontend debug panel.

    Per ADR-0037: Frontend debug panels must log with consistent structure.

    Attributes:
        id: Unique identifier for this log entry.
        timestamp: When this log entry was created (ISO-8601 UTC).
        level: Severity level of the log.
        category: Category of the log (api, state, user action, etc.).
        message: Human-readable log message.
        details: Optional additional data for context.
        source: Optional source identifier (component, hook, etc.).
    """

    id: str = Field(
        ...,
        description="Unique identifier for this log entry",
    )
    timestamp: datetime = Field(
        ...,
        description="When this log entry was created (ISO-8601 UTC)",
    )
    level: FrontendLogLevel = Field(
        ...,
        description="Severity level of the log",
    )
    category: FrontendLogCategory = Field(
        ...,
        description="Category of the log",
    )
    message: str = Field(
        ...,
        description="Human-readable log message",
    )
    details: Any | None = Field(
        None,
        description="Optional additional data for context",
    )
    source: str | None = Field(
        None,
        description="Optional source identifier (component, hook, etc.)",
    )


class FrontendAPICall(BaseModel):
    """Log entry for frontend API calls.

    Per ADR-0037: Frontend API calls must be logged via useDebugFetch hook.

    Attributes:
        id: Unique identifier for this API call.
        timestamp: When the request was initiated (ISO-8601 UTC).
        method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        url: Request URL.
        request_body: Optional request payload.
        response_status: HTTP status code of response.
        response_body: Optional response payload.
        duration_ms: Request duration in milliseconds.
        error: Error message if request failed.
        pending: Whether request is still in flight.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this API call",
    )
    timestamp: datetime = Field(
        ...,
        description="When the request was initiated (ISO-8601 UTC)",
    )
    method: str = Field(
        ...,
        description="HTTP method (GET, POST, PUT, DELETE, PATCH)",
    )
    url: str = Field(
        ...,
        description="Request URL",
    )
    request_body: Any | None = Field(
        None,
        description="Optional request payload",
    )
    response_status: int | None = Field(
        None,
        description="HTTP status code of response",
    )
    response_body: Any | None = Field(
        None,
        description="Optional response payload",
    )
    duration_ms: float | None = Field(
        None,
        description="Request duration in milliseconds",
    )
    error: str | None = Field(
        None,
        description="Error message if request failed",
    )
    pending: bool = Field(
        default=False,
        description="Whether request is still in flight",
    )


class FrontendStateTransition(BaseModel):
    """Log entry for frontend state transitions (FSM, wizard, etc.).

    Per ADR-0037: Frontend FSM/wizard state transitions must be logged.

    Attributes:
        id: Unique identifier for this transition.
        timestamp: When the transition occurred (ISO-8601 UTC).
        from_state: Previous state (null for initial state).
        to_state: New state after transition.
        trigger: What triggered this transition (user action, API response, etc.).
        payload: Optional data associated with the transition.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this transition",
    )
    timestamp: datetime = Field(
        ...,
        description="When the transition occurred (ISO-8601 UTC)",
    )
    from_state: str | None = Field(
        None,
        description="Previous state (null for initial state)",
    )
    to_state: str = Field(
        ...,
        description="New state after transition",
    )
    trigger: str = Field(
        ...,
        description="What triggered this transition",
    )
    payload: Any | None = Field(
        None,
        description="Optional data associated with the transition",
    )


class FrontendDebugExport(BaseModel):
    """Export format for frontend debug logs.

    Per ADR-0037: Debug logs must be exportable in unified JSON format.

    This model defines the structure of exported debug sessions from
    frontend debug panels. Used for sharing debug sessions, bug reports,
    and post-mortem analysis.

    Attributes:
        exported_at: When this export was created (ISO-8601 UTC).
        tool: Tool identifier (dat, sov, pptx).
        logs: Array of general log entries.
        api_calls: Array of API call logs.
        state_transitions: Array of state transition logs.
        metadata: Optional additional metadata.
    """

    exported_at: datetime = Field(
        ...,
        description="When this export was created (ISO-8601 UTC)",
    )
    tool: str = Field(
        ...,
        description="Tool identifier (dat, sov, pptx)",
    )
    logs: list[FrontendLogEntry] = Field(
        default_factory=list,
        description="Array of general log entries",
    )
    api_calls: list[FrontendAPICall] = Field(
        default_factory=list,
        description="Array of API call logs",
    )
    state_transitions: list[FrontendStateTransition] = Field(
        default_factory=list,
        description="Array of state transition logs",
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Optional additional metadata (user agent, window size, etc.)",
    )


class DebugPanelConfig(BaseModel):
    """Configuration for frontend debug panel.

    Per ADR-0037: Debug panels must be configurable.

    Attributes:
        max_entries: Maximum number of entries to keep (default 500).
        enabled_by_default: Whether logging is enabled by default.
        panel_position: Position of the debug panel button.
        log_to_console: Whether to also log to browser console.
    """

    max_entries: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Maximum number of entries to keep",
    )
    enabled_by_default: bool = Field(
        default=True,
        description="Whether logging is enabled by default",
    )
    panel_position: str = Field(
        default="bottom-right",
        description="Position of the debug panel button",
    )
    log_to_console: bool = Field(
        default=True,
        description="Whether to also log to browser console",
    )
