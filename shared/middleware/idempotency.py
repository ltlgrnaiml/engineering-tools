"""Idempotency middleware for FastAPI.

Per ADR-0033: HTTP Request Idempotency Semantics.
Per API-005: All mutating requests MUST be idempotent or retriable.

This middleware intercepts requests with X-Idempotency-Key header,
caches responses, and replays cached responses for duplicate requests.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.contracts.core.idempotency import (
    IdempotencyCheck,
    IdempotencyConfig,
    IdempotencyConflict,
    IdempotencyRecord,
    IdempotencyStatus,
)

# Header name for idempotency key
IDEMPOTENCY_HEADER = "X-Idempotency-Key"

# In-memory store for idempotency records (replace with Redis/DB in production)
_idempotency_store: dict[str, IdempotencyRecord] = {}


def compute_request_hash(body: bytes, endpoint: str, method: str) -> str:
    """Compute SHA-256 hash of request for conflict detection.

    Args:
        body: Request body bytes.
        endpoint: API endpoint path.
        method: HTTP method.

    Returns:
        SHA-256 hash string (first 16 chars).
    """
    content = f"{method}:{endpoint}:{body.decode('utf-8', errors='ignore')}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def check_idempotency(
    idempotency_key: str,
    request_hash: str,
    endpoint: str,
    method: str,
) -> IdempotencyCheck:
    """Check if request is a replay or new request.

    Args:
        idempotency_key: The idempotency key from header.
        request_hash: Hash of current request.
        endpoint: API endpoint path.
        method: HTTP method.

    Returns:
        IdempotencyCheck result.
    """
    if idempotency_key not in _idempotency_store:
        return IdempotencyCheck(is_replay=False, record=None, conflict=None)

    record = _idempotency_store[idempotency_key]

    # Check if expired
    if datetime.now(UTC) > record.expires_at:
        del _idempotency_store[idempotency_key]
        return IdempotencyCheck(is_replay=False, record=None, conflict=None)

    # Check for conflict (same key, different request)
    if record.request_hash != request_hash:
        conflict = IdempotencyConflict(
            idempotency_key=idempotency_key,
            original_request_hash=record.request_hash,
            new_request_hash=request_hash,
            message="Idempotency key already used with different request body",
        )
        return IdempotencyCheck(is_replay=False, record=record, conflict=conflict)

    # Valid replay
    return IdempotencyCheck(is_replay=True, record=record, conflict=None)


def store_idempotency_record(
    idempotency_key: str,
    request_hash: str,
    endpoint: str,
    method: str,
    response_status: int,
    response_body: dict[str, Any],
    ttl_seconds: int = 86400,
) -> IdempotencyRecord:
    """Store idempotency record after request completes.

    Args:
        idempotency_key: The idempotency key from header.
        request_hash: Hash of the request.
        endpoint: API endpoint path.
        method: HTTP method.
        response_status: HTTP response status code.
        response_body: Response body as dict.
        ttl_seconds: Time-to-live for record.

    Returns:
        Stored IdempotencyRecord.
    """
    now = datetime.now(UTC)
    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        status=IdempotencyStatus.COMPLETED,
        request_hash=request_hash,
        endpoint=endpoint,
        method=method,
        created_at=now,
        completed_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        response_status=response_status,
        response_body=response_body,
    )
    _idempotency_store[idempotency_key] = record
    return record


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for idempotency handling.

    Per ADR-0033: POST endpoints with side effects must support idempotency keys.

    Usage:
        app.add_middleware(IdempotencyMiddleware, config=IdempotencyConfig())

    Example:
        # Client sends:
        POST /api/dat/runs HTTP/1.1
        X-Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
        Content-Type: application/json

        {"profile_id": "default", "source_file": "data.csv"}
    """

    def __init__(self, app: Any, config: IdempotencyConfig | None = None) -> None:
        """Initialize middleware.

        Args:
            app: FastAPI application.
            config: Idempotency configuration.
        """
        super().__init__(app)
        self.config = config or IdempotencyConfig()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Process request with idempotency handling.

        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.

        Returns:
            Response (cached or fresh).
        """
        # Skip if disabled or not a mutating method
        if not self.config.enabled:
            return await call_next(request)

        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        # Check for idempotency header
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)

        if not idempotency_key:
            # If required, return error
            if self.config.require_for_posts and request.method == "POST":
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "missing_idempotency_key",
                        "message": f"POST requests require {IDEMPOTENCY_HEADER} header",
                    },
                )
            # Otherwise proceed without idempotency
            return await call_next(request)

        # Read request body for hashing
        body = await request.body()
        request_hash = compute_request_hash(body, str(request.url.path), request.method)

        # Check for existing record
        check = check_idempotency(
            idempotency_key, request_hash, str(request.url.path), request.method
        )

        # Handle conflict
        if check.conflict:
            return JSONResponse(
                status_code=409,
                content={
                    "error": "idempotency_conflict",
                    "message": check.conflict.message,
                    "original_request_hash": check.conflict.original_request_hash,
                    "new_request_hash": check.conflict.new_request_hash,
                },
                headers={IDEMPOTENCY_HEADER: idempotency_key},
            )

        # Handle replay
        if check.is_replay and check.record and check.record.response_body:
            return JSONResponse(
                status_code=check.record.response_status or 200,
                content=check.record.response_body,
                headers={
                    IDEMPOTENCY_HEADER: idempotency_key,
                    "X-Idempotency-Replayed": "true",
                },
            )

        # Process new request
        response = await call_next(request)

        # Store response for future replays (only for success responses)
        if 200 <= response.status_code < 300:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            try:
                response_dict = json.loads(response_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                response_dict = {"raw": response_body.decode("utf-8", errors="ignore")}

            store_idempotency_record(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                endpoint=str(request.url.path),
                method=request.method,
                response_status=response.status_code,
                response_body=response_dict,
                ttl_seconds=self.config.ttl_seconds,
            )

            # Return new response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response


def get_idempotency_record(idempotency_key: str) -> IdempotencyRecord | None:
    """Get idempotency record by key (for debugging/testing).

    Args:
        idempotency_key: The idempotency key.

    Returns:
        IdempotencyRecord if found and not expired, None otherwise.
    """
    if idempotency_key not in _idempotency_store:
        return None

    record = _idempotency_store[idempotency_key]
    if datetime.now(UTC) > record.expires_at:
        del _idempotency_store[idempotency_key]
        return None

    return record


def clear_idempotency_store() -> None:
    """Clear all idempotency records (for testing)."""
    _idempotency_store.clear()
