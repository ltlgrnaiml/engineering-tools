"""Sanitization contracts for PII detection and redaction.

This module provides stub contracts for the PII sanitization pipeline.
Replace with full implementation when DISC-004 is implemented.
"""

__version__ = "2025.12.01"

from .pii import (
    PatternCategory,
    PatternConfig,
    RedactionEntry,
    RedactionLog,
    SanitizeConfig,
    SanitizeResult,
)

__all__ = [
    "PatternCategory",
    "PatternConfig",
    "RedactionEntry",
    "RedactionLog",
    "SanitizeConfig",
    "SanitizeResult",
]
