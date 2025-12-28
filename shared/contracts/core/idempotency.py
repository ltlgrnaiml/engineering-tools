"""Idempotency contracts - request deduplication and replay.

Per ADR-0032: HTTP Request Idempotency Semantics.

These contracts define the structure for idempotency keys, cached responses,
and conflict detection for retry-safe API design.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.001"


class IdempotencyStatus(str, Enum):
    """Status of an idempotency record."""

    PENDING = "pending"  # Request is being processed
    COMPLETED = "completed"  # Request completed successfully
    FAILED = "failed"  # Request failed (may be retried)


class IdempotencyKey(BaseModel):
    """Idempotency key for request deduplication.

    Per ADR-0032: POST endpoints with side effects must support idempotency keys.
    """

    key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique idempotency key (UUID v4 or client-generated string)",
    )
    client_id: str | None = Field(
        None,
        description="Optional client identifier for key namespacing",
    )


class IdempotencyRecord(BaseModel):
    """Record of an idempotent request and its response.

    Stored in cache/database for response replay.
    """

    idempotency_key: str = Field(
        ...,
        description="The idempotency key from request header",
    )
    status: IdempotencyStatus = Field(
        ...,
        description="Current status of this request",
    )
    request_hash: str = Field(
        ...,
        description="SHA-256 hash of request body (for conflict detection)",
    )
    endpoint: str = Field(
        ...,
        description="API endpoint path (e.g., '/api/dat/runs')",
    )
    method: str = Field(
        ...,
        description="HTTP method (POST, PUT, etc.)",
    )
    created_at: datetime = Field(
        ...,
        description="When this record was created (ISO-8601 UTC)",
    )
    completed_at: datetime | None = Field(
        None,
        description="When the request completed",
    )
    expires_at: datetime = Field(
        ...,
        description="When this record expires and can be removed",
    )
    response_status: int | None = Field(
        None,
        description="HTTP status code of cached response",
    )
    response_body: dict[str, Any] | None = Field(
        None,
        description="Cached response body (JSON)",
    )
    response_headers: dict[str, str] | None = Field(
        None,
        description="Cached response headers",
    )


class IdempotencyConflict(BaseModel):
    """Conflict detected when replaying idempotent request.

    Returned when same idempotency key used with different request body.
    """

    idempotency_key: str
    original_request_hash: str
    new_request_hash: str
    message: str = Field(
        default="Idempotency key already used with different request body",
    )


class IdempotencyConfig(BaseModel):
    """Configuration for idempotency behavior."""

    enabled: bool = Field(
        default=True,
        description="Whether idempotency checking is enabled",
    )
    ttl_seconds: int = Field(
        default=86400,  # 24 hours
        description="Time-to-live for idempotency records",
    )
    storage_backend: str = Field(
        default="memory",
        description="Storage backend: 'memory', 'redis', 'database'",
    )
    require_for_posts: bool = Field(
        default=False,
        description="If true, POST requests require idempotency key",
    )


class IdempotencyCheck(BaseModel):
    """Result of idempotency check before processing request."""

    is_replay: bool = Field(
        ...,
        description="True if this is a replay of a previous request",
    )
    record: IdempotencyRecord | None = Field(
        None,
        description="Existing record if replay, None if new request",
    )
    conflict: IdempotencyConflict | None = Field(
        None,
        description="Conflict details if request hash mismatch",
    )
