"""Message catalog contracts - standardized user-facing messages.

Per ADR-0017#message-catalogs: Wire payloads use 'user_message' field
mapped from catalog 'message' field. All user-facing messages MUST be
defined in catalogs, never hardcoded in backend logic.

This module defines contracts for:
- Message definitions (templates with placeholders)
- Message catalogs (collections of messages by domain)
- Localized messages (i18n support)
- Specific message types (error, progress, notification, validation)

Messages support placeholder substitution using Python format strings:
  "Processing {file_count} files from {source_path}"
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


class MessageSeverity(str, Enum):
    """Severity level for messages."""

    DEBUG = "debug"  # Developer-only info
    INFO = "info"  # Informational
    SUCCESS = "success"  # Successful completion
    WARNING = "warning"  # Non-fatal issue
    ERROR = "error"  # Error requiring attention
    CRITICAL = "critical"  # Critical failure


class MessageCategory(str, Enum):
    """Category of message for routing and display."""

    SYSTEM = "system"  # System-level messages
    VALIDATION = "validation"  # Input validation
    PROGRESS = "progress"  # Progress updates
    RESULT = "result"  # Analysis/processing results
    NOTIFICATION = "notification"  # User notifications
    ERROR = "error"  # Error messages
    HELP = "help"  # Help/guidance text


class MessageDefinition(BaseModel):
    """A single message definition in a catalog.

    Messages are templates that can include placeholders for dynamic content.
    Placeholders use Python format string syntax: {placeholder_name}
    """

    # Identity
    message_id: str = Field(
        ...,
        description="Unique identifier within catalog (e.g., 'DAT_PARSE_START')",
        pattern=r"^[A-Z][A-Z0-9_]+$",
    )

    # Content
    message: str = Field(
        ...,
        description="Message template with {placeholder} support",
    )
    description: str | None = Field(
        None,
        description="Description for developers/translators",
    )

    # Classification
    severity: MessageSeverity = MessageSeverity.INFO
    category: MessageCategory = MessageCategory.SYSTEM

    # Placeholders
    placeholders: list[str] = Field(
        default_factory=list,
        description="Expected placeholder names in the message",
    )
    placeholder_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Descriptions for each placeholder",
    )

    # Actions
    action_required: bool = Field(
        False,
        description="True if user action is required",
    )
    suggested_action: str | None = Field(
        None,
        description="Suggested action for user to take",
    )

    # Help
    help_url: str | None = Field(
        None,
        description="URL to help documentation",
    )
    error_code: str | None = Field(
        None,
        description="Machine-readable error code for ERROR/CRITICAL",
    )

    @field_validator("placeholders", mode="before")
    @classmethod
    def extract_placeholders(cls, v: list[str], info) -> list[str]:
        """Auto-extract placeholders from message if not provided."""
        if v:
            return v
        # Extract from message template
        message = info.data.get("message", "")
        import re
        placeholders = re.findall(r"\{(\w+)\}", message)
        return list(dict.fromkeys(placeholders))  # Deduplicate preserving order

    def format(self, **kwargs: Any) -> str:
        """Format the message with provided values.

        Missing placeholders are left as-is for partial formatting.
        """
        try:
            return self.message.format(**kwargs)
        except KeyError:
            # Partial format - leave missing placeholders
            result = self.message
            for key, value in kwargs.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result


class MessageCatalog(BaseModel):
    """A collection of message definitions.

    Catalogs are organized by domain/tool for maintainability.
    Per ADR-0017: CI validates catalogs match wire contract expectations.
    """

    # Identity
    catalog_id: str = Field(
        ...,
        description="Unique catalog identifier (e.g., 'dat', 'sov', 'core')",
    )
    name: str = Field(..., description="Human-readable catalog name")
    description: str | None = None
    version: str = Field("1.0.0", description="Catalog version")

    # Messages
    messages: dict[str, MessageDefinition] = Field(
        default_factory=dict,
        description="message_id -> MessageDefinition",
    )

    # Metadata
    domain: str | None = Field(
        None,
        description="Domain this catalog belongs to",
    )
    locale: str = Field("en", description="Default locale")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_message(self, message_id: str) -> MessageDefinition | None:
        """Get a message definition by ID."""
        return self.messages.get(message_id)

    def format_message(self, message_id: str, **kwargs: Any) -> str | None:
        """Format a message with provided values."""
        msg = self.get_message(message_id)
        if msg is None:
            return None
        return msg.format(**kwargs)

    def add_message(self, message: MessageDefinition) -> None:
        """Add a message to the catalog."""
        self.messages[message.message_id] = message


class MessageRef(BaseModel):
    """Reference to a message in a catalog.

    Used in API responses to reference catalog messages.
    """

    catalog_id: str
    message_id: str
    placeholders: dict[str, Any] = Field(
        default_factory=dict,
        description="Values for message placeholders",
    )


class LocalizedMessage(BaseModel):
    """A message with localization support.

    Contains the formatted message in the user's locale.
    """

    message_id: str
    locale: str = "en"
    formatted_message: str = Field(
        ...,
        description="The final formatted message text",
    )
    severity: MessageSeverity = MessageSeverity.INFO
    category: MessageCategory = MessageCategory.SYSTEM

    # Original reference
    catalog_id: str | None = None
    placeholders_used: dict[str, Any] = Field(default_factory=dict)


class ErrorMessage(BaseModel):
    """Standardized error message for API responses.

    Per ADR-0017: All error messages follow this structure for consistency.
    """

    # Error identification
    error_code: str = Field(
        ...,
        description="Machine-readable error code (e.g., 'DAT_PARSE_FAILED')",
    )
    message: str = Field(
        ...,
        description="User-friendly error message",
    )
    severity: MessageSeverity = MessageSeverity.ERROR

    # Context
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context",
    )
    field: str | None = Field(
        None,
        description="Field that caused the error (for validation errors)",
    )
    path: str | None = Field(
        None,
        description="Path/location of error (e.g., file path, JSON path)",
    )

    # Recovery
    recoverable: bool = Field(
        False,
        description="True if error can be recovered from",
    )
    suggested_action: str | None = None
    help_url: str | None = None

    # Debugging
    request_id: str | None = Field(
        None,
        description="Request ID for support reference",
    )
    timestamp: datetime | None = None


class ProgressMessage(BaseModel):
    """Progress update message for long-running operations.

    Used to communicate progress to the frontend.
    """

    # Operation tracking
    operation_id: str = Field(..., description="ID of the operation")
    operation_type: str = Field(
        ...,
        description="Type of operation (e.g., 'parse', 'export', 'render')",
    )

    # Progress
    progress_pct: float = Field(..., ge=0.0, le=100.0)
    message: str = Field(..., description="Current status message")

    # Counts
    completed_items: int = Field(0, ge=0)
    total_items: int = Field(0, ge=0)
    failed_items: int = Field(0, ge=0)

    # Current item
    current_item: str | None = Field(
        None,
        description="Currently processing item name/path",
    )

    # Timing
    started_at: datetime
    estimated_completion: datetime | None = None
    elapsed_seconds: float = Field(0.0, ge=0.0)

    # State
    is_complete: bool = False
    is_cancelled: bool = False
    has_errors: bool = False


class NotificationMessage(BaseModel):
    """User notification message.

    For toast notifications, alerts, and other UI notifications.
    """

    # Content
    title: str = Field(..., max_length=100)
    message: str = Field(..., max_length=500)
    severity: MessageSeverity = MessageSeverity.INFO

    # Display
    auto_dismiss: bool = Field(
        True,
        description="Auto-dismiss after timeout",
    )
    dismiss_timeout_ms: int = Field(
        5000,
        ge=1000,
        le=30000,
        description="Auto-dismiss timeout in milliseconds",
    )
    show_icon: bool = True

    # Actions
    action_label: str | None = Field(
        None,
        description="Label for action button",
    )
    action_url: str | None = Field(
        None,
        description="URL to navigate to on action",
    )
    action_callback: str | None = Field(
        None,
        description="Frontend callback function name",
    )

    # Metadata
    notification_id: str | None = None
    timestamp: datetime | None = None
    read: bool = False


class ValidationMessage(BaseModel):
    """Validation error/warning message.

    Used to communicate validation issues for user input.
    """

    # Location
    field: str = Field(..., description="Field that failed validation")
    path: str | None = Field(
        None,
        description="JSON path for nested fields",
    )

    # Message
    message: str
    severity: MessageSeverity = MessageSeverity.ERROR

    # Validation details
    constraint: str | None = Field(
        None,
        description="Constraint that was violated (e.g., 'min_length', 'pattern')",
    )
    expected: Any = Field(None, description="Expected value/format")
    received: Any = Field(None, description="Actual received value")

    # Help
    suggested_fix: str | None = None


class ValidationResult(BaseModel):
    """Complete validation result with all messages."""

    valid: bool
    messages: list[ValidationMessage] = Field(default_factory=list)
    error_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)

    @property
    def errors(self) -> list[ValidationMessage]:
        """Get only error messages."""
        return [m for m in self.messages if m.severity == MessageSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationMessage]:
        """Get only warning messages."""
        return [m for m in self.messages if m.severity == MessageSeverity.WARNING]


def format_message(
    catalog: MessageCatalog,
    message_id: str,
    locale: str = "en",
    **kwargs: Any,
) -> LocalizedMessage | None:
    """Format a message from a catalog into a LocalizedMessage.

    Args:
        catalog: The message catalog
        message_id: ID of the message to format
        locale: Target locale (for future i18n support)
        **kwargs: Placeholder values

    Returns:
        LocalizedMessage if message found, None otherwise
    """
    msg_def = catalog.get_message(message_id)
    if msg_def is None:
        return None

    formatted = msg_def.format(**kwargs)

    return LocalizedMessage(
        message_id=message_id,
        locale=locale,
        formatted_message=formatted,
        severity=msg_def.severity,
        category=msg_def.category,
        catalog_id=catalog.catalog_id,
        placeholders_used=kwargs,
    )
