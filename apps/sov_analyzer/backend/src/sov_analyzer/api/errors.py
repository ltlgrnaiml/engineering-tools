"""Standardized error handling for SOV (Sources of Variance) Analyzer API.

Per ADR-0032: All HTTP errors MUST use ErrorResponse contract.
Per API-003: Error responses MUST use standard error schema.

This module provides a centralized error helper that all SOV API
endpoints should use instead of plain HTTPException.
"""

from fastapi import HTTPException

from shared.contracts.core.error_response import (
    ErrorCategory,
    ErrorDetail,
    create_error_response,
)

TOOL_NAME = "sov"


def raise_error(
    status_code: int,
    message: str,
    category: ErrorCategory | None = None,
    field: str | None = None,
    details: list[ErrorDetail] | None = None,
) -> None:
    """Raise HTTPException with standardized ErrorResponse.

    Per ADR-0032: All SOV errors use ErrorResponse contract.

    Args:
        status_code: HTTP status code (400, 404, 500, etc.).
        message: Human-readable error message.
        category: Error category (auto-detected from status_code if not provided).
        field: Optional field name for validation errors.
        details: Optional list of ErrorDetail objects.

    Raises:
        HTTPException: Always raises with ErrorResponse body.

    Example:
        >>> raise_error(404, "Analysis not found", ErrorCategory.NOT_FOUND)
        >>> raise_error(400, "Invalid factor column", field="factors")
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
        resource_type: Type of resource (e.g., "Analysis", "DataSet").
        resource_id: ID of the missing resource.

    Raises:
        HTTPException: 404 with ErrorResponse body.

    Example:
        >>> raise_not_found("Analysis", analysis_id)
        >>> raise_not_found("DataSet", dataset_id)
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
        >>> raise_validation_error("Invalid factor column", field="factors")
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
        >>> raise_internal_error("ANOVA computation failed", e)
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


def raise_analysis_error(analysis_id: str, message: str) -> None:
    """Raise error related to analysis operations.

    Args:
        analysis_id: ID of the analysis.
        message: Human-readable error message.

    Raises:
        HTTPException: 400 with ErrorResponse body.

    Example:
        >>> raise_analysis_error("analysis_123", "Insufficient data for ANOVA")
    """
    raise_error(
        status_code=400,
        message=f"Analysis {analysis_id}: {message}",
        category=ErrorCategory.BUSINESS_RULE,
        details=[
            ErrorDetail(
                field="analysis_id",
                message=message,
                context={"analysis_id": analysis_id},
            )
        ],
    )


def raise_dataset_error(dataset_id: str, message: str) -> None:
    """Raise error related to DataSet operations.

    Per ADR-0024: SOV DataSet Integration.

    Args:
        dataset_id: ID of the DataSet.
        message: Human-readable error message.

    Raises:
        HTTPException: 400 with ErrorResponse body.

    Example:
        >>> raise_dataset_error("ds_123", "Missing required columns for ANOVA")
    """
    raise_error(
        status_code=400,
        message=f"DataSet {dataset_id}: {message}",
        category=ErrorCategory.VALIDATION,
        details=[
            ErrorDetail(
                field="dataset_id",
                message=message,
                context={"dataset_id": dataset_id},
            )
        ],
    )


def raise_variance_validation_error(message: str, computed_sum: float) -> None:
    """Raise error when variance percentages don't sum to 100%.

    Per ADR-0023: SOV Analysis Pipeline (variance percentages MUST sum to 100%).

    Args:
        message: Human-readable error message.
        computed_sum: The actual sum that was computed.

    Raises:
        HTTPException: 500 with ErrorResponse body.

    Example:
        >>> raise_variance_validation_error("Variance sum validation failed", 99.5)
    """
    raise_error(
        status_code=500,
        message=message,
        category=ErrorCategory.INTERNAL,
        details=[
            ErrorDetail(
                message=f"Expected variance sum: 100%, got: {computed_sum:.2f}%",
                code="VARIANCE_SUM_MISMATCH",
                context={"computed_sum": computed_sum, "expected_sum": 100.0},
            )
        ],
    )
