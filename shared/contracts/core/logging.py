"""Logging contracts - structured logging and tracing models.

Per ADR-0037: Observability & Debugging First.
Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).

These contracts define the structure of log events, request contexts,
and state snapshots for debugging and observability.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.001"


class LogLevel(str, Enum):
    """Standard log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RequestContext(BaseModel):
    """Context for a single API request, propagated through call chain.

    Per ADR-0037: All requests must have request_id for traceability.
    """

    request_id: str = Field(
        ...,
        description="Unique ID for this request (UUID v4 or X-Request-ID header)",
    )
    user_id: str | None = Field(
        None,
        description="User ID if authenticated",
    )
    tool: str | None = Field(
        None,
        description="Tool context (dat, sov, pptx)",
    )
    operation: str | None = Field(
        None,
        description="High-level operation being performed",
    )
    started_at: datetime = Field(
        ...,
        description="When this request started (ISO-8601 UTC)",
    )
    parent_request_id: str | None = Field(
        None,
        description="Parent request ID for nested/chained calls",
    )


class LogEvent(BaseModel):
    """Structured log event for JSON logging.

    Per ADR-0037: All logs must be structured JSON via structlog.
    """

    timestamp: datetime = Field(
        ...,
        description="When this event occurred (ISO-8601 UTC)",
    )
    level: LogLevel = Field(
        ...,
        description="Log level",
    )
    event: str = Field(
        ...,
        description="Event name/message",
    )
    request_id: str | None = Field(
        None,
        description="Request ID for correlation",
    )
    module: str | None = Field(
        None,
        description="Source module name",
    )
    function: str | None = Field(
        None,
        description="Source function name",
    )
    duration_ms: float | None = Field(
        None,
        description="Duration in milliseconds (for timed operations)",
    )
    context: dict[str, Any] | None = Field(
        None,
        description="Additional context fields",
    )
    error_type: str | None = Field(
        None,
        description="Exception type if this is an error log",
    )
    error_message: str | None = Field(
        None,
        description="Exception message if this is an error log",
    )
    stack_trace: str | None = Field(
        None,
        description="Stack trace if this is an error log",
    )


class StateSnapshot(BaseModel):
    """Snapshot of FSM state for debugging.

    Per ADR-0037: FSM transitions must emit state snapshots at DEBUG level.
    """

    snapshot_id: str = Field(
        ...,
        description="Unique ID for this snapshot",
    )
    request_id: str = Field(
        ...,
        description="Request ID that triggered this state change",
    )
    timestamp: datetime = Field(
        ...,
        description="When this snapshot was taken (ISO-8601 UTC)",
    )
    stage_id: str = Field(
        ...,
        description="Stage ID (e.g., 'dat:selection', 'sov:analyze')",
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
        description="What triggered this transition (e.g., 'user_action', 'api_call')",
    )
    state_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Full state data serialized as JSON",
    )
    artifacts_affected: list[str] = Field(
        default_factory=list,
        description="Artifact IDs affected by this state change",
    )


class FSMTransitionLog(BaseModel):
    """Log entry for FSM state transitions.

    Per ADR-0037: FSM transitions must emit structured log events.
    """

    request_id: str
    stage_id: str
    from_state: str | None
    to_state: str
    trigger: str
    duration_ms: float | None = None
    artifacts_created: list[str] = Field(default_factory=list)
    cascade_triggered: bool = False
    affected_stages: list[str] = Field(default_factory=list)


class ArtifactLog(BaseModel):
    """Log entry for artifact operations.

    Per ADR-0037: ArtifactStore writes must log artifact_id and content_hash.
    """

    request_id: str
    artifact_id: str
    operation: str = Field(
        ...,
        description="'write', 'read', 'delete', 'lock', 'unlock'",
    )
    content_hash: str | None = Field(
        None,
        description="SHA-256 hash of content (for writes)",
    )
    file_path: str | None = Field(
        None,
        description="Relative file path",
    )
    size_bytes: int | None = Field(
        None,
        description="Size in bytes (for writes)",
    )
    timestamp: datetime = Field(
        ...,
        description="When this operation occurred",
    )


class TraceQuery(BaseModel):
    """Query parameters for trace viewer."""

    request_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    level: LogLevel | None = None
    stage_id: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class TraceResult(BaseModel):
    """Result from trace query."""

    events: list[LogEvent]
    state_snapshots: list[StateSnapshot]
    total_count: int
    has_more: bool
