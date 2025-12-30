"""Message catalog contracts - user-facing messages and errors.

Per ADR-0018#message-catalogs: All user-facing messages must be defined
in catalogs, never hardcoded in backend logic.

This package contains Pydantic models for:
- User message definitions and catalogs
- Error message standardization
- Notification contracts
- Progress message templates

All messages are domain-agnostic with placeholder support for
dynamic content injection at runtime.
"""

from shared.contracts.messages.catalog import (
    MessageSeverity,
    MessageCategory,
    MessageDefinition,
    MessageCatalog,
    MessageRef,
    LocalizedMessage,
    ErrorMessage,
    ProgressMessage,
    NotificationMessage,
    ValidationMessage,
    format_message,
)

__all__ = [
    "MessageSeverity",
    "MessageCategory",
    "MessageDefinition",
    "MessageCatalog",
    "MessageRef",
    "LocalizedMessage",
    "ErrorMessage",
    "ProgressMessage",
    "NotificationMessage",
    "ValidationMessage",
    "format_message",
]
