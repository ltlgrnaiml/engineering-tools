"""Shared utilities implementing cross-cutting guardrails.

Per ADR-0018, these utilities enforce:
- path_safety: All public paths must be relative
- stage_id: Deterministic SHA-256 stage IDs (ADR-0005)
- timestamps: ISO-8601 UTC formatting (ADR-0009)
"""

__version__ = "0.1.0"
