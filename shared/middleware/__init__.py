"""Shared middleware for FastAPI applications.

Per ADR-0033: HTTP Request Idempotency Semantics.
Per ADR-0037: Observability & Debugging First.

This package provides middleware components used across all tools.
"""

from shared.middleware.idempotency import (
    IDEMPOTENCY_HEADER,
    IdempotencyMiddleware,
    check_idempotency,
    clear_idempotency_store,
    compute_request_hash,
    get_idempotency_record,
    store_idempotency_record,
)

__version__ = "2025.12.001"

__all__ = [
    "IDEMPOTENCY_HEADER",
    "IdempotencyMiddleware",
    "check_idempotency",
    "clear_idempotency_store",
    "compute_request_hash",
    "get_idempotency_record",
    "store_idempotency_record",
]
