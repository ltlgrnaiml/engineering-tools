"""Standardized error handling for PPTX API.

Per ADR-0032: All HTTP errors MUST use ErrorResponse contract.
Per API-003: Error responses MUST use standard error schema.

This module provides a centralized error helper that all PPTX API
endpoints should use instead of plain HTTPException.
"""

from fastapi import HTTPException

from shared.contracts.core.error_response import (
    ErrorCategory,
    ErrorDetail,
    ErrorResponse,
    create_error_response,
)

TOOL_NAME = "pptx"


def raise_error(
    status_code: int,
    message: str,
    category: ErrorCategory | None = None,
    field: str | None = None,
    details: list[ErrorDetail] | None = None,
) -> None:
    """Raise HTTPException with standardized ErrorResponse.

    Per ADR-0032: All PPTX errors use ErrorResponse contract.

    Args:
        status_code: HTTP status code (400, 404, 500, etc.).
        message: Human-readable error message.
        category: Error category (auto-detected from status_code if not provided).
        field: Optional field name for validation errors.
        details: Optional list of ErrorDetail objects.

    Raises:
        HTTPException: Always raises with ErrorResponse body.

    Example:
        >>> raise_error(404, "Project not found", ErrorCategory.NOT_FOUND)
        >>> raise_error(400, "Invalid file type", field="file")
    """
    error_details = details or []
    if field and not details:
        error_details = [ErrorDetail(field=field, message=message)]

    error = create_error_response(
        status_code=status_code,
        message=message,
        category=category,
        details=error_details,
        tool=TOOL_NAME,
    )

    raise HTTPException(
        status_code=status_code,
        detail=error.model_dump(mode="json"),
    )


def raise_not_found(resource_type: str, resource_id: str) -> None:
    """Raise 404 Not Found error for a missing resource.

    Args:
        resource_type: Type of resource (e.g., "Project", "Template").
        resource_id: ID of the missing resource.

    Raises:
        HTTPException: 404 with ErrorResponse body.

    Example:
        >>> raise_not_found("Project", str(project_id))
    """
    raise_error(
        status_code=404,
        message=f"{resource_type} not found: {resource_id}",
        category=ErrorCategory.NOT_FOUND,
    )


def raise_validation_error(message: str, field: str | None = None) -> None:
    """Raise 400 Validation Error.

    Args:
        message: Human-readable validation error message.
        field: Optional field name that failed validation.

    Raises:
        HTTPException: 400 with ErrorResponse body.

    Example:
        >>> raise_validation_error("Invalid file type", field="file")
    """
    raise_error(
        status_code=400,
        message=message,
        category=ErrorCategory.VALIDATION,
        field=field,
    )


def raise_internal_error(message: str, exception: Exception | None = None) -> None:
    """Raise 500 Internal Server Error.

    Args:
        message: Human-readable error message.
        exception: Optional original exception for context.

    Raises:
        HTTPException: 500 with ErrorResponse body.

    Example:
        >>> raise_internal_error("Failed to save template", e)
    """
    details = []
    if exception:
        details = [
            ErrorDetail(
                message=str(exception),
                code="INTERNAL_ERROR",
                context={"exception_type": type(exception).__name__},
            )
        ]

    raise_error(
        status_code=500,
        message=message,
        category=ErrorCategory.INTERNAL,
        details=details,
    )


def raise_conflict_error(message: str) -> None:
    """Raise 409 Conflict Error.

    Args:
        message: Human-readable conflict message.

    Raises:
        HTTPException: 409 with ErrorResponse body.

    Example:
        >>> raise_conflict_error("Project already has a template")
    """
    raise_error(
        status_code=409,
        message=message,
        category=ErrorCategory.CONFLICT,
    )
