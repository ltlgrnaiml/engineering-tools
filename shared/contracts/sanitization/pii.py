"""PII Sanitization Contracts.

Stub implementation for DISC-004 (PII Sanitization Pipeline).
Provides interfaces for regex-based PII detection and redaction.

Decision: Regex-based MVP with <5% false positive rate.
Reversibility: Dev mode only.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class PatternCategory(str, Enum):
    """Categories of PII patterns to detect."""

    API_KEYS = "api_keys"
    SECRETS = "secrets"
    EMAILS = "emails"
    IPS = "ips"
    URLS = "urls"
    CUSTOM = "custom"


class PatternConfig(BaseModel):
    """Configuration for a single PII pattern.

    Attributes:
        category: The category of PII this pattern detects.
        pattern: Regex pattern string.
        replacement: Replacement text for redacted content.
        enabled: Whether this pattern is active.
    """

    category: PatternCategory
    pattern: str
    replacement: str = "[REDACTED]"
    enabled: bool = True


class RedactionEntry(BaseModel):
    """Record of a single redaction operation.

    Attributes:
        original: Original text that was redacted.
        replacement: Replacement text used.
        category: Category of the detected PII.
        start: Start position in original content.
        end: End position in original content.
    """

    original: str
    replacement: str
    category: PatternCategory
    start: int
    end: int


class RedactionLog(BaseModel):
    """Log of all redactions performed on content.

    Only populated in dev mode for debugging.

    Attributes:
        entries: List of redaction entries.
        reversible: Whether redactions can be reversed.
    """

    entries: list[RedactionEntry] = Field(default_factory=list)
    reversible: bool = False


class SanitizeConfig(BaseModel):
    """Configuration for sanitization operation.

    Attributes:
        patterns: List of pattern configurations to apply.
        reversible: Whether to store redaction log (dev only).
        max_content_length: Maximum content length to process.
    """

    patterns: list[PatternConfig] = Field(default_factory=list)
    reversible: bool = False
    max_content_length: int = 1_000_000


class SanitizeResult(BaseModel):
    """Result of a sanitization operation.

    Attributes:
        content: Sanitized content with PII replaced.
        redaction_count: Number of redactions performed.
        redaction_log: Log of redactions (if reversible=True).
        error: Error message if sanitization failed.
    """

    content: str
    redaction_count: int = 0
    redaction_log: RedactionLog | None = None
    error: str | None = None


# === STUB IMPLEMENTATION ===
# Replace with full implementation when DISC-004 is executed


def sanitize(content: str, config: SanitizeConfig | None = None) -> SanitizeResult:
    """Sanitize content by removing PII.

    STUB: Returns content unchanged until DISC-004 is implemented.

    Args:
        content: Raw content to sanitize.
        config: Sanitization configuration.

    Returns:
        SanitizeResult with sanitized content.
    """
    # STUB: Pass through unchanged
    return SanitizeResult(content=content, redaction_count=0)


def restore_redactions(content: str, log: RedactionLog) -> str:
    """Restore original content from redaction log.

    STUB: Only available in dev mode.

    Args:
        content: Sanitized content.
        log: Redaction log from original sanitization.

    Returns:
        Original content with PII restored.

    Raises:
        ValueError: If log is not reversible.
    """
    if not log.reversible:
        raise ValueError("Redaction log is not reversible")
    # STUB: Return content unchanged
    return content
