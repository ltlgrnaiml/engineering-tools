"""PII Sanitizer - SPEC-0043-SA01, SA02, SA03.

Sanitize sensitive content before LLM exposure.
GUARDRAIL: ALL content must pass through sanitizer before LLM.
"""

import re
from dataclasses import dataclass, field


@dataclass
class SanitizationResult:
    """Result of sanitization with redaction tracking."""
    content: str
    redactions: list[dict] = field(default_factory=list)
    redaction_count: int = 0


class Sanitizer:
    """PII and sensitive content sanitizer."""

    # Patterns for sensitive content (SPEC-0043-SA01)
    PATTERNS = {
        'email': (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
        'api_key': (r'sk-[a-zA-Z0-9]{20,}', '[API_KEY]'),
        'aws_key': (r'AKIA[0-9A-Z]{16}', '[AWS_KEY]'),
        'phone': (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        'credit_card': (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
        'ip_address': (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
        'bearer_token': (r'Bearer\s+[a-zA-Z0-9._-]+', '[BEARER_TOKEN]'),
    }

    # Allowlist patterns that should NOT be redacted
    ALLOWLIST = [
        r'example\.com',
        r'localhost',
        r'127\.0\.0\.1',
        r'test@test\.com',
    ]

    def __init__(self, extra_patterns: dict[str, tuple[str, str]] | None = None):
        """Initialize with optional custom patterns."""
        self.patterns = {**self.PATTERNS}
        if extra_patterns:
            self.patterns.update(extra_patterns)

    def _is_allowlisted(self, match: str) -> bool:
        """Check if match is in allowlist."""
        for pattern in self.ALLOWLIST:
            if re.search(pattern, match, re.IGNORECASE):
                return True
        return False

    def sanitize(self, content: str) -> SanitizationResult:
        """Sanitize content by redacting sensitive patterns."""
        redactions = []
        result = content

        for name, (pattern, replacement) in self.patterns.items():
            matches = list(re.finditer(pattern, result))
            for match in reversed(matches):  # Reverse to preserve positions
                original = match.group()
                if self._is_allowlisted(original):
                    continue
                redactions.append({
                    'type': name,
                    'start': match.start(),
                    'end': match.end(),
                    'original_length': len(original)
                })
                result = result[:match.start()] + replacement + result[match.end():]

        return SanitizationResult(
            content=result,
            redactions=redactions,
            redaction_count=len(redactions)
        )

    def sanitize_for_llm(self, content: str) -> str:
        """Convenience method: sanitize and return content only."""
        return self.sanitize(content).content
