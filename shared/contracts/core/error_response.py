"""Unified Error Response contracts for all tools.

Per API-003: Error responses MUST use standard error schema.

All tools should use these contracts for consistent error handling
across the platform.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__version__ = "0.1.0"


class ErrorSeverity(str, Enum):
    """Severity level of an error."""

    ERROR = "error"  # Request failed, action required
    WARNING = "warning"  # Request succeeded with issues
    INFO = "info"  # Informational message


class ErrorCategory(str, Enum):
    """Category of error for routing/handling."""

    VALIDATION = "validation"  # Input validation failed
    NOT_FOUND = "not_found"  # Resource not found
    CONFLICT = "conflict"  # Resource state conflict
    PERMISSION = "permission"  # Permission denied
    RATE_LIMIT = "rate_limit"  # Rate limit exceeded
    INTERNAL = "internal"  # Internal server error
    DEPENDENCY = "dependency"  # External dependency failed
    TIMEOUT = "timeout"  # Operation timed out
    CANCELLED = "cancelled"  # Operation was cancelled


class ErrorDetail(BaseModel):
    """Detailed error information for a specific field or component."""

    field: str | None = Field(None, description="Field name if validation error")
    message: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Machine-readable error code")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for debugging",
    )


class ErrorResponse(BaseModel):
    """Standard error response for all API endpoints.

    Per API-003: All error responses across tools MUST use this schema.

    Example:
        {
            "error": true,
            "status_code": 400,
            "category": "validation",
            "message": "Invalid request parameters",
            "details": [
                {"field": "factors", "message": "At least one factor required"}
            ],
            "request_id": "abc123",
            "timestamp": "2024-12-27T10:30:00Z"
        }
    """

    error: bool = Field(True, description="Always true for error responses")
    status_code: int = Field(..., ge=400, le=599, description="HTTP status code")
    category: ErrorCategory = Field(..., description="Error category for routing")
    severity: ErrorSeverity = Field(
        ErrorSeverity.ERROR,
        description="Severity level",
    )
    message: str = Field(..., description="Human-readable summary message")
    details: list[ErrorDetail] = Field(
        default_factory=list,
        description="Detailed error information",
    )
    request_id: str | None = Field(
        None,
        description="Request ID for tracing",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the error occurred (ISO-8601 UTC)",
    )
    tool: str | None = Field(
        None,
        description="Tool that generated the error (dat, sov, pptx, gateway)",
    )
    documentation_url: str | None = Field(
        None,
        description="Link to relevant documentation",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": True,
            "status_code": 400,
            "category": "validation",
            "severity": "error",
            "message": "Invalid request parameters",
            "details": [
                {
                    "field": "factors",
                    "message": "At least one factor is required",
                    "code": "REQUIRED_FIELD",
                }
            ],
            "request_id": "req_abc123xyz",
            "timestamp": "2024-12-27T10:30:00Z",
            "tool": "sov",
        }
    })


class ValidationErrorResponse(ErrorResponse):
    """Specialized error response for validation failures."""

    status_code: int = Field(400, ge=400, le=499)
    category: ErrorCategory = Field(ErrorCategory.VALIDATION)

    @classmethod
    def from_field_errors(
        cls,
        field_errors: dict[str, str],
        message: str = "Validation failed",
        tool: str | None = None,
    ) -> "ValidationErrorResponse":
        """Create from a dictionary of field errors.

        Args:
            field_errors: Dict mapping field names to error messages.
            message: Overall error message.
            tool: Tool name.

        Returns:
            ValidationErrorResponse instance.
        """
        details = [
            ErrorDetail(field=field, message=msg)
            for field, msg in field_errors.items()
        ]
        return cls(
            status_code=400,
            message=message,
            details=details,
            tool=tool,
        )


class NotFoundErrorResponse(ErrorResponse):
    """Specialized error response for not found errors."""

    status_code: int = Field(404)
    category: ErrorCategory = Field(ErrorCategory.NOT_FOUND)

    @classmethod
    def for_resource(
        cls,
        resource_type: str,
        resource_id: str,
        tool: str | None = None,
    ) -> "NotFoundErrorResponse":
        """Create for a missing resource.

        Args:
            resource_type: Type of resource (e.g., "project", "dataset").
            resource_id: ID of the missing resource.
            tool: Tool name.

        Returns:
            NotFoundErrorResponse instance.
        """
        return cls(
            status_code=404,
            message=f"{resource_type} not found: {resource_id}",
            details=[
                ErrorDetail(
                    message=f"No {resource_type} exists with ID '{resource_id}'",
                    code="RESOURCE_NOT_FOUND",
                    context={"resource_type": resource_type, "resource_id": resource_id},
                )
            ],
            tool=tool,
        )


class InternalErrorResponse(ErrorResponse):
    """Specialized error response for internal server errors."""

    status_code: int = Field(500)
    category: ErrorCategory = Field(ErrorCategory.INTERNAL)

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        include_traceback: bool = False,
        tool: str | None = None,
    ) -> "InternalErrorResponse":
        """Create from an exception.

        Args:
            exception: The exception that occurred.
            include_traceback: Whether to include traceback (dev only).
            tool: Tool name.

        Returns:
            InternalErrorResponse instance.
        """
        context = {"exception_type": type(exception).__name__}
        if include_traceback:
            import traceback

            context["traceback"] = traceback.format_exc()

        return cls(
            status_code=500,
            message="An internal error occurred",
            details=[
                ErrorDetail(
                    message=str(exception),
                    code="INTERNAL_ERROR",
                    context=context,
                )
            ],
            tool=tool,
        )


def create_error_response(
    status_code: int,
    message: str,
    category: ErrorCategory | None = None,
    details: list[ErrorDetail] | None = None,
    tool: str | None = None,
    request_id: str | None = None,
) -> ErrorResponse:
    """Factory function to create standard error responses.

    Args:
        status_code: HTTP status code.
        message: Human-readable error message.
        category: Error category (auto-detected from status_code if not provided).
        details: List of error details.
        tool: Tool name.
        request_id: Request ID for tracing.

    Returns:
        ErrorResponse instance.
    """
    if category is None:
        if status_code == 404:
            category = ErrorCategory.NOT_FOUND
        elif status_code == 409:
            category = ErrorCategory.CONFLICT
        elif status_code == 403:
            category = ErrorCategory.PERMISSION
        elif status_code == 429:
            category = ErrorCategory.RATE_LIMIT
        elif 400 <= status_code < 500:
            category = ErrorCategory.VALIDATION
        else:
            category = ErrorCategory.INTERNAL

    return ErrorResponse(
        status_code=status_code,
        category=category,
        message=message,
        details=details or [],
        tool=tool,
        request_id=request_id,
    )
